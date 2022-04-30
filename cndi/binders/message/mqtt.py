from cndi.binders.message import MessageChannel

class MqttProducerBinding(MessageChannel):
    def send(self, message) -> None:
        print("Message: ", message)