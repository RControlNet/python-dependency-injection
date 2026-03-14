import pytest
import unittest

from cndi.annotations import Component, Bean, Autowired
from cndi.env import VARS
from cndi.tests import test_with_context
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

    @test_with_context
    def testComponents(self, firstComponent: FirstComponent, secondComponent: SecondTestClass, testBean: TestBean):
        self.assertTrue(firstComponent.triggered)
        self.assertIsNotNone(testBean)
        self.assertIsNotNone(secondComponent.firstComponent)