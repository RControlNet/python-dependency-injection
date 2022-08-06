import re

class SubscriberChannel:
    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)
    def setTopic(self, topic, channelName=None):
        self.topic = topic
    def setOnConsumeCallback(self, callback):
        self.callback = callback

class MessageChannel:
    def setTopic(self, topic):
        self.topic = topic
    def close(self):
        pass
    def send(self, message) -> None:
        pass


def extractChannelNameFromPropertyKey(key):
    matches = re.match(
        "rcn.binders.message.(?P<defaultBinder>[a-z]+).(?P<binderType>(\w)+).(?P<channelName>[a-z0-9\-\_]+).[destination|property]",
        key.lower())
    if matches is not None:
        return matches.groupdict()['channelName']
    return None