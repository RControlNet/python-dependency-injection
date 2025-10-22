from functools import wraps
from typing import Dict

from cndi.annotations import Component, constructKeyWordArguments
import logging

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

def OnEvent(event):
    def inner_function(func):
        annotations = func.__annotations__
        func_name = '.'.join([func.__module__, func.__qualname__])
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if event not in REGISTERED_EVENTS:
            REGISTERED_EVENTS[event] = dict()

        REGISTERED_EVENTS[event][func_name] = Event(eventType=event, eventCallback=wrapper, kwargs=annotations)

        return wrapper
    return inner_function

class EventNotFound(Exception):
    def __init__(self, *args):
        super().__init__( *args)

@Component
class EventExecutor:
    def __init__(self):
        pass

    def register(self, event: Event):
        REGISTERED_EVENTS[event.eventType] = event

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