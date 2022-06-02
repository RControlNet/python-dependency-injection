import unittest

from cndi.annotations import Component, Autowired
from cndi.binders.message import DefaultMessageBinder, MessageChannel, Output, SubscriberChannel, Input
from cndi.binders.message.mqtt import MqttProducerBinding
from cndi.env import VARS, loadEnvFromFile
from cndi.initializers import AppInitilizer


@Component
class SinkTest:
    outputChannel1Binding: MessageChannel
    @Output("default-channel-output")
    def setOutputForDefaultChannel(self, messageBinder: MqttProducerBinding):
        self.outputChannel1Binding = messageBinder


@Input("default-channel-input")
def setInputForDefaultChannel(message):
    print(message)

class DefaultMessageBinderTest(unittest.TestCase):
    def setUp(self) -> None:
        VARS.clear()
        loadEnvFromFile("tests/resources/binder_tests.yml")

    def testDefaultMessageBinder(self):
        defaultMessageBinder = DefaultMessageBinder()

    def testWithAppInitializer(self):
        @Autowired()
        def setSink(sink: SinkTest):
            sink.outputChannel1Binding.send("Hello")

        appInitializer = AppInitilizer()
        appInitializer.componentScan("cndi.binders")
        appInitializer.run()