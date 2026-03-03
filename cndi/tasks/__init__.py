import threading
import time
import uuid
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from queue import Queue

from cndi.annotations import Component, ConditionalRendering
from cndi.annotations.threads import ContextThreads
from cndi.consts import RCN_ENABLE_CONTEXT_THREADS, RCN_ENABLE_TASK_EXECUTOR, RCN_TASK_EXECUTOR_NUM_THREADS
from cndi.env import getContextEnvironment
import logging

logger = logging.getLogger(__name__)

@dataclass
class Task:
    def __init__(self, name: str, callback,  completed_callback=None):
        self.name = name
        self.callback = callback
        self.completed_callback = completed_callback
        self.result = None
        self.id = uuid.uuid4().__str__()
        self.status = TaskStatus.CREATED

class TaskStatus(Enum):
    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_ENABLE_TASK_EXECUTOR, defaultValue=False, castFunc=bool)
                      and getContextEnvironment(RCN_TASK_EXECUTOR_NUM_THREADS, defaultValue=1, castFunc=int) > 0
                      and getContextEnvironment(RCN_ENABLE_CONTEXT_THREADS, defaultValue=False, castFunc=bool))
class TaskExecutor(threading.Thread):
    def __init__(self, context_threads: ContextThreads):
        super().__init__()
        self.tasks = {}
        self.num_threads = getContextEnvironment(RCN_TASK_EXECUTOR_NUM_THREADS, defaultValue=1, castFunc=int)
        self.queue = Queue()
        self.running = False
        context_threads.add_thread(self)
        self.start()

    def add_task(self, task: Task):
        self.tasks[task.id] = task
        self.queue.put(task)
        task.status = TaskStatus.SCHEDULED
        logger.debug(f"Added task {task.name} with id {task.id} to the queue")

    def remove_task(self, name: str):
        if name in self.tasks:
            del self.tasks[name]

    def execute(self, id: str, *args, **kwargs):
        if id in self.tasks:
            return self.tasks[id].callback(*args, **kwargs)
        else:
            raise Exception(f"Task with name {id} not found")

    def get_task(self,id):
        if id in self.tasks:
            return self.tasks[id]
        else:
            raise Exception(f"Task with name {id} not found")

    def run(self):
        while True:
            queue_size = self.queue.qsize()
            tasks = []
            future_results = []
            for i in range(min(queue_size, self.num_threads)):
                tasks.append(self.queue.get())
            if tasks.__len__() > 0:
                logger.debug(f"Executing {tasks.__len__()} tasks")
                with ThreadPoolExecutor(max_workers=tasks.__len__()) as executor:
                    for task in tasks:
                        future = executor.submit(self.execute, task.id)
                        task.status = TaskStatus.RUNNING
                        task.running = True
                        future_results.append(dict(future=future, id=task.id))

                    executor.shutdown(wait=True)

                    for future in future_results:
                        self.tasks[future['id']].result = future['future'].result() if future['future'].exception() is None else future['future'].exception()
                        self.tasks[future['id']].status = TaskStatus.COMPLETED if future['future'].exception() is None else TaskStatus.FAILED
                        self.tasks[future['id']].running = False

                logger.debug(f"Finished executing {tasks.__len__()} tasks")
            else:
                time.sleep(1)