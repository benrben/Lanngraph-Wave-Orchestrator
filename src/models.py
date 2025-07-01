from typing import Annotated, List, Dict, Set, Optional, Type, Callable
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Literal

class TaskPlan(BaseModel):
    task_id: str = Field(description="Unique identifier for the task")
    task: str = Field(description="The task description")
    node_allocated: str = Field(description="The node allocated to the task")

class TaskResult(BaseModel):
    task_id: str = Field(description="Task identifier")
    task_status: Literal["pending", "running", "completed", "failed"] = Field(description="The status of the task")
    task_result: str = Field(description="The result of the task")
    execution_time: float = Field(description="Execution time in seconds", default=0.0)


class ExecutionWaves(BaseModel):
    waves: Dict[int, List[TaskPlan]] = Field(
        description="Dictionary mapping wave number to list of tasks in that wave",
        default_factory=dict,
    )
    
class ParallelTasksPlans(BaseModel):
    task_plans: List[TaskPlan] = Field(description="The task plans with dependencies")
    max_waves: int = Field(description="Maximum number of execution waves", default=1)


# Worker task state for individual node execution
class WorkerTaskState(BaseModel):
    task_id: str
    task: str
    node_allocated: str
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)

class WorkerNode(BaseModel):
    function: Callable = Field(description="The function to execute")
    model: Optional[Type[BaseModel]] = Field(description="The model to use", default=None)
    state_placeholder: str = Field(description="The state placeholder")
    description: str = Field(description="The description")
    name: str = Field(description="The name")


class ParallelStarState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    task_plans: ParallelTasksPlans = Field(
        description="The task plans", default_factory=lambda: ParallelTasksPlans(task_plans=[])
    )
    task_results: Dict[str, str] = Field(
        description="Results indexed by task_id", default_factory=dict
    )
    current_wave: int = Field(description="Current execution wave", default=0)
    active_tasks: Set[str] = Field(
        description="Currently running task IDs", default_factory=set
    )
    execution_waves: ExecutionWaves = Field(
        description="Execution waves", default_factory=ExecutionWaves
    )
