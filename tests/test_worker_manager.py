import pytest
from src.worker_manager import WorkerManager
from src.models import WorkerNode, TaskPlan
from pydantic import BaseModel

class DummyModel(BaseModel):
    messages: list = []

def dummy_func(state):
    return {"done": True}

def build_manager():
    wm = WorkerManager()
    node1 = WorkerNode(function=dummy_func, model=DummyModel, state_placeholder="s1", description="node one", name="n1")
    node2 = WorkerNode(function=dummy_func, model=None, state_placeholder="s2", description="node two", name="n2")
    wm.add_node(node1)
    wm.add_node(node2)
    return wm, node1, node2

def test_add_and_describe_nodes():
    wm, node1, node2 = build_manager()
    assert wm.workers == ["n1", "n2"]
    assert wm.worker_descriptions["n1"] == "node one"
    assert wm.workers_nodes["n2"] is node2

def test_get_worker_list_description():
    wm, _, _ = build_manager()
    desc = wm.get_worker_list_description()
    assert "**n1**: node one" in desc and "**n2**: node two" in desc

def test_get_dynamic_fields():
    wm, node1, node2 = build_manager()
    fields = wm.get_dynamic_fields()
    assert list(fields.keys()) == ["s1"]
    assert DummyModel in getattr(fields["s1"][0], "__args__", [])

def test_get_tasks_per_nodes():
    wm, node1, node2 = build_manager()
    tasks = [
        TaskPlan(task_id="1", task="t1", node_allocated="n1"),
        TaskPlan(task_id="2", task="t2", node_allocated="n2"),
        TaskPlan(task_id="3", task="t3", node_allocated="n1"),
    ]
    per_node = wm.get_tasks_per_nodes(tasks)
    assert [t.task_id for t in per_node["n1"]] == ["1", "3"]
    assert [t.task_id for t in per_node["n2"]] == ["2"]
