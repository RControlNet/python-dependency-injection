import unittest
import os
from cndi.env import loadEnvFromFile, getContextEnvironment


class LoadEnv(unittest.TestCase):
    def testloadEnvFromFile(self):
        RCN_ENVS_CONFIG = 'RCN_ENVS_CONFIG'
        os.environ[f"{RCN_ENVS_CONFIG}.active.profile"] = "test"

        loadEnvFromFile("resources/test.yml")
        self.assertEqual("test", getContextEnvironment("rcn.profile"))