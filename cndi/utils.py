import os
import importlib
from re import template
from uuid import uuid4

from importlib._bootstrap_external import _NamespacePath
import logging

from cndi.env import getContextEnvironment

logger = logging.getLogger("cndi.utils")

def injectEnvAsDict(dictObject, parent=""):
    for (key,value) in dictObject.items():
        if isinstance(value, dict):
            injectEnvAsDict(value, key + ".")
        elif isinstance(value, list) or isinstance(value, set) or isinstance(value, tuple):
             raise NotImplementedError("Value of type: %s object cannot be list, set or tuple" % (type(value)))
        else:
            injectEnvAsKeyValue(key, value)

def injectEnvAsKeyValue(key, value):
    if key not in os.environ:
        os.environ[key] = value

def dirModuleFilter(module, filt = lambda y: True):
    return filter(lambda x: not x.startswith('__') and filt(x), dir(module))

def walkDir(path):
    pythonFilesInComponent = list()
    for (root, dirs, files) in os.walk(path, topdown=path):
        pythonFilesInComponent.extend(map(lambda x: '.'.join([root[path.__len__():].replace('\\', '.'),x[:-3]]),filter(lambda x: x.endswith(".py"), files)))
    return pythonFilesInComponent

def walkChild(module):
    locations = module.__spec__.submodule_search_locations
    if isinstance(locations, _NamespacePath):
        l = module.__spec__.submodule_search_locations._path
    else:
        l = locations
    pythonComponents = list(map(lambda x: module.__name__ + x ,walkDir(l[0] if isinstance(l, list) else l)))
    return pythonComponents

def importSubModules(module, skipModules=[], callback=None):
    for m in walkChild(module):
        if len(list(filter(lambda x: m.startswith(x), skipModules))) > 0:
            logger.warning(f"Skipping ImportModule: {m}")
            continue
        logger.info(f"Importing: {m}")
        moduleInstance = importlib.import_module(m)
        if callback is not None:
            callback(moduleInstance)


class File:
    def __init__(self, path, tempFile=False):
        self.path = path
        self.tempFile = tempFile
    def resolveChildren(self, childName):
        childPath = os.path.join(self.path, childName)
        return File(childPath, tempFile=self.tempFile)
    def mkdir(self):
        os.path.makedirs(self.path)

def tempfile(content: str):
    filename = uuid4().__str__()
    tempDir = getContextEnvironment("rcn.tempdir", "./tmp")
    if (os.path.exists(tempDir)):
        os.makedirs(tempDir)

    tempFile = File(os.path.join(tempDir, filename), tempFile=True)
    with open(tempFile.path, "w") as file:
        file.write(content)

    return tempFile