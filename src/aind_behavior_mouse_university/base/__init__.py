from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Generic, List, Literal, TypeVar

from aind_data_schema.base import AindCoreModel, AindModel
from pydantic import Field, GetJsonSchemaHandler, field_serializer
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
    describedBy: Literal["tbd_link.url"] = "tbd_link.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    task: TTask = Field(..., description="Task that the metrics belong to.")
    metrics: Any = Field(None, description="Metrics that the task contains.")


class TransitionRule(AindBehaviorModel):
    """Base class used to define the stage transition logic of a mouse university task."""

    target_stage: Stage = Field(..., description="Target stage of the transition.")
    callable: Rule = Field(..., description="Callable or reference to a callable that defines the transition rule.")
    description: str = Field("", description="Optional description of the transition rule.")
    # Todo Consider adding a validation step to the transition rule. e.g. Callable[[Metrics], bool]


class Stage(AindBehaviorModel, Generic[TTask]):
    """Base class used to define the stage logic of a mouse university task."""

    name: str = Field(..., description="Name of the stage.")
    description: str = Field("", description="Description of the stage.")
    task: TTask = Field(..., description="Task that the stage belongs to.")
    stage_transitions: List[TransitionRule] = Field(
        default_factory=list, description="Stage transitions that the stage contains."
    )
    metrics: Metrics[TTask] = Field(..., description="Metrics reference for the specific stage")

    @field_serializer("task")
    def task_as_reference(self, task: TTask, _info):
        return Task.model_validate_json(task.model_dump_json())

    @field_serializer("metrics")
    def metrics_as_reference(self, metrics: Metrics[TTask], _info):
        return Metrics.model_validate_json(metrics.model_dump_json())

    def append_transition(self, transition: TransitionRule) -> None:
        self.stage_transitions.append(transition)

    def pop_transition(self, index: int) -> TransitionRule:
        return self.stage_transitions.pop(index)


class Curriculum(AindBehaviorCoreModel):
    """Base class used to define the curriculum in the mouse university."""

    name: str
    description: str
    describedBy: Literal["tbd_link.url"] = "tbd_link.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
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
