from threading import Thread

import pika
from pika import BlockingConnection
import logging

from pika.adapters.blocking_connection import BlockingChannel

from cndi.binders.message import Message, SubscriberChannel
from cndi.binders.message.utils import extractChannelNameFromPropertyKey, MessageChannel
from cndi.env import getContextEnvironment, getContextEnvironments


class RabbitMQProducerBinding(MessageChannel):
    def __init__(self, connection: BlockingConnection):
        self.channel = connection.channel()
        self.topic = None

    def setTopic(self, topic):
        MessageChannel.setTopic(self, topic)
        self.channel.queue_declare(queue=self.topic)
        self.channel.exchange_declare(exchange=self.topic)
        self.channel.queue_bind(exchange=self.topic, queue=self.topic)

    def send(self, message: Message) -> None:
        self.channel.basic_publish(
            exchange=self.topic,
            routing_key=self.topic,
            body=message.message
        )

    def close(self):
        self.channel.close()

class RabbitMQSubscriberChannel(SubscriberChannel):
    def __init__(self, channel: BlockingChannel):
        SubscriberChannel.__init__(self)
        self.channel = channel

    def setTopic(self, topic, channelName=None):
        SubscriberChannel.setTopic(self, topic)
        self.channel.queue_declare(queue=topic)



class RabbitMQBinder():
    def __init__(self):
        self.logger = logging.getLogger('.'.join([self.__class__.__module__, self.__class__.__name__]))
        brokerUrl = getContextEnvironment("rcn.binders.message.rabbitmq.brokerUrl", defaultValue=None)
        brokerPort = getContextEnvironment("rcn.binders.message.rabbitmq.brokerPort", defaultValue=None)

        brokerUrl = getContextEnvironment("rcn.binders.message.brokerUrl", required=True, defaultValue=brokerUrl)
        brokerPort = getContextEnvironment("rcn.binders.message.brokerPort", required=True, castFunc=int,
                                           defaultValue=brokerPort)

        contextEnvs = getContextEnvironments()

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=brokerUrl, port=brokerPort))
        self.rabbotmqProducerChannelBindings = filter(lambda key: key.startswith('rcn.binders.message.rabbitmq.producer'),
                                                 contextEnvs)
        self.mqttConsumerChannelBindings = filter(
            lambda key: key.startswith('rcn.binders.message.rabbitmq.consumer') and key.endswith("destination"),
            contextEnvs)
        self.CHANNELS_TO_TOPIC_MAP = dict()
        self.channel = self.connection.channel()

        self.channelThread = Thread(target=self.channel.start_consuming)

    def stopConsumers(self):
        self.channel.stop_consuming()

    def bindSubscribers(self, CHANNELS_TO_FUNC_MAP):
        subscriptionTopics = list()
        topicConsumers = dict()
        binders = dict()

        for propertyKey in self.mqttConsumerChannelBindings:
            channelName = extractChannelNameFromPropertyKey(propertyKey)
            if channelName not in CHANNELS_TO_FUNC_MAP:
                self.logger.error(f"Channel not found: {channelName}")
                continue
            consumerBinding = RabbitMQSubscriberChannel(self.channel)
            callbackDetails = CHANNELS_TO_FUNC_MAP[channelName]
            callback = callbackDetails['func']
            consumerBinding.setOnConsumeCallback(callback)
            topicName = getContextEnvironment(propertyKey, required=True)
            subscriptionTopics.append(topicName)

            consumerBinding.setTopic(topicName)
            if topicName in topicConsumers:
                raise KeyError(f"Duplicate topic found {topicName} with {topicConsumers[topicName]}")

            topicConsumers[topicName] = consumerBinding
            binders[channelName] = consumerBinding

            self.channel.basic_consume(queue=topicName, auto_ack=True, on_message_callback=
                        lambda ch, method, properties, body : consumerBinding(body))


        self.channelThread.start()

        return binders

    def bindProducers(self):
        binders = dict()
        for propertyKey in self.rabbotmqProducerChannelBindings:
            channelName = extractChannelNameFromPropertyKey(propertyKey)
            producerBinding = RabbitMQProducerBinding(connection=self.connection)

            topicName = getContextEnvironment(propertyKey, required=True)
            self.logger.info("Topic Name: "  + topicName)
            producerBinding.setTopic(topicName)
            self.CHANNELS_TO_TOPIC_MAP[channelName] = topicName
            binders[channelName] = producerBinding

        return binders