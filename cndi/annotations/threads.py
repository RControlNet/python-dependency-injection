import logging
import os
import signal
import sys
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
        log.warning(f"SingletonContext Threads is disable in property please enable it by setting {RCN_ENABLE_CONTEXT_THREADS} to true")

    return enabled

@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_ENABLE_CONTEXT_THREADS, defaultValue=False, castFunc=bool))
class ContextThreads:
    def __init__(self):
        self.threads: List[Thread] = list()
        self.shutdownInProgress = False
        self.registerSignalHandlers()

    def add_thread(self, thread):
        self.threads.append(thread)

    def clean_up(self):
        exitedThread = []
        for thread in self.threads:
            if not thread.is_alive():
                exitedThread.append(thread)

        for exitThread in exitedThread:
            self.threads.remove(exitThread)

    def registerSignalHandlers(self):
        """
        Registers OS signals for graceful and hard shutdown of context threads.

        SIGINT/SIGTERM trigger a graceful shutdown, giving every registered thread a
        chance to stop on its own before the process joins/terminates them.
        SIGQUIT (or a repeated SIGINT/SIGTERM received while a graceful shutdown is
        already running) triggers an immediate hard shutdown of the process.
        """
        try:
            signal.signal(signal.SIGINT, self.__on_graceful_shutdown_signal)
            signal.signal(signal.SIGTERM, self.__on_graceful_shutdown_signal)
            if hasattr(signal, "SIGQUIT"):
                signal.signal(signal.SIGQUIT, self.__on_hard_shutdown_signal)
        except ValueError:
            log.warning("Unable to register signal handlers for ContextThreads, this can happen when it is "
                         "constructed outside of the main thread")

    def __on_graceful_shutdown_signal(self, signum, frame):
        signalName = signal.Signals(signum).name
        if self.shutdownInProgress:
            log.warning(f"Received {signalName} while shutdown already in progress, forcing hard shutdown")
            self.hardShutdown()
            return

        log.info(f"Received {signalName}, starting graceful shutdown of context threads")
        self.gracefulShutdown()

    def __on_hard_shutdown_signal(self, signum, frame):
        signalName = signal.Signals(signum).name
        log.warning(f"Received {signalName}, forcing hard shutdown of context threads")
        self.hardShutdown()

    def gracefulShutdown(self, timeout: float = 10):
        """
        Attempts to stop every registered thread cleanly.

        Threads exposing a `stop()` method are asked to stop cooperatively, then each
        thread is joined up to `timeout` seconds. Once done the interpreter is exited
        via sys.exit so cleanup handlers (e.g. atexit, logging) still run.
        """
        self.shutdownInProgress = True
        self.clean_up()

        for thread in self.threads:
            stop = getattr(thread, "stop", None)
            if callable(stop):
                try:
                    stop()
                except Exception as e:
                    log.error(f"Failed to gracefully stop thread {thread.name}: {e}")

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=timeout)
                if thread.is_alive():
                    log.warning(f"Thread {thread.name} did not stop within {timeout} seconds")

        self.clean_up()
        log.info("Graceful shutdown of context threads completed")
        sys.exit(0)

    def hardShutdown(self):
        """
        Immediately terminates the process without waiting for threads to stop.
        """
        log.warning("Forcing hard shutdown, terminating process immediately")
        os._exit(1)