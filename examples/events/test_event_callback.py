from cndi.annotations import Autowired, Component
from cndi.annotations.events import OnEvent, EventExecutor, StandaloneEventBroker
from cndi.consts import RCN_ENABLE_STANDALONE_MESSAGE_BROKER, RCN_ENABLE_CONTEXT_THREADS
from cndi.env import RCN_ENVS_CONFIG
from cndi.initializers import AppInitializer
import os

os.environ[RCN_ENVS_CONFIG + '.' + RCN_ENABLE_STANDALONE_MESSAGE_BROKER] = "True"
os.environ[RCN_ENVS_CONFIG + '.' + RCN_ENABLE_CONTEXT_THREADS] = "True"

@OnEvent("on_load")
async def on_load_1():
    print("Called Func 1")

@OnEvent("on_load")
def on_load_2():
    print("Called Func 2")

@OnEvent("on_load_3")
def on_load_3():
    print("Called Func 3")


@Autowired()
def setEventExecutor(event_executor: EventExecutor, messageBroker: StandaloneEventBroker):
    event_executor.execute("on_load")               # Execute using event executor
    messageBroker.push_event("on_load")             # Execute using Push Event

if __name__ == '__main__':
    app_initializer = AppInitializer()
    app_initializer.run()