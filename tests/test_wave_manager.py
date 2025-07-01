from src.worker_manager import WorkerManager
from src.wave_manager import WaveManager
from src.models import WorkerNode, TaskPlan, ExecutionWaves
from pydantic import BaseModel

class DummyModel(BaseModel):
    messages: list = []

def dummy_func(state):
    return {}


def build_wave_manager():
    wm = WorkerManager()
    node1 = WorkerNode(function=dummy_func, model=DummyModel, state_placeholder="s1", description="d1", name="n1")
    node2 = WorkerNode(function=dummy_func, model=None, state_placeholder="s2", description="d2", name="n2")
    wm.add_node(node1)
    wm.add_node(node2)
    return WaveManager(wm), wm

def test_create_execution_waves():
    wave_manager, wm = build_wave_manager()
    tasks = [
        TaskPlan(task_id="1", task="t1", node_allocated="n1"),
        TaskPlan(task_id="2", task="t2", node_allocated="n2"),
        TaskPlan(task_id="3", task="t3", node_allocated="n1"),
    ]
    waves = wave_manager.create_execution_waves(tasks)
    assert waves.waves[0][0].task_id == "1"
    assert waves.waves[0][1].task_id == "2"
    assert waves.waves[1][0].task_id == "3"

def test_is_waves_complete_and_get_current_tasks():
    wave_manager, wm = build_wave_manager()
    exec_waves = ExecutionWaves(waves={0: [TaskPlan(task_id="1", task="t", node_allocated="n1")]})
    state = type("S", (), {"current_wave": 0, "execution_waves": exec_waves})()
    assert not wave_manager.is_waves_complete(state)
    tasks = wave_manager.get_current_wave_tasks(state)
    assert tasks[0].task_id == "1"
    state.current_wave = 1
    assert wave_manager.is_waves_complete(state)
