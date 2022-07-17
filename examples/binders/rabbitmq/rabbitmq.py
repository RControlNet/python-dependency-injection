from time import sleep

from cndi.annotations import Component, Autowired
from cndi.binders.message import Input, Output, Message
from cndi.binders.message.utils import MessageChannel
from cndi.env import loadEnvFromFile
from cndi.initializers import AppInitilizer
from cndi.resources import ResourceFinder

@Component
class Source:
    @Output("producer-channel")
    def setOutput(self, outputChannel: MessageChannel):
        self.outputChannel = outputChannel

@Input("consumer-channel")
def consumeData(data):
    print(data)

if __name__ == '__main__':
    resourceFinder = ResourceFinder()
    ymlPath = resourceFinder.findResource("rabbitmqProperties.yml")

    loadEnvFromFile(ymlPath)

    @Autowired()
    def setOutputs(source: Source):
        source.outputChannel.send(Message("Hello")
                                  .setKey("key1"))

    app_initializer = AppInitilizer()
    app_initializer.run()

    while True:
        sleep(10)