from typing import List
from .models import TaskPlan, ExecutionWaves
from .worker_manager import WorkerManager


class WaveManager:
    def __init__(self, worker_manager: WorkerManager):
        self.worker_manager = worker_manager
    
    def create_execution_waves(self, task_plans: List[TaskPlan]) -> ExecutionWaves:
        """
        Creates execution waves from task plans by organizing tasks by node
        and distributing them across parallel execution waves.
        """
        tasks_per_nodes = self.worker_manager.get_tasks_per_nodes(task_plans)
        more_task_node_name = max(tasks_per_nodes, key=lambda x: len(tasks_per_nodes[x]))
        execution_waves = ExecutionWaves()
        max_tasks = len(tasks_per_nodes[more_task_node_name])
        for wave_num in range(max_tasks):
            for node in tasks_per_nodes:
                if len(tasks_per_nodes[node]) > wave_num:
                    task_plan = tasks_per_nodes[node][wave_num]
                    if wave_num not in execution_waves.waves:
                        execution_waves.waves[wave_num] = []
                    execution_waves.waves[wave_num].append(task_plan)
        return execution_waves
    
    def is_waves_complete(self, state: any) -> bool:
        return state.current_wave == len(state.execution_waves.waves)
    
    def get_current_wave_tasks(self, state: any) -> List[TaskPlan]:
        return state.execution_waves.waves[state.current_wave] 