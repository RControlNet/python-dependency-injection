from functools import wraps


class EventsTypes:
    ON_ENV_LOAD="on_env_load"

REGISTERED_EVENTS = list()

class Event(object):
    def __init__(self, eventType, eventCallback):
        self.eventType = eventType
        self.eventCallback = eventCallback



def OnEvent(eventType):
    def inner_function(func):
        annotations = func.__annotations__

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        REGISTERED_EVENTS.append(Event(eventType=eventType, eventCallback=wrapper))

        return wrapper
    return inner_function

