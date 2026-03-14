from functools import wraps
from typing import Callable

from cndi.annotations import constructKeyWordArguments
from cndi.initializers import AppInitializer


def test_with_context(test_func: Callable):
    """Decorator to initialize Context before running a test."""

    @wraps(test_func)
    def wrapper(self, *args, **kwargs):
        # Initialize the singleton Context instance
        app = AppInitializer()
        app.run(freeze=False)

        constructed_kwargs = constructKeyWordArguments(test_func.__annotations__)
        # Run the test
        return test_func(self, *args, **constructed_kwargs,**kwargs)

    return wrapper