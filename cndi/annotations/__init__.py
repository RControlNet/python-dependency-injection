import os

from cndi.annotations.component import ComponentClass
import logging

from cndi.env import RCN_ACTIVE_PROFILE

logger = logging.getLogger("cndi.annotations")

validatedBeans = list()
beans = list()
autowires = list()
components = list()
beanStore = dict()
componentStore = dict()
profilesStores = dict()
conditionalRender = dict()
overrideStore = dict()

from functools import wraps
import importlib
import copy


def importModuleName(fullname):
    modules = fullname.split('.')
    module = importlib.import_module(modules[-1], package='.'.join(modules[:-1]))
    return module


def normaliseModuleAndClassName(name):
    nameList: list = name.split(".")
    if "__init__" in nameList:
        nameList.remove("__init__")
    return '.'.join(nameList)


def getBeanObject(objectType):
    bean = queryBeanStorage(objectType)
    objectInstance = bean['objectInstance']
    # if (objectInstance.__class__.__name__ == "function"):
    #     args[key] = objectInstance()
    # else:
    return copy.deepcopy(objectInstance) if bean['newInstance'] else objectInstance


def queryBeanStorage(fullname):
    objectType = normaliseModuleAndClassName(fullname)
    bean = beanStore[objectType]
    return bean


class AutowiredClass:
    def __init__(self, required, func, kwargs: dict()):
        self.fullname = '.'.join([func.__qualname__])
        self.className = normaliseModuleAndClassName('.'.join(func.__qualname__.split(".")[:-1]))
        self.func = func
        self.kwargs = kwargs
        self.required = required

    def dependencyInject(self):
        dependencies = self.calculateDependencies()
        dependencyNotFound = list()
        for dependency in dependencies:
            if dependency not in beanStore:
                dependencyNotFound.append(dependency)

        if len(dependencyNotFound) > 0:
            logger.warning(f"Skipping {self.fullname}")
            assert not self.required, "Could not initialize " + self.fullname + " with beans " + str(
                dependencyNotFound)

        kwargs = self.kwargs
        args = dict()
        for (key, value) in kwargs.items():
            fullName = normaliseModuleAndClassName('.'.join([value.__module__, value.__name__]))
            if fullName in beanStore:
                args[key] = getBeanObject(fullName)

        if self.className in beanStore:
            self.func(beanStore[self.className], **args)
        else:
            logger.info(f"{self.className} {self.fullname}")
            self.func(**args)

    def calculateDependencies(self):
        return list(
            map(lambda dependency: normaliseModuleAndClassName('.'.join([dependency.__module__, dependency.__name__])),
                self.kwargs.values()))


