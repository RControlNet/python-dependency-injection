import os

from cndi.annotations import Bean, ConditionalRendering
from cndi.autoconfiguration.configure import AutoConfigurationProviders
from cndi.consts import RCN_ENABLE_ENV_PROVIDER
from cndi.env import reload_envs, getContextEnvironments, RCN_ENVS_CONFIG, getContextEnvironment

ENV_PROVIDER_PREFIX = "env://"

class FromEnvProvider:
    def __init__(self):
        for key, value in getContextEnvironments().items():
            self.resolve(key, value)
        reload_envs()
        AutoConfigurationProviders._PROVIDERS[ENV_PROVIDER_PREFIX] = self

    def resolve(self, key, value):
        if value.startswith(ENV_PROVIDER_PREFIX):
            env_var_name = value[len(ENV_PROVIDER_PREFIX):]
            env_value = os.environ[env_var_name]
            if env_value is not None:
                os.environ[RCN_ENVS_CONFIG + '.' + key] = env_value
            else:
                raise ValueError(f"Environment variable '{env_var_name}' not found for key '{key}'")

@Bean()
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_ENABLE_ENV_PROVIDER, defaultValue=False, castFunc=bool))
def getEnvProvider() -> FromEnvProvider:
    return FromEnvProvider()