from cndi.autoconfiguration.configure import AutoConfigurationProviders
from cndi.consts import RCN_ENABLE_VAULT_PROVIDER
from cndi.env import RCN_ENVS_CONFIG, getContextEnvironment
from cndi.initializers import AppInitializer
import os

os.environ[RCN_ENVS_CONFIG+'.' + RCN_ENABLE_VAULT_PROVIDER] = "true"
os.environ[RCN_ENVS_CONFIG+'.' + "secrets.provider.vault.addr"] = ""
os.environ[RCN_ENVS_CONFIG+'.' + "secrets.provider.vault.token"] = ""
os.environ[RCN_ENVS_CONFIG+'.' + 'SECRET_VALUE'] = "vault://<mount path> <secret> <key>"

if __name__ == '__main__':
    app_initializer = AppInitializer()
    app_initializer.componentScan("cndi.secrets")
    app_initializer.run()
    print(AutoConfigurationProviders._PROVIDERS)
    print(getContextEnvironment('SECRET_VALUE'))