from functools import wraps

from cndi.annotations import getBeanObject
from cndi.env import getContextEnvironment, getContextEnvironments
import re
import logging

logger = logging.getLogger(__name__)


CHANNELS_TO_TOPIC_MAP = dict()
CHANNELS_TO_FUNC_MAP = dict()

class SubscriberChannel:
    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)
    def setTopic(self, topic):
        self.topic = topic
    def setOnConsumeCallback(self, callback):
        self.callback = callback

class MessageChannel:
    def setTopic(self, topic):
        self.topic = topic

    def send(self, message) -> None:
        pass

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

class DefaultMessageBinder:
    def __init__(self):
        self.logger = logging.getLogger('.'.join([self.__class__.__module__, self.__class__.__name__]))

        defaultMessageBinder = getContextEnvironment("rcn.binders.message.default")
        if defaultMessageBinder is None:
            raise AttributeError(f"Message binder not found")

        self.defaultMessageBinder = defaultMessageBinder
        self.binders = dict()
        self.topicConsumers = dict()
        self.initializeBinders()

    def extractChannelNameFromPropertyKey(self, key):
        matches = re.match("rcn.binders.message.(?P<defaultBinder>[a-z]+).(?P<binderType>(\w)+).(?P<channelName>[a-z0-9\-]+).[destination|property]", key.lower())
        if matches is not None:
            return matches.groupdict()['channelName']
        return None

    def performInjection(self):
        for channelName, methodWrapper in CHANNELS_TO_FUNC_MAP.items():
            if channelName not in self.binders:
                logger.error(f"No binding found for channel - {channelName}")
                continue
            #
            if methodWrapper['is_sink']:
                binder = self.binders[channelName]
                method = methodWrapper['func']
                methodsClassFullname = f"{method.__module__}.{method.__qualname__.split('.')[0]}"
                classBean = getBeanObject(methodsClassFullname)
                method(classBean, binder)

    def initializeBinders(self):
        if self.defaultMessageBinder.strip().lower() == "mqtt":
            from cndi.binders.message.mqtt import MqttProducerBinding
            from paho.mqtt.client import Client, MQTTMessage

            brokerUrl = getContextEnvironment("rcn.binders.message.brokerUrl", required=True)
            brokerPort = getContextEnvironment("rcn.binders.message.brokerPort", required=True, castFunc=int)

            contextEnvs = getContextEnvironments()
            mqttClient = Client()

            mqttProducerChannelBindings = filter(lambda key: key.startswith('rcn.binders.message.mqtt.producer'), contextEnvs)
            for propertyKey in mqttProducerChannelBindings:
                channelName = self.extractChannelNameFromPropertyKey(propertyKey)
                producerBinding = MqttProducerBinding(mqttClient)
                topicName = getContextEnvironment(propertyKey, required=True)

                producerBinding.setTopic(topicName)
                CHANNELS_TO_TOPIC_MAP[channelName] = topicName
                self.binders[channelName] = producerBinding

            mqttConsumerChannelBindings = filter(lambda key: key.startswith('rcn.binders.message.mqtt.consumer') and key.endswith("destination"), contextEnvs)
            subscriptionTopics = list()

            for propertyKey in mqttConsumerChannelBindings:
                channelName = self.extractChannelNameFromPropertyKey(propertyKey)
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
            mqttClient.loop_start()