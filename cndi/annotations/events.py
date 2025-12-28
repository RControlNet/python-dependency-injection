import logging
import threading
from functools import wraps
from multiprocessing import Queue
from typing import Dict
import asyncio
from cndi.annotations import Component, constructKeyWordArguments, ConditionalRendering
from cndi.annotations.threads import ContextThreads
from cndi.consts import RCN_ENABLE_STANDALONE_MESSAGE_BROKER, RCN_ENABLE_CONTEXT_THREADS
from cndi.env import getContextEnvironment

logger = logging.getLogger(__name__)


class BuiltInEventsTypes:
    ON_ENV_LOAD="on_env_load"

class Event(object):
    def __init__(self, eventType,
                 eventCallback, kwargs={}):
        self.eventType = eventType
        self.eventCallback = eventCallback
        self.kwargs = kwargs

REGISTERED_EVENTS: Dict[str, dict[str, Event]] = dict()
def register_event(event: Event, func_name: str):
    if event.eventType not in REGISTERED_EVENTS:
        REGISTERED_EVENTS[event.eventType] = dict()

    REGISTERED_EVENTS[event.eventType][func_name] = event

def OnEvent(event):
    def inner_function(func):
        annotations = func.__annotations__

        func_name = '.'.join([func.__module__, func.__qualname__])
        @wraps(func)
        def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return asyncio.run(func(*args, **kwargs))
            return func(*args, **kwargs)

        register_event(Event(eventType=event, eventCallback=wrapper, kwargs=annotations), func_name)

        return wrapper
    return inner_function

class EventNotFound(Exception):
    def __init__(self, *args):
        super().__init__( *args)

@Component
class EventExecutor:
    def execute(self, event: str, required=True, **override_kwargs):
        if event not in REGISTERED_EVENTS:
            if required:
                raise EventNotFound(f"{event} not found, please check the decorators")
            else:
                return None

        event_objs = REGISTERED_EVENTS.get(event)
        response = dict()
        for func_name, event_obj in event_objs.items():
            logger.debug(f"Event call started on {func_name}")

            kwargs = {
                **constructKeyWordArguments(event_obj.kwargs, required=False),
                **override_kwargs
            }
            kwargs = dict(map(lambda x: [x, kwargs[x]],set(event_obj.kwargs.keys()).intersection(kwargs.keys())))
            response[func_name] = event_obj.eventCallback(**kwargs)
            logger.debug(f"Event call completed on {func_name}")
        return response

_shared_queue = Queue()

@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_ENABLE_STANDALONE_MESSAGE_BROKER, defaultValue=False, castFunc=bool) and
                getContextEnvironment(RCN_ENABLE_CONTEXT_THREADS, defaultValue=False, castFunc=bool)
          )
class Consumer(threading.Thread):
    def __init__(self, eventExecutor: EventExecutor,
                 contextThread: ContextThreads):
        super().__init__()
        self.eventExecutor = eventExecutor
        self.start()
        contextThread.add_thread(self)

    def run(self):
        while self.is_alive():
            event_name = _shared_queue.get(block=True)
            self.eventExecutor.execute(event_name)


@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_ENABLE_STANDALONE_MESSAGE_BROKER, defaultValue=False, castFunc=bool))
class StandaloneEventBroker:
    def __init__(self, consumer: Consumer):
        self.data = dict()
        self.consumer = consumer

    def push_event(self, event_name):
        _shared_queue.put(event_name)