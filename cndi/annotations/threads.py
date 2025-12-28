import logging
from threading import Thread
from typing import List

from cndi.annotations import Component, ConditionalRendering
from cndi.consts import RCN_ENABLE_CONTEXT_THREADS
from cndi.env import getContextEnvironment

log = logging.getLogger(__name__)

def isContextThreadEnable(dependent):
    enabled = getContextEnvironment(RCN_ENABLE_CONTEXT_THREADS, defaultValue=False, castFunc=bool)
    if not enabled:
        log.warning(f"{dependent} Component depends on {__name__}.{ContextThreads.__name__}")
        log.warning(f"Context Threads is disable in property please enable it by setting {RCN_ENABLE_CONTEXT_THREADS} to true")

    return enabled

@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_ENABLE_CONTEXT_THREADS, defaultValue=False, castFunc=bool))
class ContextThreads:
    def __init__(self):
        self.threads: List[Thread] = list()

    def add_thread(self, thread):
        self.threads.append(thread)

    def clean_up(self):
        exitedThread = []
        for thread in self.threads:
            if not thread.is_alive():
                exitedThread.append(thread)

        for exitThread in exitedThread:
            self.threads.remove(exitThread)