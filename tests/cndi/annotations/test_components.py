import unittest

from cndi.annotations import Component, Bean, Autowired
from cndi.env import VARS
from cndi.initializers import AppInitializer
from test_module.TestBean import TestBean


@Bean()
def getTestBean() -> TestBean:
    return TestBean("testBean")

@Component
class FirstComponent:
    def __init__(self):
        self.triggered = False
    def postConstruct(self):
        self.triggered = True

@Component
class SecondTestClass:
    def __init__(self, firstComponent: FirstComponent):
        self.firstComponent = firstComponent
        self.testBean = None

    def postConstruct(self, testBean: TestBean):
        self.testBean = testBean

class TestComponents(unittest.TestCase):
    def setUp(self) -> None:
        VARS.clear()
        self.store = dict()

    def testComponents(self):
        @Autowired()
        def setComponent(secondComponent: SecondTestClass, bean: TestBean):
            self.store['component'] = secondComponent
            self.store['bean'] = bean

        appInitializer = AppInitializer()
        appInitializer.run()

        self.assertTrue(self.store['component'].firstComponent.triggered)
        self.assertIsNotNone(self.store['component'].testBean)