from langchain_core.messages import HumanMessage, AIMessage
from src.worker_manager import WorkerManager
from src.state_manager import StateManager
from src.models import WorkerNode, TaskPlan, ExecutionWaves
from pydantic import BaseModel

class DummyModel(BaseModel):
    messages: list = []

def dummy_func(state):
    return {}

def setup_manager():
    wm = WorkerManager()
    node = WorkerNode(function=dummy_func, model=DummyModel, state_placeholder="s1", description="d", name="n1")
    wm.add_node(node)
    return wm, node

def test_prepare_command_output_first_wave():
    wm, node = setup_manager()
    sm = StateManager(wm)
    exec_waves = ExecutionWaves(waves={0: [TaskPlan(task_id="1", task="t1", node_allocated="n1")]})
    state = type("S", (), {
        "current_wave": 0,
        "task_results": {},
        "execution_waves": exec_waves,
        "s1": DummyModel(messages=[AIMessage(content="r")]),
    })()
    out = sm.prepare_command_output(state)
    assert out == {"current_wave": 1, "task_results": {}}

def test_prepare_command_output_subsequent_wave():
    wm, node = setup_manager()
    sm = StateManager(wm)
    exec_waves = ExecutionWaves(waves={0: [TaskPlan(task_id="1", task="t1", node_allocated="n1")]})
    state = type("S", (), {
        "current_wave": 1,
        "task_results": {},
        "execution_waves": exec_waves,
        "s1": DummyModel(messages=[HumanMessage(content="task")]),
    })()
    out = sm.prepare_command_output(state)
    assert out["current_wave"] == 2
    assert out["task_results"] == {"t1": "task"}

def test_create_dynamic_state():
    wm, node = setup_manager()
    sm = StateManager(wm)
    Dynamic = sm.create_dynamic_state()
    field_names = Dynamic.__fields__.keys()
    assert "s1" in field_names
