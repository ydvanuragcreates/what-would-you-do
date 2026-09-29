import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import RoundNotCompletedError
from app.db.models import Category, Round, RoundQuestion, RoundResult, Scenario, UserAnswer
from app.db.models.enums import RoundStatus
from app.domain.dimensions import Dimension
from app.domain.profiles import DISCLAIMER, Profile, profile_for
from app.schemas.result import (
    DimensionScore,
    ProfilePublic,
    QuestionReview,
    ResultHistoryResponse,
    ResultSummary,
    RoundResultResponse,
)
from app.services import analytics
from app.services import scenarios as scenario_service
from app.services.rounds import get_owned_round

RANDOM_CATEGORY_NAME = "Random"


def get_result(db: Session, *, round_id: uuid.UUID, user_id: uuid.UUID) -> RoundResultResponse:
    """The finished result of one of the caller's own rounds."""
    round_ = get_owned_round(db, round_id, user_id)  # 404 if missing OR someone else's
    result = round_.result
    if round_.status != RoundStatus.COMPLETED or result is None:
        raise RoundNotCompletedError

    return RoundResultResponse(
        round_id=round_.id,
        category_id=round_.category_id,
        category_name=_category_name(db, round_.category_id),
        completed_at=round_.completed_at or result.created_at,
        profile=_public_profile(profile_for(result.profile_key, result.scores)),
        scores=_score_rows(result.scores),
        questions=_question_reviews(db, round_),
        disclaimer=DISCLAIMER,
    )


def list_results(
    db: Session, *, user_id: uuid.UUID, limit: int, offset: int
) -> ResultHistoryResponse:
    """The caller's finished rounds, newest first."""
    finished = (Round.user_id == user_id) & (Round.status == RoundStatus.COMPLETED)
    total = db.scalar(select(func.count(Round.id)).where(finished)) or 0

    rows = db.execute(
        select(Round, RoundResult, Category.name)
        .join(RoundResult, RoundResult.round_id == Round.id)
        .outerjoin(Category, Category.id == Round.category_id)
        .where(finished)
        .order_by(Round.completed_at.desc(), Round.id)
        .limit(limit)
        .offset(offset)
    ).all()

    return ResultHistoryResponse(
        total=total,
        results=[
            ResultSummary(
                round_id=round_.id,
                category_name=category_name or RANDOM_CATEGORY_NAME,
                completed_at=round_.completed_at or result.created_at,
                profile=_public_profile(profile_for(result.profile_key, result.scores)),
            )
            for round_, result, category_name in rows
        ],
    )


def _question_reviews(db: Session, round_: Round) -> list[QuestionReview]:
    ordered = db.scalars(
        select(RoundQuestion)
        .where(RoundQuestion.round_id == round_.id)
        .order_by(RoundQuestion.question_order)
    ).all()
    scenarios = {
        scenario.id: scenario
        for scenario in db.scalars(
            select(Scenario)
            .where(Scenario.id.in_([q.scenario_id for q in ordered]))
            .options(selectinload(Scenario.choices), selectinload(Scenario.category))
        )
    }
    chosen = dict(
        db.execute(
            select(UserAnswer.scenario_id, UserAnswer.choice_id).where(
                UserAnswer.round_id == round_.id
            )
        )
        .tuples()
        .all()
    )
    crowd = analytics.crowd_stats_for(db, list(scenarios.values()), exclude_user_id=round_.user_id)

    return [
        QuestionReview(
            question_number=question.question_order,
            scenario=scenario_service.to_public(scenarios[question.scenario_id]),
            your_choice_id=chosen[question.scenario_id],
            crowd=crowd[question.scenario_id],
        )
        for question in ordered
    ]


def _category_name(db: Session, category_id: int | None) -> str:
    if category_id is None:
        return RANDOM_CATEGORY_NAME
    category = db.get(Category, category_id)
    return category.name if category else RANDOM_CATEGORY_NAME


def _public_profile(profile: Profile) -> ProfilePublic:
    return ProfilePublic(key=profile.key, title=profile.title, summary=profile.summary)


def _score_rows(scores: dict[str, float]) -> list[DimensionScore]:
    return [
        DimensionScore(dimension=dim.value, label=dim.label, score=scores.get(dim.value))
        for dim in Dimension
    ]
