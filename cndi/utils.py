import os
import importlib
from importlib._bootstrap_external import _NamespacePath


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
            print("Skipping ImportModule:", m)
            continue
        print("Importing:", m)
        moduleInstance = importlib.import_module(m)
        if callback is not None:
            callback(moduleInstance)