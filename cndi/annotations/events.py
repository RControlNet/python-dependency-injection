import asyncio
import dataclasses
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps
from typing import Dict, Callable

from cndi.annotations import Component, constructKeyWordArguments, ConditionalRendering
from cndi.consts import RCN_EVENTS_ENABLE, RCN_EVENTS_NUM_THREADS
from cndi.env import getContextEnvironment

logger = logging.getLogger(__name__)

class BuiltInEventsTypes:
    ON_ENV_LOAD="on_env_load"
    ON_CONTEXT_LOAD="on_context_load"

@dataclasses.dataclass
class Event(object):
    def __init__(self, eventType,
                 eventCallback, kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.eventType = eventType
        self.eventCallback: Callable = eventCallback
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
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_EVENTS_ENABLE, defaultValue=False, castFunc=bool)
                            and getContextEnvironment(RCN_EVENTS_NUM_THREADS, defaultValue=1, castFunc=int) > 0)
class EventBus:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=getContextEnvironment(RCN_EVENTS_NUM_THREADS, defaultValue=1, castFunc=int))

    def publish(self, event_name: str, data=None) -> None:
        if data is None:
            data = {}
        if event_name in REGISTERED_EVENTS:
            for func_name, event  in REGISTERED_EVENTS[event_name].items():
                kwargs = {
                    **constructKeyWordArguments(event.kwargs, required=False),
                    **data
                }
                kwargs = dict(map(lambda x: [x, kwargs[x]], set(event.kwargs.keys()).intersection(kwargs.keys())))
                self._executor.submit(event.eventCallback, **kwargs)
        else:
            logger.warning(f"{event_name} event not found, please check the decorators")

    def subscribe(self, event_name: str, event: Event) -> None:
        if event_name not in REGISTERED_EVENTS:
            REGISTERED_EVENTS[event_name] = dict()
        REGISTERED_EVENTS[event_name][event.eventType] = event