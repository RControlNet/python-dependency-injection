import os
from threading import Thread

import pika
from pika import BlockingConnection
import logging

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

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

    def setTopic(self, topic, group="", channelName=None):
        SubscriberChannel.setTopic(self, topic)
        self.channel.queue_declare(queue=topic  + group)
        self.channel.queue_bind(exchange=topic, queue=topic + group, routing_key="#")



class RabbitMQBinder:
    @staticmethod
    def name():
        return "rabbitmq"

    def __init__(self):
        self.logger = logging.getLogger('.'.join([self.__class__.__module__, self.__class__.__name__]))
        brokerUrl = getContextEnvironment("rcn.binders.message.rabbitmq.brokerUrl", defaultValue=None)
        brokerPort = getContextEnvironment("rcn.binders.message.rabbitmq.brokerPort", defaultValue=None)

        brokerUrl = getContextEnvironment("rcn.binders.message.brokerUrl", required=True, defaultValue=brokerUrl)
        brokerPort = getContextEnvironment("rcn.binders.message.brokerPort", required=True, castFunc=int,
                                           defaultValue=brokerPort)

        user = getContextEnvironment("rcn.binders.message.rabbitmq.user")
        userSecret = getContextEnvironment("rcn.binders.message.rabbitmq.userSecret")

        contextEnvs = getContextEnvironments()
        credentials = pika.PlainCredentials(user,  userSecret)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=brokerUrl, port=brokerPort, credentials=credentials, heartbeat=60))
        self.rabbotmqProducerChannelBindings = filter(lambda key: key.startswith('rcn.binders.message.rabbitmq.producer'),
                                                 contextEnvs)
        self.mqttConsumerChannelBindings = filter(
            lambda key: key.startswith('rcn.binders.message.rabbitmq.consumer') and key.endswith("destination"),
            contextEnvs)
        self.CHANNELS_TO_TOPIC_MAP = dict()
        self.channel = self.connection.channel()

        self.channelThread = Thread(target=self.channel.start_consuming)
        self.producers = {}
        self.consumers = {}

    def stopConsumers(self):
        self.channel.stop_consuming()

    def info(self):
        producers = []
        consumers = []
        for channel, producerBinding in self.producers.items():
            producers.append(dict(
                channel=channel,
                topic=producerBinding.topic
            ))

        for channel, consumerBinding in self.consumers.items():
            consumers.append(dict(
                channel = channel
            ))
        return dict(
            producers = producers
        )
    def health(self):
        return self.channel.is_open and self.connection.is_open

    def bindSubscribers(self, CHANNELS_TO_FUNC_MAP):
        subscriptionTopics = list()
        topicConsumers = dict()
        binders = dict()

        def consumerMessage(ch: BlockingChannel, method: Basic.Deliver, properties, body):
            topicConsumers[method.exchange](body)

        for propertyKey in self.mqttConsumerChannelBindings:
            channelName = extractChannelNameFromPropertyKey(propertyKey)
            print(channelName)
            binderPath = f"rcn.binders.message.rabbitmq.consumer.{channelName}"
            consumerGroup = getContextEnvironment(f"{binderPath}.group")

            if channelName not in CHANNELS_TO_FUNC_MAP:
                self.logger.error(f"Channel not found: {channelName}")
                continue
            consumerBinding = RabbitMQSubscriberChannel(self.channel)
            callbackDetails = CHANNELS_TO_FUNC_MAP[channelName]
            callback = callbackDetails['func']
            consumerBinding.setOnConsumeCallback(callback)
            topicName = getContextEnvironment(propertyKey, required=True)
            routing_key = getContextEnvironment(f"{binderPath}.routing_key", defaultValue=topicName)
            subscriptionTopics.append(topicName)

            consumerBinding.setTopic(topicName, group=consumerGroup)
            if topicName in topicConsumers:
                raise KeyError(f"Duplicate topic found {topicName} with {topicConsumers[topicName]}")

            topicConsumers[topicName] = consumerBinding
            binders[channelName] = consumerBinding

            queue = f"{topicName}.{consumerGroup}"

            self.channel.queue_bind(queue=queue, exchange=topicName, routing_key=routing_key)
            self.channel.basic_consume(queue=queue, auto_ack=True, on_message_callback=consumerMessage)

        self.consumers = binders
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
        self.producers=binders
        return binders