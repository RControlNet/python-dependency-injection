from cndi.annotations import Autowired, Component
from cndi.annotations.events import OnEvent, EventExecutor
from cndi.initializers import AppInitializer

@OnEvent("on_load")
def on_load_1():
    print("Called Func 1")

@OnEvent("on_load")
def on_load_2():
    print("Called Func 2")


@Autowired()
def setEventExecutor(event_executor: EventExecutor):
    event_executor.execute("on_load")

if __name__ == '__main__':
    app_initializer = AppInitializer()
    app_initializer.run()