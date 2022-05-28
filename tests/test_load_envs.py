import unittest

RCN_ENVS_CONFIG = 'RCN_ENVS_CONFIG'

from cndi.env import loadEnvFromFile, getContextEnvironment, VARS


class LoadEnvTest(unittest.TestCase):
    def setUp(self) -> None:
        VARS.clear()
        VARS[f"{RCN_ENVS_CONFIG}.active.profile".lower()] = "test"


    def testloadEnvFromFile(self):
        loadEnvFromFile("tests/resources/test.yml")
        self.assertEqual("test", getContextEnvironment("rcn.profile"))

    def testloadEnvWithListDatatype(self):
        loadEnvFromFile("tests/resources/test.yml")

        self.assertEqual(getContextEnvironment('mini.listdata.#1.name'), 'thereitis')
        self.assertEqual(getContextEnvironment('mini.listdata.#0.page.#0.default'), '2')
