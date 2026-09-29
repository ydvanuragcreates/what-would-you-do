"""Insert other players' finished rounds directly, to build up a crowd for the stats tests."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Choice, Round, RoundQuestion, Scenario, User, UserAnswer
from app.db.models.enums import RoundStatus


def make_player(db: Session, name: str) -> User:
    user = User(username=name, email=f"{name}@example.com", password_hash="x")
    db.add(user)
    db.flush()
    return user


def record_round(
    db: Session,
    user: User,
    answers: Sequence[tuple[Scenario, Choice]],
    *,
    status: RoundStatus = RoundStatus.COMPLETED,
    answered_at: datetime | None = None,
) -> Round:
    """A round in which `user` answered each (scenario, choice) pair, in that order."""
    round_ = Round(user_id=user.id, question_count=len(answers), status=status)
    round_.questions = [
        RoundQuestion(scenario_id=scenario.id, question_order=order)
        for order, (scenario, _) in enumerate(answers, start=1)
    ]
    db.add(round_)
    db.flush()
    for scenario, choice in answers:
        answer = UserAnswer(round_id=round_.id, scenario_id=scenario.id, choice_id=choice.id)
        if answered_at is not None:
            answer.answered_at = answered_at
        db.add(answer)
    db.flush()
    return round_
