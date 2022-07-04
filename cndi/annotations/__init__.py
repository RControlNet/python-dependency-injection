from cndi.annotations.component import ComponentClass
import logging

logger = logging.getLogger("cndi.annotations")

beans = list()
autowires = list()
components = list()
beanStore = dict()
componentStore = dict()
profiles = dict()

from functools import wraps
import importlib
import copy


def importModuleName(fullname):
    modules = fullname.split('.')
    module = importlib.import_module(modules[-1], package='.'.join(modules[:-1]))
    return module

def normaliseModuleAndClassName(name):
    nameList:list = name.split(".")
    if "__init__" in nameList:
        nameList.remove("__init__")
    return '.'.join(nameList)
def getBeanObject(objectType):
    objectType = normaliseModuleAndClassName(objectType)
    bean = beanStore[objectType]
    objectInstance = bean['objectInstance']
    # if (objectInstance.__class__.__name__ == "function"):
    #     args[key] = objectInstance()
    # else:
    return copy.deepcopy(objectInstance) if bean['newInstance'] else objectInstance


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
            map(lambda dependency: normaliseModuleAndClassName('.'.join([dependency.__module__, dependency.__name__])), self.kwargs.values()))


def Component(func: object):

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    moduleName = wrapper.__module__[:-9] if wrapper.__module__.endswith(".__init__") else wrapper.__module__
    componentFullName = '.'.join([moduleName,wrapper.__qualname__])
    logger.info(f"Function name " + componentFullName)
    duplicateComponents = list(filter(lambda component: component.fullname == componentFullName, components))
    if duplicateComponents.__len__() > 0:
        logger.info(f"Duplicate Component found for: {duplicateComponents}")
    else:
        components.append(ComponentClass(**{
            'fullname': componentFullName,
            'func': wrapper,
            'annotations': wrapper.__init__.__annotations__ if "__annotations__" in dir(wrapper.__init__) else {}
        }))
    return  wrapper


def Bean(newInstance=False):
    def inner_function(func):
        annotations = func.__annotations__
        returnType = annotations['return']
        del annotations['return']

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        annotations = dict(
            map(lambda key: (key, '.'.join([annotations[key].__module__, annotations[key].__qualname__])), annotations))
        beans.append({
            'name': '.'.join([returnType.__module__, returnType.__name__]),
            'newInstance': newInstance,
            'object': wrapper,
            'fullname': wrapper.__qualname__,
            'kwargs': annotations,
            'index': len(beans)
        })
        return wrapper

    return inner_function


def Autowired(required=True):
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


