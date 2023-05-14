import os

from cndi.env import RCN_ACTIVE_PROFILE

os.environ[RCN_ACTIVE_PROFILE] = "default"

from cndi.annotations import Bean, Profile, Autowired, Component, ConditionalRendering, OverrideBeanType
from cndi.initializers import AppInitializer
from test_module.TestBean import TestBean

@Profile(profiles=['hello'])
@Bean()
def getTestBean() -> TestBean:
    return TestBean("Test 123")

@Bean()
@Profile(profiles=['default'])
def getTestBean1() -> TestBean:
    return TestBean("Test 453")

class tetClassA:
    pass

@Component
@Profile(profiles=['default'])
@ConditionalRendering()
@OverrideBeanType(tetClassA)
class testClass:
    pass

@Autowired()
def test(test: TestBean, testC: tetClassA):
    print(test.name, testC)

if __name__ == '__main__':
    app_initializer = AppInitializer()
    app_initializer.run()