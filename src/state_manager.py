from pydantic import create_model
from src.models import ParallelStarState
from .worker_manager import WorkerManager


class StateManager:
    def __init__(self, worker_manager: WorkerManager):
        self.worker_manager = worker_manager
    
    def prepare_command_output(self, state: any):
        if state.current_wave > 0:
            updated_task_results = dict(state.task_results)
            for task in state.execution_waves.waves[state.current_wave - 1]:
                node_allocated = task.node_allocated
                node = self.worker_manager.workers_nodes[node_allocated]
                placeholder_value = getattr(state, node.state_placeholder)
                if hasattr(placeholder_value, "messages"):
                    message = placeholder_value.messages[-1]
                else:
                    message = placeholder_value
                result = message.content if hasattr(message, "content") else str(message)
                updated_task_results[task.task] = result
        else:
            updated_task_results = state.task_results
        return {
            "current_wave": state.current_wave + 1,
            "task_results": updated_task_results
        }
    
    def create_dynamic_state(self):
        dynamic_fields = self.worker_manager.get_dynamic_fields()
        return create_model("DynamicParallelStarState", __base__=ParallelStarState, **dynamic_fields) 