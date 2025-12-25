from cndi.annotations import Component, ConditionalRendering
from cndi.consts import RCN_AUTO_CONFIGURE_SECRETS_ENABLE
from cndi.env import getContextEnvironment


@Component
@ConditionalRendering(callback=lambda x: getContextEnvironment(RCN_AUTO_CONFIGURE_SECRETS_ENABLE, defaultValue=False, castFunc=bool))
class AutoConfigurationProviders:
    _PROVIDERS = dict()
    def __init__(self):
        pass