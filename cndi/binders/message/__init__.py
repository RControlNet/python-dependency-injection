from functools import wraps

from cndi.annotations import getBeanObject, Component, ConditionalRendering
from cndi.binders.consts import RCN_MESSAGE_BINDERS
from cndi.binders.message.utils import extractChannelNameFromPropertyKey, SubscriberChannel
from cndi.env import getContextEnvironment, getContextEnvironments
import logging

logger = logging.getLogger(__name__)


CHANNELS_TO_TOPIC_MAP = dict()
CHANNELS_TO_FUNC_MAP = dict()


class Message:
    def __init__(self, message):
        self.message = message
        self.key = None

    def setMessage(self, message):
        self.message = message
        return self

    def setKey(self, key):
        self.key = key
        return self


def Input(channelName):
    def inner_function(func):
        CHANNELS_TO_FUNC_MAP[channelName] = dict(func=func, annotations=func.__annotations__, is_sink=False)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return inner_function

def Output(channelName):
    def inner_function(func):
        CHANNELS_TO_FUNC_MAP[channelName] = dict(func=func, annotations=func.__annotations__, is_sink=True)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return inner_function

def _conditionalRenderDefaultMessageBinder(wrapper):
    defaultMessageBinder = getContextEnvironment("rcn.binders.message.enable",  defaultValue=False, castFunc=bool)
    return defaultMessageBinder

@Component
@ConditionalRendering(callback=_conditionalRenderDefaultMessageBinder)
class DefaultMessageBinder:
    def __init__(self):
        self.logger = logging.getLogger('.'.join([self.__class__.__module__, self.__class__.__name__]))

        self.binders = dict()
        self.topicConsumers = dict()
        self.callbacks = list()
        self.defaultMessageBinder = getContextEnvironment("rcn.binders.message.default")
        self.channelBinders = self.initializeBinders()

    def start(self):
        for callback in self.callbacks:
            callback()

    def performInjection(self):
        for channelName, methodWrapper in CHANNELS_TO_FUNC_MAP.items():
            if channelName not in self.binders:
                self.logger.error(f"No binding found for channel - {channelName}")
                continue

            if methodWrapper['is_sink']:
                binder = self.binders[channelName]
                method = methodWrapper['func']
                methodsClassFullname = f"{method.__module__}.{method.__qualname__.split('.')[0]}"
                classBean = getBeanObject(methodsClassFullname)
                method(classBean, binder)

    def initializeBinders(self):
        contextEnvs = getContextEnvironments()
        channelBinders = dict()
        if self.defaultMessageBinder.strip().lower() == "rabbitmq":
            from cndi.binders.message.rabbitmq import RabbitMQProducerBinding, RabbitMQBinder

            rabbitMqBinder = RabbitMQBinder()

            self.binders.update(rabbitMqBinder.bindProducers())
            self.binders.update(rabbitMqBinder.bindSubscribers(CHANNELS_TO_FUNC_MAP=CHANNELS_TO_FUNC_MAP))
            self.callbacks.append(rabbitMqBinder.channelThread.start)

            channelBinders[rabbitMqBinder.name()] = rabbitMqBinder

        elif self.defaultMessageBinder.strip().lower() == "mqtt":
            from cndi.binders.message.mqtt import MqttProducerBinding
            from paho.mqtt.client import Client, MQTTMessage

            brokerUrl = getContextEnvironment(f"{RCN_MESSAGE_BINDERS}.mqtt.brokerUrl", defaultValue=None)
            brokerPort = getContextEnvironment(f"{RCN_MESSAGE_BINDERS}.mqtt.brokerPort", defaultValue=None)

            brokerUrl = getContextEnvironment(f"{RCN_MESSAGE_BINDERS}.brokerUrl", required=True, defaultValue=brokerUrl)
            brokerPort = getContextEnvironment(f"{RCN_MESSAGE_BINDERS}.brokerPort", required=True, castFunc=int, defaultValue=brokerPort)

            mqttClient = Client()

            mqttProducerChannelBindings = filter(lambda key: key.startswith('rcn.binders.message.mqtt.producer'), contextEnvs)
            for propertyKey in mqttProducerChannelBindings:
                channelName = extractChannelNameFromPropertyKey(propertyKey)
                producerBinding = MqttProducerBinding(mqttClient)
                topicName = getContextEnvironment(propertyKey, required=True)

                producerBinding.setTopic(topicName)
                CHANNELS_TO_TOPIC_MAP[channelName] = topicName
                self.binders[channelName] = producerBinding

            mqttConsumerChannelBindings = filter(lambda key: key.startswith('rcn.binders.message.mqtt.consumer') and key.endswith("destination"), contextEnvs)
            subscriptionTopics = list()

            for propertyKey in mqttConsumerChannelBindings:
                channelName = extractChannelNameFromPropertyKey(propertyKey)
                if channelName not in CHANNELS_TO_FUNC_MAP:
                    self.logger.error(f"Channel not found: {channelName}")
                    continue
                consumerBinding = SubscriberChannel()
                callbackDetails = CHANNELS_TO_FUNC_MAP[channelName]
                callback = callbackDetails['func']
                consumerBinding.setOnConsumeCallback(callback)
                topicName = getContextEnvironment(propertyKey, required=True)
                consumerBinding.setTopic(topicName)
                subscriptionTopics.append(topicName)
                if topicName in self.topicConsumers:
                    raise KeyError(f"Duplicate topic found {topicName} with {self.topicConsumers[topicName]}")

                self.topicConsumers[topicName] = consumerBinding
                self.binders[channelName] = consumerBinding

            def on_connect(client: Client, userdata, flags, rc):
                self.logger.info("Connected with result code " + str(rc))
                for topic in subscriptionTopics:
                    client.subscribe(topic)

            def on_message(client, userdata, msg: MQTTMessage):
                self.topicConsumers[msg.topic](msg)

            mqttClient.on_connect = on_connect
            mqttClient.on_message = on_message

            mqttClient.connect(brokerUrl, brokerPort)
            self.callbacks.append(mqttClient.loop_start)

        return channelBinders