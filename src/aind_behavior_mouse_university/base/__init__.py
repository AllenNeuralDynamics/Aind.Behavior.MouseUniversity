from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Generic, List, TypeVar, Optional

from aind_data_schema.base import AindCoreModel, AindModel
from pydantic import Field, GetJsonSchemaHandler, ValidationError, field_serializer
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from semver import Version


class AindBehaviorCoreModel(AindCoreModel, extra="ignore"):
    pass


class AindBehaviorModel(AindModel, extra="ignore"):
    pass


class SemVerAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Version:
            return Version.parse(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Version),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


class Task(AindBehaviorCoreModel):
    """Base class used to define the task logic of a mouse university task."""

    name: str
    description: str


TTask = TypeVar("TTask", bound=Task)


class Metrics(AindBehaviorCoreModel, Generic[TTask]):
    """Base class used to define the metrics model for a specific tasks in the mouse university."""

    name: str
    description: str = Field("", description="Description of the metrics.")
    task: TTask = Field(..., description="Task that the metrics belong to.")

    @field_serializer("task")
    def task_as_reference(self, task: TTask, _info):
        return Task.model_validate_json(task.model_dump_json())


class TransitionRule(AindBehaviorModel):
    """Base class used to define the stage transition logic of a mouse university task."""

    target_stage: Stage = Field(..., description="Target stage of the transition.")
    callable: Rule = Field(..., description="Callable or reference to a callable that defines the transition rule.")
    description: str = Field("", description="Optional description of the transition rule.")

    @field_serializer("target_stage")
    def metrics_as_reference(self, target_stage: Stage, _info):
        return StageReference.model_validate_json(target_stage.model_dump_json())


class StageReference(AindBehaviorModel, Generic[TTask]):
    """Base class used to reference the stage logic of a mouse university task. You should not inherit from this class."""

    name: str = Field(..., description="Name of the stage.")
    task: Optional[TTask] = Field(None, description="Task that the stage belongs to.")
    stage_transitions: Optional[List[TransitionRule]] = Field(
        None, description="Stage transitions that the stage contains."
    )
    metrics: Optional[Metrics[TTask]] = Field(None, description="Metrics reference for the specific stage")
    description: str = Field("", description="Description of the stage.")

    @field_serializer("task")
    def task_as_reference(self, task: Optional[TTask], _info):
        return None

    @field_serializer("metrics")
    def metrics_as_reference(self, metrics: Optional[Metrics[TTask]], _info):
        return None

    @field_serializer("stage_transitions")
    def metrics_as_reference(self, stage_transitions: Optional[List[TransitionRule]], _info):
        return None

    def append_transition(self, transition: TransitionRule) -> None:
        self.stage_transitions.append(transition)

    def pop_transition(self, index: int) -> TransitionRule:
        return self.stage_transitions.pop(index)


class Stage(StageReference):
    """Base class used to define the stage logic of a mouse university task."""
    task: TTask = Field(..., description="Task that the stage belongs to.")
    stage_transitions: List[TransitionRule] = Field(
        ..., description="Stage transitions that the stage contains."
    )

    @field_serializer("task")
    def task_as_reference(self, task: Optional[TTask], _info):
        return Task.model_validate_json(task.model_dump_json())

    @field_serializer("metrics")
    def metrics_as_reference(self, metrics: Optional[Metrics[TTask]], _info):
        return Metrics.model_validate_json(metrics.model_dump_json())



class Curriculum(AindBehaviorCoreModel):
    """Base class used to define the curriculum in the mouse university."""

    name: str
    description: str
    stages: list[Stage] = Field(..., description="Stages that the curriculum contains.")


class Rule:

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Callable:
            return cls._deserialize_callable(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Callable),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(function=cls._serialize_callable),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

    @staticmethod
    def _deserialize_callable(value: str | Callable) -> Callable:
        if callable(value):
            return value
        else:
            split = value.rsplit(".", 1)
            if len(split) == 0:
                raise ValueError(
                    "Invalid rule value while attempting to deserialize callable. \
                        Got {value}, expected string in the format 'module.function'}"
                )
            elif len(split) == 1:
                return globals()[split]
            else:
                module = import_module(split[0])
                return getattr(module, split[1])

    @staticmethod
    def _serialize_callable(value: str | Callable) -> Callable:
        if isinstance(value, str):
            value = Rule._deserialize_callable(value)
        return value.__module__ + "." + value.__name__
