from threading import Thread
from typing import List

from cndi.annotations import Component, ConditionalRendering
from cndi.env import getContextEnvironment


@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment("management.context.thread.enable", defaultValue=False, castFunc=bool))
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