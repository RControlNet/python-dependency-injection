import threading
import time
import logging

from cndi.annotations import Component
from cndi.env import getContextEnvironment

class Event(object):
    def __init__(self, event_name=None, event_handler=None, event_object=None, event_invoker=None):
        self.event_name = event_name
        self.event_handler = event_handler
        self.event_invoker = event_invoker
        self.event_object = event_object

@Component
class EventHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.EVENTS_MAP = dict()
        self.sleepwait = getContextEnvironment("rcn.events.waittime", 2.0, float)
        self.expectedInvokerTime = getContextEnvironment("rcn.events.expected.invoker.time", 0.003, float)
        self._enabled = getContextEnvironment("rcn.events.enable", defaultValue=False, castFunc=bool)
        self.logger.debug(f"Expected Invoker Time set to {self.expectedInvokerTime} seconds")
        self.logger.debug(f"Sleep time set to {self.sleepwait} seconds")

    def postConstruct(self):
        if self._enabled:
            self.start()

    def registerEvent(self, event: Event):
        self.EVENTS_MAP[event.event_name] = event

    def triggerEventExplicit(self, eventName, **kwargs):
        if eventName not in self.EVENTS_MAP or not self._enabled:
            return None

        eventObject:Event = self.EVENTS_MAP[eventName]
        eventObject.event_handler(kwargs, None)

    def run(self) -> None:
        while self._enabled:
            for event_name in self.EVENTS_MAP:
                event = self.EVENTS_MAP[event_name]
                if event.event_invoker is None:
                    continue
                try:
                    self.logger.debug(f"Calling event - {event_name}")
                    start = time.time()
                    callEvent = event.event_invoker(event.event_object)
                    timeDiff = time.time() - start
                    if timeDiff > self.expectedInvokerTime:
                        self.logger.warning(f"Time exceed for event invoker: {timeDiff} secs")
                    if callEvent is not None and 'trigger' in callEvent and callEvent['trigger']:
                        responseObject = event.event_handler(callEvent, event.event_object)
                        if responseObject is not None:
                            event.event_object = responseObject
                            self.EVENTS_MAP[event_name] = event

                except Exception as e:
                    self.logger.error(f"Exception occured while invoking event: {event_name} Exception: {e}")
            time.sleep(self.sleepwait)