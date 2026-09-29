"""What players are allowed to see of a scenario.

There is deliberately NO weights/scores field anywhere in this file. A field that
doesn't exist can't be leaked, so this is safer than remembering to exclude it.
"""

from typing import Literal

from pydantic import BaseModel


class ChoicePublic(BaseModel):
    id: int
    label: Literal["A", "B", "C"]
    text: str


class ScenarioPublic(BaseModel):
    id: int
    title: str
    situation_text: str
    category: str  # the category slug
    choices: list[ChoicePublic]


class CategoryPublic(BaseModel):
    id: int
    slug: str
    name: str
    emoji: str
    scenario_count: int
    playable: bool  # enough scenarios to fill a whole round


class RandomOption(BaseModel):
    scenario_count: int
    playable: bool


class CategoriesResponse(BaseModel):
    round_length: int
    random: RandomOption
    categories: list[CategoryPublic]
