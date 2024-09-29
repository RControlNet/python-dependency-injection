import copy
import importlib
import os

from cndi.binders.message import DefaultMessageBinder
import logging

from cndi.annotations import beanStore, workOrder, beans, components, componentStore, autowires, getBeanObject, getBean, \
    validateBean, queryOverideBeanStore, validatedBeans
from cndi.env import loadEnvFromFile, getContextEnvironment, reload_envs
from cndi.exception import BeanNotFoundException
from cndi.flask.flask_app import FlaskApplication
from cndi.http.management import ManagementServer
from cndi.utils import importSubModules
from cndi.version import VERSION

logger = logging.getLogger(__name__)

initializerComponents = [
    '.'.join([ManagementServer.__module__, ManagementServer.__name__]),
    '.'.join([FlaskApplication.__module__, FlaskApplication.__name__])
]

class AppInitializer:
    def __init__(self):
        """
        Responsible to initialise Dependency Injection for Application
        """
        logger.info(f"CNDI Version: v{VERSION}")
        try:
            from dotenv import load_dotenv
            load_dotenv("./.env")
            reload_envs()
        except ImportError as e:
            logger.error(e)
        self.componentsPath = list()
        applicationYml = "resources/application.yml"

        if os.path.exists(applicationYml):
            logger.info(f"External Configuration found: {applicationYml}")
            loadEnvFromFile(applicationYml)


    def componentScan(self, module):
        importModule = importlib.import_module(module)
        self.componentsPath.append(importModule)


    def run(self):
        """
        Performing Dependency Injection, on priority basis
        Steps Involved in DI
            1. Load Modules and Sub Modules for Bean/Component scanning
            2. Create list for the Available Beans and Components
            3. Resolve Dependency Tree for Beans and Components and Sort in reverse tree dependency
            4. For component classes run postConstruct method if available
            5. Read Configuration for binders and initialise binders for given type (i.e rabbitmq, mqtt)
            6. Perform Dependency Injection by calling setter methods
            7. Start Binder Configuration
        :return: None
        """

        for module in self.componentsPath:
            importSubModules(module)

        for bean in beans:
            validBean = validateBean(bean['fullname'])
            if not validBean:
                continue
            else:
                validatedBeans.append(bean)

        workOrderBeans = workOrder(validatedBeans)

        for bean in workOrderBeans:
            logger.info(f"Registering Bean {bean['fullname']}")
            kwargs = dict()
            for key, className in bean['kwargs'].items():
                tempBean = beanStore[className]
                kwargs[key] = copy.deepcopy(tempBean['object']) if tempBean['newInstance'] else tempBean['object']

            functionObject = bean['object']
            fullname = ".".join([functionObject.__module__, functionObject.__qualname__])
            validBean = validateBean(fullname)
            if validBean:
                bean['objectInstance'] = bean['object'](**kwargs)
                beanStore[bean['name']] = bean
            else:
                logger.debug(f"Ignoring Bean {fullname} due to bean not satisfy")

        for component in components:
            validBean = validateBean(component.fullname)
            if not validBean:
                logger.debug(f"Ignoring Component {component.fullname} due to bean not satisfy")
                continue

            componentStore[component.fullname] = component
            logger.info(f"Building Component: {component.fullname}")
            kwargs = constructKeyWordArguments(component.annotations)
            logger.info("Initializing")
            objectInstance = component.func(**kwargs)
            if 'postConstruct' in dir(objectInstance):
                postConstructKArgs = constructKeyWordArguments(objectInstance.postConstruct.__annotations__)
                objectInstance.postConstruct(**postConstructKArgs)

            override = queryOverideBeanStore(component.fullname)
            if override is not None:
                overrideType = override['overrideType']
                component.fullname = ".".join([overrideType.__module__, overrideType.__name__])

            beanStore[component.fullname] = dict(objectInstance=objectInstance,
                                                 name=component.fullname,
                                                 object=objectInstance, index=0, newInstance=False,
                                                 fullname=component.func.__name__, kwargs=kwargs)

        messageBinderEnabled = getContextEnvironment("rcn.binders.message.enable", defaultValue=False, castFunc=bool)
        defaultMessageBinder = None

        if messageBinderEnabled:
            defaultMessageBinder = getBeanObject(".".join([DefaultMessageBinder.__module__, DefaultMessageBinder.__name__]))
            defaultMessageBinder.performInjection()

        for autowire in autowires:
            autowire.dependencyInject()

        if defaultMessageBinder is not None:
            defaultMessageBinder.start()

        for componentName, componentClass in componentStore.items():
            if componentName in initializerComponents:
                objectInstance = getBeanObject(componentName)
                componentClass.func.run(objectInstance)


def constructKeyWordArguments(annotations):
    kwargs = dict()
    for key, classObject in annotations.items():
        beanName = f"{classObject.__module__}.{classObject.__name__}"
        if beanName in beanStore:
            tempBean = beanStore[beanName]
            kwargs[key] = copy.deepcopy(tempBean['object']) if tempBean['newInstance'] else tempBean['object']
        else:
            raise BeanNotFoundException(f"Following Bean failed to load in Context: "+beanName)

    return kwargs
