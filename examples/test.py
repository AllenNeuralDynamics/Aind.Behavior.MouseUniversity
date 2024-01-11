from typing import Literal, Dict
from pydantic import Field
from aind_behavior_mouse_university.base import Metrics, Stage, Task, Curriculum, TransitionRule, StageReference
from aind_behavior_mouse_university.base import AindBehaviorModel


class TaskFoo(Task):
    """Example Foo task."""

    name: Literal["foo"] = "foo"
    description: Literal["Example task."] = "Example task."
    describedBy: Literal["foo.url"] = "foo.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    param1: str = Field("on", description="Parameter 1")
    param_float_gain: float = Field(1.0, description="gain")


class MetricsFoo(Metrics[TaskFoo]):
    """Example Foo metrics."""

    name: Literal["foo_metrics"] = "foo_metrics"
    description: Literal["Example metrics."] = "Example metrics."
    describedBy: Literal["foo_metrics.url"] = "foo_metrics.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    task: TaskFoo = Field(..., description="Task that the metrics belong to.") # TODO we should be able to provide the reference to a task without having to instantiate it.
    output1: float = Field(1, description="Parameter 1")
    output2: float = Field(0, description="Parameter 2")


stage_3_specs = TaskFoo(param1="A", param_float_gain=2.0)
stage_3_metrics = MetricsFoo(task=stage_3_specs, output2=10)

stage3 = (
    Stage(
        name="stage3",
        task=stage_3_specs,
        metrics=stage_3_metrics,
        stage_transitions=[]))


print(stage3.model_dump())
StageReference.model_validate(stage3.model_dump())
