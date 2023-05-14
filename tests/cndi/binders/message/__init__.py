import unittest

from cndi.annotations import Component, Autowired
from cndi.binders.message import DefaultMessageBinder, Output, Input
from cndi.binders.message.mqtt import MqttProducerBinding
from cndi.binders.message.utils import MessageChannel
from cndi.env import VARS, loadEnvFromFile, RCN_ENVS_CONFIG
from cndi.initializers import AppInitializer


@Component
class SinkMQTTTest:
    outputChannel1Binding: MessageChannel
    @Output("default-channel-output")
    def setOutputForDefaultChannel(self, messageBinder: MqttProducerBinding):
        self.outputChannel1Binding = messageBinder


@Component
class SinkRabbitMQTTTest:
    outputChannel1Binding: MessageChannel
    @Output("default-channel-output-rabbit")
    def setOutputForDefaultChannel(self, messageBinder: MqttProducerBinding):
        self.outputChannel1Binding = messageBinder


@Input("default-channel-input")
def setInputForDefaultChannel(message):
    print(message)


@Input("default-channel-input-rabbit")
def setInputForDefaultChannel(message):
    print(message)

class MQTTDefaultMessageBinderTest(unittest.TestCase):
    def setUp(self) -> None:
        VARS.clear()
        VARS[f"{RCN_ENVS_CONFIG}.active.profile".lower()] = "mqtt-test"

        loadEnvFromFile("tests/resources/binder_tests.yml")

    def testDefaultMessageBinder(self):
        defaultMessageBinder = DefaultMessageBinder()

    def testWithAppInitializer(self):
        @Autowired()
        def setSink(sink: SinkMQTTTest):
            sink.outputChannel1Binding.send("Hello")

        appInitializer = AppInitializer()
        appInitializer.componentScan("cndi.binders")
        appInitializer.run()

#
# class RabbitMQDefaultMessageBinderTest(unittest.TestCase):
#     def setUp(self) -> None:
#         VARS.clear()
#         VARS[f"{RCN_ENVS_CONFIG}.active.profile".lower()] = "rabbitmq-test"
#
#         loadEnvFromFile("tests/resources/binder_tests.yml")
#
#     def testDefaultMessageBinder(self):
#         defaultMessageBinder = DefaultMessageBinder()
#
#     def testWithAppInitializer(self):
#         @Autowired()
#         def setSink(sink: SinkRabbitMQTTTest):
#             print(sink)
#             sink.outputChannel1Binding.send("Hello")
#
#         appInitializer = AppInitializer()
#         appInitializer.componentScan("cndi.binders")
#         appInitializer.run()