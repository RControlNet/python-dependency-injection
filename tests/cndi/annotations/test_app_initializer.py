import unittest
from cndi.annotations import Bean
from cndi.tests import test_with_context
from test_module.TestBean import TestBean

@Bean()
def getTestBean() -> TestBean:
    return TestBean("Hello")

class AppInitializerTest(unittest.TestCase):
    @test_with_context
    def testComponentScanAndDI(self, testBean: TestBean):
        self.assertIsNotNone(testBean)
        self.assertEqual(testBean.name, "Hello")
