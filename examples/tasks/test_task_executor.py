import time

from cndi.annotations import Autowired
from cndi.initializers import AppInitializer
from cndi.env import RCN_ENVS_CONFIG, getContextEnvironment
from cndi.consts import RCN_ENABLE_CONTEXT_THREADS

import os

from cndi.tasks import TaskExecutor, Task

os.environ[RCN_ENVS_CONFIG + '.' + RCN_ENABLE_CONTEXT_THREADS] = "True"
os.environ[RCN_ENVS_CONFIG + '.' + "task.executor.enable"] = "True"

def test_task():
    print("Test Task Executed")
    raise Exception("Test Task Failed")

@Autowired()
def set_task_executor(task_executor: TaskExecutor):
    print("Task Executor Injected: ", task_executor)
    task = Task("test_task", test_task)
    task_executor.add_task(task)

    time.sleep(5)

    _task = task_executor.get_task(task.id)
    print("Executed Task Result: ", _task.result, _task.status)


if __name__ == '__main__':
    app_initializer = AppInitializer()
    app_initializer.componentScan("cndi.tasks")
    app_initializer.run()