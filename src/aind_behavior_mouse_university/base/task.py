from __future__ import annotations

from typing import Generic, List, Literal, TypeVar

from pydantic import Field, field_serializer

from aind_behavior_mouse_university.base import AindBehaviorCoreModel, AindBehaviorModel


class Task(AindBehaviorCoreModel):
    """Base class used to define the task logic of a mouse university task."""

    name: str
    description: str
    describedBy = "tbd_link.url"
    schema_version: Literal["0.1.0"] = "0.1.0"


TTask = TypeVar("TTask", bound=Task)


class TransitionRule(AindBehaviorModel):
    """Base class used to define the transition rule logic of a mouse university task."""

    name: str = Field(..., description="Name of the transition rule.")
    file: str = Field("todo", description="File that contains the transition rule.")
    url: str = Field("todo", description="URL to the file that contains the transition rule.")
    version: str = Field("todo", description="Version of the transition rule.")


class StageTransition(AindBehaviorModel):
    """Base class used to define the stage transition logic of a mouse university task."""

    target_state: Stage = Field(..., description="Target stage of the transition.")
    transition_rule: TransitionRule = Field(..., description="Transition rule that defines the transition.")
    description: str = Field("", description="Optional description of the stage transition.")


class Stage(AindBehaviorModel, Generic[TTask]):
    """Base class used to define the stage logic of a mouse university task."""

    name: str = Field(..., description="Name of the stage.")
    description: str = Field("", description="Description of the stage.")
    task: TTask = Field(..., description="Task that the stage belongs to.")
    stage_transitions: List[StageTransition] = Field(
        default_factory=list, description="Stage transitions that the stage contains."
    )

    @field_serializer("task")
    def as_reference(self, task: TTask, _info):
        return Task.model_validate_json(task.model_dump_json())


class Curriculum(AindBehaviorCoreModel):
    """Base class used to define the curriculum in the mouse university."""

    name: str
    description: str
    describedBy = "tbd_link.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    stages: list[Stage] = Field(..., description="Stages that the curriculum contains.")
