from typing import List, Dict, Optional
from .models import WorkerNode, TaskPlan


class WorkerManager:
    def __init__(self):
        self.workers = []
        self.worker_descriptions = {}
        self.workers_nodes = {}
    
    def add_node(self, node: WorkerNode):
        self.workers_nodes[node.name] = node
        self.workers.append(node.name)
        self.worker_descriptions[node.name] = node.description
    
    def get_worker_list_description(self) -> str:
        return ', '.join([f'**{worker}**: {self.worker_descriptions[worker]}' for worker in self.workers])
    
    def get_dynamic_fields(self) -> Dict[str, tuple]:
        dynamic_fields = {}
        for node_name in self.workers_nodes:
            if self.workers_nodes[node_name].model:
                dynamic_fields[self.workers_nodes[node_name].state_placeholder] = (Optional[self.workers_nodes[node_name].model], None)
        return dynamic_fields
    
    def get_tasks_per_nodes(self, task_plans: List[TaskPlan]) -> Dict[str, List[TaskPlan]]:
        return {
            node: [task for task in task_plans if task.node_allocated == node]
            for node in self.workers
        } 