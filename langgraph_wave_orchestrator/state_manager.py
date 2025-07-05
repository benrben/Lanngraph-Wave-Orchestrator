from pydantic import create_model, BaseModel
from .models import ParallelStarState
from .worker_manager import WorkerManager
from typing import Dict, Any, Optional, Generic, TypeVar, Type, Union, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Define generic type variables
StateT = TypeVar('StateT')
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class StateManager(Generic[StateT]):
    def __init__(self, worker_manager: WorkerManager[InputT, OutputT], user_state_params: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None):
        self.worker_manager = worker_manager
        self.user_state_params = self._process_user_state_params(user_state_params)
    
    def _process_user_state_params(self, user_state_params: Optional[Union[Dict[str, Any], Type[BaseModel]]]) -> Dict[str, Any]:
        """Process user state parameters, handling both dict and Pydantic model inputs."""
        if user_state_params is None:
            return {}
        
        if isinstance(user_state_params, dict):
            return user_state_params
        
        # If it's a Pydantic model class, extract field information
        if isinstance(user_state_params, type) and issubclass(user_state_params, BaseModel):
            field_dict = {}
            for field_name, field_info in user_state_params.model_fields.items():
                field_type = field_info.annotation
                # Handle default values and default_factory
                if field_info.default is not None:
                    default_value = field_info.default
                elif field_info.default_factory is not None:
                    default_value = field_info.default_factory
                else:
                    default_value = None
                field_dict[field_name] = (field_type, default_value)
            return field_dict
        
        # If it's an instance of a Pydantic model, extract from its class
        if isinstance(user_state_params, BaseModel):
            return self._process_user_state_params(type(user_state_params))
        
        # Fallback to empty dict if we can't process it
        return {}
    
    def prepare_command_output(self, state: StateT) -> Dict[str, Any]:
        if state.current_wave > 0:
            updated_task_results = dict(state.task_results)
            for task in state.execution_waves.waves[state.current_wave - 1]:
                node_allocated = task.node_allocated
                node = self.worker_manager.workers_nodes[node_allocated]
                # Handle BaseMessage list structure
                messages = getattr(state, node.state_placeholder)
                if messages and len(messages) > 0:
                    result = messages[-1].content
                    updated_task_results[task.task] = result
        else:
            updated_task_results = state.task_results
        return {
            "current_wave": state.current_wave + 1,
            "task_results": updated_task_results
        }
    
    def create_dynamic_state(self) -> Type[StateT]:
        # Create dynamic fields from user-provided state parameters
        dynamic_fields = {}
        for field_name, field_config in self.user_state_params.items():
            if isinstance(field_config, tuple):
                # field_config is (type, default_value)
                dynamic_fields[field_name] = field_config
            else:
                # field_config is just the type, default to None
                dynamic_fields[field_name] = (Optional[field_config], None)
        
        # Add worker-specific fields for BaseMessage communication
        for node_name, node in self.worker_manager.workers_nodes.items():
            # Use annotated BaseMessage list for LangGraph compatibility
            def create_empty_list():
                return []
            dynamic_fields[node.state_placeholder] = (
                Annotated[List[BaseMessage], add_messages], 
                create_empty_list
            )
        
        return create_model("DynamicParallelStarState", __base__=ParallelStarState, **dynamic_fields) 