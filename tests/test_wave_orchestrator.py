from langchain_core.messages import HumanMessage, AIMessage
from src.models import WorkerNode, TaskPlan
from src.wave_orchestrator import WaveOrchestrator
from pydantic import BaseModel

class DummyLLM:
    def __init__(self):
        self.invoked = []
    def invoke(self, prompt):
        self.invoked.append(prompt)
        return AIMessage(content="ok")
    def with_structured_output(self, model):
        class Wrapper:
            def __init__(self, outer):
                self.outer = outer
            def invoke(self, prompt):
                # return simple valid object
                return model(task_plans=[TaskPlan(task_id="1", task="t", node_allocated="n1")])
        return Wrapper(self)

class DummyModel(BaseModel):
    messages: list = []

def dummy_func(state):
    return {"dummy": True}

def setup_orchestrator():
    orch = WaveOrchestrator(llm=DummyLLM())
    node = WorkerNode(function=dummy_func, model=DummyModel, state_placeholder="s1", description="d", name="n1")
    orch.add_node(node)
    return orch

def test_create_answering_node():
    orch = setup_orchestrator()
    node_fn = orch.create_answering_node()
    state = type("S", (), {"task_results": {"a": "b"}, "messages": [HumanMessage(content="q")]} )()
    cmd = node_fn(state)
    assert cmd.goto == "__end__"
    assert isinstance(cmd.update["messages"][-1], AIMessage)


def test_create_sequential_plan_node():
    orch = setup_orchestrator()
    plan_fn = orch.create_sequential_plan_node()
    state = type("S", (), {"messages": [HumanMessage(content="q")]} )()
    cmd = plan_fn(state)
    assert cmd.goto == "progress"
    assert cmd.update["execution_waves"].waves


def test_create_sequential_progress_node_and_compile():
    orch = setup_orchestrator()
    # create simple plan manually
    tasks = [TaskPlan(task_id="1", task="t", node_allocated="n1")]
    orch.wave_manager = orch.wave_manager  # ensure wave_manager exists
    exec_waves = orch.wave_manager.create_execution_waves(tasks)
    state = type("S", (), {
        "messages": [],
        "task_plans": tasks,
        "task_results": {},
        "execution_waves": exec_waves,
        "current_wave": 0,
    })()
    progress_fn = orch.create_sequential_progress_node()
    cmd = progress_fn(state)
    assert cmd.goto == ["n1"]
    assert "s1" in cmd.update
    compiled = orch.compile()
    assert compiled


def test_progress_node_when_complete_and_no_model():
    orch = WaveOrchestrator(llm=DummyLLM())
    node = WorkerNode(function=dummy_func, model=None, state_placeholder="s0", description="d", name="n0")
    orch.add_node(node)
    tasks = [TaskPlan(task_id="1", task="t", node_allocated="n0")]
    exec_waves = orch.wave_manager.create_execution_waves(tasks)
    state = type(
        "S", (), {
            "messages": [],
            "task_plans": tasks,
            "task_results": {},
            "execution_waves": exec_waves,
            "s0": DummyModel(messages=[AIMessage(content="r")]),
            "current_wave": len(exec_waves.waves),
        }
    )()
    progress_fn = orch.create_sequential_progress_node()
    cmd = progress_fn(state)
    assert cmd.goto == "answering"


def test_progress_node_without_model_branch():
    orch = WaveOrchestrator(llm=DummyLLM())
    node = WorkerNode(function=dummy_func, model=None, state_placeholder="s0", description="d", name="n0")
    orch.add_node(node)
    tasks = [TaskPlan(task_id="1", task="t", node_allocated="n0")]
    exec_waves = orch.wave_manager.create_execution_waves(tasks)
    state = type(
        "S", (), {
            "messages": [],
            "task_plans": tasks,
            "task_results": {},
            "execution_waves": exec_waves,
            "s0": DummyModel(messages=[AIMessage(content="r")]),
            "current_wave": 0,
        }
    )()
    progress_fn = orch.create_sequential_progress_node()
    cmd = progress_fn(state)
    assert cmd.goto == ["n0"]
    assert "s0" in cmd.update
