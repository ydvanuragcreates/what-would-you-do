from enum import StrEnum


class Dimension(StrEnum):
    """The 8 things a round's choices are scored on.

    Each choice carries a 0-10 weight per dimension its scenario measures, where
    10 means "this choice strongly expresses this trait" and 0 means "strongly
    opposes it". A choice is never "good" or "bad" overall, only more or less of
    each trait. Adding a dimension later is a one-line change here (no migration,
    because weights are stored as JSON).
    """

    HONESTY = "honesty"
    LOYALTY = "loyalty"
    EMPATHY = "empathy"
    SELF_INTEREST = "self_interest"
    RISK = "risk"
    RESPONSIBILITY = "responsibility"
    FAIRNESS = "fairness"
    SOCIAL_PRESSURE = "social_pressure"  # 10 = strongly swayed by what the group does or thinks

    @property
    def label(self) -> str:
        """Display name for the result screen."""
        return _LABELS[self]


_LABELS = {
    Dimension.HONESTY: "Honesty",
    Dimension.LOYALTY: "Loyalty",
    Dimension.EMPATHY: "Empathy",
    Dimension.SELF_INTEREST: "Self-interest",
    Dimension.RISK: "Risk",
    Dimension.RESPONSIBILITY: "Responsibility",
    Dimension.FAIRNESS: "Fairness",
    Dimension.SOCIAL_PRESSURE: "Social pressure",
}
