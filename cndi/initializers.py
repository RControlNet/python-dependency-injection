import copy
import importlib
import os

from cndi.binders.message import DefaultMessageBinder
import logging

from cndi.annotations import beanStore, workOrder, beans, components, componentStore, autowires, getBeanObject, getBean
from cndi.env import loadEnvFromFile, getContextEnvironment
from cndi.utils import importSubModules

logger = logging.getLogger(__name__)

class AppInitilizer:
    def __init__(self):
        self.componentsPath = list()
        applicationYml = "resources/application.yml"
        if os.path.exists(applicationYml):
            logger.info(f"External Configuration found: {applicationYml}")
            loadEnvFromFile(applicationYml)


    def componentScan(self, module):
        importModule = importlib.import_module(module)
        self.componentsPath.append(importModule)


    def run(self):
        for module in self.componentsPath:
            importSubModules(module)

        workOrderBeans = workOrder(beans)

        for bean in workOrderBeans:
            logger.info(f"Registering Bean {bean['fullname']}")
            kwargs = dict()
            for key, className in bean['kwargs'].items():
                tempBean = beanStore[className]
                kwargs[key] = copy.deepcopy(tempBean['object']) if tempBean['newInstance'] else tempBean['object']

            bean['objectInstance'] = bean['object'](**kwargs)
            beanStore[bean['name']] = bean

        for component in components:
            componentStore[component.fullname] = component
            kwargs = constructKeyWordArguments(component.annotations)
            objectInstance = component.func(**kwargs)
            if 'postConstruct' in dir(objectInstance):
                postConstructKArgs = constructKeyWordArguments(objectInstance.postConstruct.__annotations__)
                objectInstance.postConstruct(**postConstructKArgs)

            beanStore[component.fullname] = dict(objectInstance=objectInstance,
                                                 name=component.fullname,
                                                 object=objectInstance, index=0, newInstance=False,
                                                 fullname=component.func.__name__, kwargs=kwargs)

        messageBinderEnabled = getContextEnvironment("rcn.binders.message.enable", defaultValue=False, castFunc=bool)
        defaultMessageBinder = None

        if messageBinderEnabled:
            defaultMessageBinder = DefaultMessageBinder()
            defaultMessageBinder.performInjection()

        for autowire in autowires:
            autowire.dependencyInject()

        if defaultMessageBinder is not None:
            defaultMessageBinder.start()

def constructKeyWordArguments(annotations):
    kwargs = dict()
    for key, classObject in annotations.items():
        tempBean = beanStore[f"{classObject.__module__}.{classObject.__name__}"]
        kwargs[key] = copy.deepcopy(tempBean['object']) if tempBean['newInstance'] else tempBean['object']
    return kwargs
