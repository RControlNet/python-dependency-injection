import threading
import time
import logging

from cndi.annotations import Component, getBeanObject, ConditionalRendering
from cndi.annotations.threads import ContextThreads
from cndi.consts import RCN_EVENTS_ENABLE, RCN_EVENTS_WAITTIME, RCN_EVENTS_INVOKER_SLEEP_TIME
from cndi.env import getContextEnvironment

class Event(object):
    """
    Represents an event with its name, handler, object, and invoker.

    Attributes:
        event_name: The name of the event.
        event_handler: The function to be called when the event is triggered.
        event_object: The object that the event pertains to.
        event_invoker: The object that triggered the event.
    """
    def __init__(self, event_name=None, event_handler=None, event_object=None, event_invoker=None):
        self.event_name = event_name
        self.event_handler = event_handler
        self.event_invoker = event_invoker
        self.event_object = event_object

@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_EVENTS_ENABLE, defaultValue=False, castFunc=bool))
class EventHandler(threading.Thread):
    """
    Handles events in a separate thread.

    Attributes:
        EVENTS_MAP: A dictionary mapping event names to their handlers.
        sleepwait: The time to wait between checking for new events.
        expectedInvokerTime: The expected time for an event invoker to complete.
        _enabled: Whether the event handler is enabled.

    Methods:
        postConstruct: Starts the event handler thread if it is enabled.
        registerEvent: Registers a new event.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.EVENTS_MAP = dict()
        self._enabled = getContextEnvironment(RCN_EVENTS_ENABLE, defaultValue=False, castFunc=bool)
        self.sleepwait = getContextEnvironment(RCN_EVENTS_WAITTIME, defaultValue=2.0, castFunc=float)
        self.expectedInvokerTime = getContextEnvironment(RCN_EVENTS_INVOKER_SLEEP_TIME, defaultValue=0.003, castFunc=float)
        self.logger.debug(f"Expected Invoker Time set to {self.expectedInvokerTime} seconds")
        self.logger.debug(f"Sleep time set to {self.sleepwait} seconds")

    def postConstruct(self, contextThread: ContextThreads):
        """
        Starts the event handler thread if it is enabled.
        """
        contextThread.add_thread(self)
        self.start()

    def registerEvent(self, event: Event):
        """
        Registers a new event.

        Args:
            event: The event to register.
        """
        self.EVENTS_MAP[event.event_name] = event

    def triggerEventExplicit(self, eventName, **kwargs):
        """
        Triggers an event explicitly by its name.

        Args:
            eventName: The name of the event to trigger.
            **kwargs: Additional keyword arguments to pass to the event handler.

        Returns:
            None if the event name is not in the EVENTS_MAP or the event handler is not enabled.
        """
        if eventName not in self.EVENTS_MAP or not self._enabled:
            return None

        eventObject:Event = self.EVENTS_MAP[eventName]
        eventObject.event_handler(kwargs, None)

    def run(self) -> None:
        """
        Continuously checks for and handles events while the event handler is enabled.

        Returns:
            None
        """
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