def OverrideBeanType(type: object):
    """
    OverrideBeanType is used to override the current annotated @Component class to be injected as some other object

    :param type: Class type to override while performing Dependency Injection
    :return: function wrapper
    """

    def inner_function(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        fullname = '.'.join([wrapper.__module__, wrapper.__name__])

        overrideStore[fullname] = {
            "func": wrapper,
            "overrideType": type
        }
        return wrapper

    return inner_function


def queryOverideBeanStore(fullname):
    if fullname in overrideStore:
        return overrideStore[fullname]
    else:
        return None


def Component(func: object):
    """
    When decorated with @Component, AppInitializer tries to automatically initialise the class this decorator is added to
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    moduleName = wrapper.__module__[:-9] if wrapper.__module__.endswith(".__init__") else wrapper.__module__
    componentFullName = '.'.join([moduleName, wrapper.__qualname__])
    logger.info(f"Registering Function name " + componentFullName)
    duplicateComponents = list(filter(lambda component: component.fullname == componentFullName, components))
    if duplicateComponents.__len__() > 0:
        logger.info(f"Duplicate Component found for: {duplicateComponents}")
    else:
        components.append(ComponentClass(**{
            'fullname': componentFullName,
            'func': wrapper,
            'annotations': wrapper.__init__.__annotations__ if "__annotations__" in dir(wrapper.__init__) else {}
        }))
    return wrapper


def validateBean(fullname):
    """
    Validates Beans before performing the dependency injection
    :param fullname: bean class full classpath name
    :return: Boolean type
    """

    profile = queryProfileData(fullname)
    condition = queryContitionalRenderingStore(fullname)
    if profile is None and condition is None:
        return True
    flag = True

    if profile is not None:
        profileNames = set(profile['profiles'])
        environmentProfiles = set(map(lambda x: x.strip(), os.environ[RCN_ACTIVE_PROFILE].split(",")))
        intersectionProfiles = profileNames.intersection(environmentProfiles)

        flag &= intersectionProfiles.__len__() >= 1

    if condition is not None:
        callback = condition['callback']
        callbackValue = callback(condition['func'])
        flag &= bool(callbackValue)

    if flag is False:
        logger.info("Validation Failed for Bean " + fullname)

    return flag


def Bean(newInstance=False):
    """

    :param newInstance:
    :return:
    """

    def inner_function(func):
        annotations = func.__annotations__
        returnType = annotations['return']
        del annotations['return']

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        fullname = '.'.join([returnType.__module__, returnType.__name__])
        annotations = dict(
            map(lambda key: (key, '.'.join([annotations[key].__module__, annotations[key].__qualname__])), annotations))

        if validateBean(fullname):
            beans.append({
                'name': fullname,
                'newInstance': newInstance,
                'object': wrapper,
                'fullname': wrapper.__qualname__,
                'kwargs': annotations,
                'index': len(beans)
            })

            return wrapper
        else:
            return None

    return inner_function


def ConditionalRendering(callback=lambda method: True, overrideFullName = None):
    """

    :param callback:
    :return:
    """

    def inner_function(func: object):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        fullname = ".".join([wrapper.__module__, wrapper.__qualname__]) if overrideFullName is None else overrideFullName

        conditionalRender[fullname] = {
            "func": wrapper,
            "callback": callback
        }

        return wrapper

    return inner_function


def queryContitionalRenderingStore(fullname):
    if fullname in conditionalRender:
        return conditionalRender[fullname]
    else:
        return None


def Profile(profiles=["default"]):
    """

    :param profiles:
    :return:
    """

    def inner_function(func: object):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        fullname = ".".join([wrapper.__module__, wrapper.__qualname__])
        profilesStores[fullname] = {
            "func": wrapper,
            "profiles": profiles
        }

        return wrapper

    return inner_function


def queryProfileData(fullname):
    if fullname in profilesStores:
        return profilesStores.get(fullname)
    else:
        return None


def Autowired(required=True):
    """
    
    :param required:
    :return:
    """

    def inner_function(func: object):
        annotations = func.__annotations__

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        autowires.append(AutowiredClass(required=required, **{
            'kwargs': annotations,
            'func': wrapper
        }))

        return wrapper

    return inner_function


def getBean(beans, name):
    return list(filter(lambda x: x['name'] == name, beans))[0]


def workOrder(beans):
    allBeanNames = list(map(lambda bean: bean['name'], beans))
    beanQueue = list(filter(lambda bean: len(bean['kwargs']) == 0, beans))
    beanIndexes = list(map(lambda bean: bean['index'], beanQueue))

    beanDependents = list(filter(lambda bean: bean['index'] not in beanIndexes, beans))
    beanQueueNames = list(map(lambda bean: bean['name'], beanQueue))

    for i in range(len(beanQueue)):
        beanQueue[i]['index'] = i

    for dependents in beanDependents:
        args = list(dependents['kwargs'].values())
        flag = True
        for argClassName in args:
            if (argClassName not in beanQueueNames and argClassName in allBeanNames) or argClassName in beanQueueNames:
                flag = flag and True
                dependents['index'] = getBean(beans, argClassName)['index'] + max(beanIndexes)
            else:
                flag = False

        if flag:
            beanQueue.append(dependents)
            beanQueueNames.append(dependents['name'])

    assert len(beanQueue) == len(beans), "Somebeans were not initialized properly"
    return list(sorted(beanQueue, key=lambda x: x['index']))
