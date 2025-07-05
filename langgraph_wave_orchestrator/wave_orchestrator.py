from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional, Generic, TypeVar, Union, Type

from .models import WorkerNode, TaskPlan, ParallelTasksPlans
from typing import List, Literal
from pydantic import BaseModel, Field
from langgraph.graph import START, StateGraph
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from .worker_manager import WorkerManager
from .wave_manager import WaveManager
from .state_manager import StateManager
from .prompts import create_answering_prompt, create_planning_prompt
import json

# Define generic type variables
StateT = TypeVar('StateT')
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class WaveOrchestrator(Generic[StateT, InputT, OutputT]):
    def __init__(self, llm: any, user_state_params: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None, 
                 answering_prompt_override: str = None, planning_prompt_override: str = None):
        self.llm = llm
        self.worker_manager: WorkerManager[InputT, OutputT] = WorkerManager()
        self.state_manager: StateManager[StateT] = StateManager(self.worker_manager, user_state_params)
        self.wave_manager: WaveManager[InputT, OutputT] = WaveManager(self.worker_manager)
        self.answering_prompt_override = answering_prompt_override
        self.planning_prompt_override = planning_prompt_override
        self.user_state_params = user_state_params
    
    def add_node(self, node: WorkerNode[InputT, OutputT]):
        self.worker_manager.add_node(node)
    
    def create_answering_node(self):
        def answering_node(state: StateT) -> Command[Literal["__end__"]]:
            results = state.task_results
            system_prompt = create_answering_prompt(
                user_question=state.messages[-1].content,
                task_results=results,
                user_override=self.answering_prompt_override
            )
            response = self.llm.invoke(system_prompt)
            update = {
                "messages": [*state.messages, response]
            }
            return Command(goto="__end__", update=update)
        return answering_node
    
    def create_sequential_progress_node(self):
        def sequential_progress(state: StateT) -> Command[Literal[*self.worker_manager.workers,"answering"]]:
            print(f"sequential_progress")
            
            update = self.state_manager.prepare_command_output(state)
            print(f"length of waves: {len(state.execution_waves.waves)} current wave: {state.current_wave}")
            if self.wave_manager.is_waves_complete(state):
                print(f"answering node")
                return Command(goto="answering", update=update)
            current_wave = self.wave_manager.get_current_wave_tasks(state)
            goto = []
            for task in current_wave:
                if task.node_allocated in self.worker_manager.workers_nodes:
                    node = self.worker_manager.workers_nodes[task.node_allocated]
                    # Create a new message list with the task content
                    task_message = HumanMessage(content=str(task.task))
                    update[node.state_placeholder] = [task_message]
                    goto.append(task.node_allocated)
            return Command(
                goto=goto,
                update=update
            )
        return sequential_progress
    
    def create_sequential_plan_node(self):
        def sequential_plan_node(state: StateT) -> Command[Literal["progress"]]:
            llm = self.llm
            worker_list = self.worker_manager.get_worker_list_description()
            
            plan_prompt = create_planning_prompt(
                worker_list=worker_list,
                user_query=state.messages[-1].content,
                user_override=self.planning_prompt_override
            )
            
            class SequentialTaskPlanRequest(BaseModel):
                task_plans: List[TaskPlan] = Field(description="Sequential list of tasks")
            
            llm_with_structured_output = llm.with_structured_output(SequentialTaskPlanRequest)
            response = llm_with_structured_output.invoke(plan_prompt)
            
            plans = ParallelTasksPlans(task_plans=response.task_plans)
            print(f"📋 Sequential plan: {len(response.task_plans)} tasks")
            print(f"response.task_plans: {response.task_plans}")
            execution_waves = self.wave_manager.create_execution_waves(response.task_plans)
            print(f"execution waves: {execution_waves}")    
            print(f"task plans: {plans}")
            # Reset current_wave to 0 for new planning cycle
            return Command(goto="progress", update={
                "task_plans": plans, 
                "execution_waves": execution_waves,
                "current_wave": 0
            })
        
        return sequential_plan_node
    
    def compile(self) -> StateGraph[StateT]:
        DynamicParallelStarState = self.state_manager.create_dynamic_state()
        self.graph = StateGraph(DynamicParallelStarState)
        
        for node_name in self.worker_manager.workers_nodes:
            self.graph.add_node(node_name, self.worker_manager.workers_nodes[node_name].function)
            self.graph.add_edge(node_name, "progress")
        self.graph.add_node("plan_node", self.create_sequential_plan_node())
        self.graph.add_node("progress", self.create_sequential_progress_node())
        self.graph.add_node("answering", self.create_answering_node())
        self.graph.add_edge(START, "plan_node")
        return self.graph.compile()