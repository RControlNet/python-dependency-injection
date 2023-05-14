import unittest

from cndi.annotations import Autowired
from cndi.initializers import AppInitializer
from test_module.TestBean import TestBean


class AppInitializerTest(unittest.TestCase):
    def testComponentScanAndDI(self):
        @Autowired()
        def setTestBean(bean: TestBean):
            global testBean
            print(bean)
            testBean = bean

        app = AppInitializer()
        app.componentScan("test_module")

        app.run()
        self.assertEqual(testBean.name, "Test 123")
        self.assertIsInstance(testBean, TestBean)