from cndi.annotations import getBeanObject, Component, ConditionalRendering
from cndi.binders.message import DefaultMessageBinder
from cndi.env import getContextEnvironment
import logging

logger = logging.getLogger(__name__)
try:
    from cndi.binders.message.rabbitmq import RabbitMQBinder

    @Component
    @ConditionalRendering(callback= lambda x: getContextEnvironment("rcn.binders.message.enable", defaultValue=False, castFunc=bool) \
                                              and getContextEnvironment("rcn.binders.message.default", defaultValue=None) == RabbitMQBinder.name())
    class ChannelHealthChecker:
        def __init__(self, defaultMessageBinder: DefaultMessageBinder):
            self.channelBinders = defaultMessageBinder.channelBinders

        def check(self):
            targetResponse = []
            for channel, binder in self.channelBinders.items():
                targetResponse.append(dict(
                    channel= channel,
                    name = binder.name(),
                    status= "OK" if binder.health() else "UNHEALTHY",
                    info = binder.info()
                ))

            return targetResponse
except ModuleNotFoundError | ImportError:
    logger.warning("RabbitMQ Binder not loaded")
    ChannelHealthChecker = None

class BeanHealthChecker:
    def check(self, name):
        try:
            bean = getBeanObject(name)
            status = bean.status()
            return dict(
                status = status,
                code = 200
            )
        except AttributeError:
            return dict(
                status="Not Eligible",
                code = 201
            )
        except KeyError as error:
            return dict(
                error = "Bean Object not found",
                status = "ERROR",
                code = 404
            )