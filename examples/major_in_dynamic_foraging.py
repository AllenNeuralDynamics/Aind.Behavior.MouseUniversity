from typing import Literal

from pydantic import Field

from aind_behavior_mouse_university.base import Curriculum, Metrics, Stage, Task, TransitionRule

# Define tasks


class TaskFoo(Task):
    """Example Foo task."""

    name: Literal["foo"] = "foo"
    description: Literal["Example task."] = "Example task."
    describedBy: Literal["foo.url"] = "foo.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    version: Literal["0.1.0"] = "0.1.0"
    param1: str = Field("on", description="Parameter 1")
    param_float_gain: float = Field(1.0, description="gain")


class MetricsFoo(Metrics[TaskFoo]):
    """Example Foo metrics."""

    name: Literal["foo_metrics"] = "foo_metrics"
    description: Literal["Example metrics."] = "Example metrics."
    describedBy: Literal["foo_metrics.url"] = "foo_metrics.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    task: TaskFoo = Field(TaskFoo.as_reference(), description="Task that the metrics belong to.")
    output1: float = Field(1, description="Parameter 1")
    output2: float = Field(0, description="Parameter 2")


class TaskBar(Task):
    """Example Bar task."""

    name: Literal["bar"] = "bar"
    description: Literal["Example task."] = "Example task."
    describedBy: Literal["bar.url"] = "bar.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    version: Literal["0.1.0"] = "0.1.0"
    param1: int = Field(1, description="Parameter 1")
    param2: str = Field("hard_mode_enabled", description="Parameter 2")


class MetricsBar(Metrics[TaskBar]):
    """Example Bar metrics."""

    name: Literal["bar_metrics"] = "bar_metrics"
    description: Literal["Example metrics."] = "Example metrics."
    describedBy: Literal["bar_metrics.url"] = "bar_metrics.url"
    schema_version: Literal["0.1.0"] = "0.1.0"
    task: TaskBar = Field(TaskBar.as_reference(), description="Task that the metrics belong to.")
    bar_regression_slope: float = Field(-0.2, description="slopes of regression")


# Define transitions
# The metrics should be sub classed here to include metrics specific for a task.
def rule1_bar(metrics: MetricsBar) -> bool:
    return metrics.bar_regression_slope > 0.5


def rule2_bar(metrics: MetricsBar) -> bool:
    my_lambda = lambda x: x < 2
    return my_lambda(metrics.bar_regression_slope)


def rule3_foo(metrics: MetricsFoo) -> bool:
    return metrics.output1 == metrics.output2


# Define stages
stage_1_specs = TaskBar(param2="A", param1=1)
stage_1_metrics = MetricsBar(bar_regression_slope=1.0)  # TODO reference to task is sufficient
stage1 = Stage(name="stage1", task=stage_1_specs, metrics=stage_1_metrics, stage_transitions=[])


stage_2_specs = TaskBar(param1=1, param2="B")
stage_2_metrics = MetricsBar(task=stage_2_specs)

stage2 = Stage(name="stage2", task=stage_2_specs, metrics=stage_2_metrics, stage_transitions=[])

#
stage_3_specs = TaskFoo(param1="A", param_float_gain=2.0)
stage_3_metrics = MetricsFoo(task=stage_3_specs, output2=10)

stage3 = Stage(name="stage3", task=stage_3_specs, metrics=stage_3_metrics, stage_transitions=[])


# Define transitions

transitions_from_stage1 = [
    TransitionRule(target_stage=stage2, callable=rule1_bar, description="rule1"),
]
_ = [stage1.append_transition(transition) for transition in transitions_from_stage1]

transitions_from_stage2 = [
    TransitionRule(target_stage=stage1, callable=rule1_bar, description="rule1"),
    TransitionRule(target_stage=stage3, callable=rule2_bar, description="rule2"),
]
_ = [stage2.append_transition(transition) for transition in transitions_from_stage2]

transitions_from_stage3 = [
    TransitionRule(target_stage=stage1, callable=rule3_foo, description="rule3"),
    TransitionRule(target_stage=stage2, callable=rule3_foo, description="rule3"),
]
_ = [stage3.append_transition(transition) for transition in transitions_from_stage3]

# Define curriculum

major_in_dynamic_foraging = Curriculum(
    describedBy="ASD",
    schema_version="0.1.0",
    name="major_in_dynamic_foraging",
    description="Example curriculum.",
    stages=[stage1, stage2, stage3],
)

with open("file.json", "w") as f:
    f.write(major_in_dynamic_foraging.model_dump_json(indent=3))

deserialized = Curriculum.model_validate_json(major_in_dynamic_foraging.model_dump_json())
print(deserialized)

print("Should I transition from stage 1 to stage 2?")
print(deserialized.stages[0].stage_transitions[0].callable(MetricsBar(task=stage_1_specs, bar_regression_slope=7)))
# prints "True"
