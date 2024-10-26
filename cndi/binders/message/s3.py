import re
import time
from datetime import timedelta

import logging
from cndi.utils import File


logger = logging.getLogger(__name__)

class S3BaseChannel:
    def __init__(self, bucketName, func, localDir, pollDelay: timedelta,fileFilter=None,
                 deleteAfterPoll=False,**kwargs):
        self.bucketName = bucketName
        self.func = func
        self.pollDelay = pollDelay.total_seconds()
        self.localDir = File(localDir)
        self.deleteAfterPoll = deleteAfterPoll
        self.localDir.mkdir()
        self.fileFilter = fileFilter

    def pullObject(self, key: str):
        pass

    def process(self):
        pass

    def run(self):
        while True:
            self.process()
            time.sleep(self.pollDelay)

class FileFilter:
    def __init__(self, filter):
        self.filter = filter
        self.pattern = re.compile(self.filter)

    def matches(self, objectName):
        return self.pattern.match(objectName) is not None

class MinioS3Channel(S3BaseChannel):
    def __init__(self, url, bucketName, accessKey, accessSecret, func, localDir,
                 deleteAfterPoll=False, filter:FileFilter = None,
                 pollDelay:timedelta = timedelta(seconds=30), **kwargs):
        from minio import Minio
        S3BaseChannel.__init__(self, bucketName=bucketName,deleteAfterPoll=deleteAfterPoll,
                               pollDelay=pollDelay, func=func, localDir=localDir, **kwargs)

        self.client = Minio(
            url,
            access_key=accessKey,
            secret_key=accessSecret
        )
        self.filter = filter


    def pullObject(self, key: str):
        response = self.client.get_object(self.bucketName, key)
        localFile = self.localDir.resolveChildren(key, isFile=True)
        localFile.mkdir()
        with open(localFile.path, "wb") as stream:
            stream.write(response.read())

        return localFile

    def process(self):
        objects = list(map(lambda x: x.object_name, self.client.list_objects(self.bucketName, recursive=True)))
        objects = list(filter(lambda x: self.filter is None or self.filter.matches(x), objects))
        for object in objects:
            file = self.pullObject(object)
            self.func(file)
            if self.deleteAfterPoll:
                self.client.remove_object(self.bucketName, object)