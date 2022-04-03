import unittest
import os
from cndi.env import loadEnvFromFile, getContextEnvironment


class LoadEnv(unittest.TestCase):
    def setUp(self) -> None:
        RCN_ENVS_CONFIG = 'RCN_ENVS_CONFIG'
        os.environ[f"{RCN_ENVS_CONFIG}.active.profile"] = "test"

    def testloadEnvFromFile(self):
        loadEnvFromFile("resources/test.yml")
        self.assertEqual("test", getContextEnvironment("rcn.profile"))

    def testloadEnvWithListDatatype(self):
        loadEnvFromFile("resources/test.yml")

        self.assertEqual(getContextEnvironment('mini.listdata.#1.name'), 'thereitis')
        self.assertEqual(getContextEnvironment('mini.listdata.#0.page.#0.default'), '2')
