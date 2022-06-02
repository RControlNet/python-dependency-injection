from paho.mqtt.client import Client

from cndi.binders.message import MessageChannel

class MqttProducerBinding(MessageChannel):
    def __init__(self, mqttClient: Client):
        self.mqttClient = mqttClient
        self.topic = None

    def send(self, message) -> None:
        self.mqttClient.publish(self.topic, message)