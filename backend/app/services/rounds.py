import random
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import (
    InvalidChoiceError,
    NotCurrentQuestionError,
    NotEnoughScenariosError,
    RoundNotFoundError,
    RoundNotInProgressError,
)
from app.db.models import Choice, Round, RoundQuestion, RoundResult, Scenario, UserAnswer
from app.db.models.enums import RoundStatus
from app.domain.profiles import pick_profile
from app.domain.scoring import SCORING_VERSION, compute_scores
from app.domain.selection import Candidate, select_scenarios
from app.schemas.round import LastAnswer, RoundResultPublic, RoundStateResponse
from app.services import analytics
from app.services import scenarios as scenario_service


def get_owned_round(db: Session, round_id: uuid.UUID, user_id: uuid.UUID) -> Round:
    """A round ID never reveals whether it belongs to someone else: both "no such
    round" and "not yours" are the same 404, mirroring InvalidCredentialsError."""
    round_ = db.get(Round, round_id)
    if round_ is None or round_.user_id != user_id:
        raise RoundNotFoundError
    return round_


def _current_question_scenario(db: Session, round_id: uuid.UUID) -> Scenario | None:
    answered = select(UserAnswer.scenario_id).where(UserAnswer.round_id == round_id)
    query = (
        select(Scenario)
        .join(RoundQuestion, RoundQuestion.scenario_id == Scenario.id)
        .where(RoundQuestion.round_id == round_id, Scenario.id.not_in(answered))
        .options(selectinload(Scenario.choices), selectinload(Scenario.category))
        .order_by(RoundQuestion.question_order)
        .limit(1)
    )
    return db.scalars(query).first()


def _answered_count(db: Session, round_id: uuid.UUID) -> int:
    return db.scalar(select(func.count(UserAnswer.id)).where(UserAnswer.round_id == round_id)) or 0


def _chosen_weights(db: Session, round_id: uuid.UUID) -> list[dict[str, int]]:
    query = (
        select(Choice.weights)
        .join(UserAnswer, UserAnswer.choice_id == Choice.id)
        .where(UserAnswer.round_id == round_id)
    )
    return list(db.scalars(query))


def _to_state_response(
    round_: Round,
    current_scenario: Scenario | None,
    answered_count: int,
    last_answer: LastAnswer | None = None,
) -> RoundStateResponse:
    result = None
    if round_.result is not None:
        result = RoundResultPublic(
            scores=round_.result.scores, profile_key=round_.result.profile_key
        )
    return RoundStateResponse(
        id=round_.id,
        status=round_.status,
        category_id=round_.category_id,
        question_count=round_.question_count,
        current_question_number=(answered_count + 1) if current_scenario is not None else None,
        question=scenario_service.to_public(current_scenario) if current_scenario else None,
        result=result,
        last_answer=last_answer,
    )


def _last_seen(db: Session, user_id: uuid.UUID) -> dict[int, datetime]:
    """When this player last answered each scenario (only their own history)."""
    query = (
        select(UserAnswer.scenario_id, func.max(UserAnswer.answered_at))
        .join(Round, Round.id == UserAnswer.round_id)
        .where(Round.user_id == user_id)
        .group_by(UserAnswer.scenario_id)
    )
    return dict(db.execute(query).tuples().all())


def start_round(
    db: Session,
    *,
    user_id: uuid.UUID,
    category_id: int | None,
    round_length: int,
    rng: random.Random | None = None,
) -> RoundStateResponse:
    scenarios = scenario_service.get_active_scenarios(db, category_id=category_id)
    if len(scenarios) < round_length:
        raise NotEnoughScenariosError

    by_id = {scenario.id: scenario for scenario in scenarios}
    chosen_ids = select_scenarios(
        [Candidate(s.id, s.category_id) for s in scenarios],
        _last_seen(db, user_id),
        round_length,
        rng or random.Random(),
        spread_categories=category_id is None,  # a single-category round has nothing to spread
    )
    chosen = [by_id[scenario_id] for scenario_id in chosen_ids]
    round_ = Round(
        user_id=user_id,
        category_id=category_id,
        question_count=round_length,
        questions=[
            RoundQuestion(scenario_id=scenario.id, question_order=order)
            for order, scenario in enumerate(chosen, start=1)
        ],
    )
    db.add(round_)
    db.commit()
    return _to_state_response(round_, chosen[0], answered_count=0)


def get_round_state(db: Session, *, round_id: uuid.UUID, user_id: uuid.UUID) -> RoundStateResponse:
    round_ = get_owned_round(db, round_id, user_id)
    if round_.status != RoundStatus.IN_PROGRESS:
        return _to_state_response(round_, None, _answered_count(db, round_id))
    current = _current_question_scenario(db, round_id)
    return _to_state_response(round_, current, _answered_count(db, round_id))


def submit_answer(
    db: Session, *, round_id: uuid.UUID, user_id: uuid.UUID, scenario_id: int, choice_id: int
) -> RoundStateResponse:
    round_ = get_owned_round(db, round_id, user_id)
    if round_.status != RoundStatus.IN_PROGRESS:
        raise RoundNotInProgressError

    current = _current_question_scenario(db, round_id)
    if current is None or current.id != scenario_id:
        raise NotCurrentQuestionError

    choice = db.get(Choice, choice_id)
    if choice is None or choice.scenario_id != scenario_id:
        raise InvalidChoiceError

    db.add(UserAnswer(round_id=round_id, scenario_id=scenario_id, choice_id=choice_id))
    try:
        db.flush()
    except IntegrityError:
        # Someone else's request answered this exact question first.
        db.rollback()
        raise NotCurrentQuestionError from None

    # Crowd split for the question just answered: shown to the player as the reveal.
    # Computed for other players only, so it reads the same on the final results page.
    crowd = analytics.crowd_stats_for(db, [current], exclude_user_id=user_id)[current.id]
    last_answer = LastAnswer(scenario_id=scenario_id, your_choice_id=choice_id, crowd=crowd)

    answered = _answered_count(db, round_id)
    if answered >= round_.question_count:
        round_.status = RoundStatus.COMPLETED
        round_.completed_at = datetime.now(UTC)
        scores = compute_scores(_chosen_weights(db, round_id))
        db.add(
            RoundResult(
                round_id=round_id,
                scores=scores,
                profile_key=pick_profile(scores).key,
                scoring_version=SCORING_VERSION,
            )
        )
        db.commit()
        return _to_state_response(round_, None, answered, last_answer)

    db.commit()
    return _to_state_response(
        round_, _current_question_scenario(db, round_id), answered, last_answer
    )
