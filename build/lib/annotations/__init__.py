from annotations.component import ComponentClass

beans = list()
autowires = list()
components = list()
beanStore = dict()
componentStore = dict()

from functools import wraps, partial
import importlib
import copy

def importModuleName(fullname):
    modules = fullname.split('.')
    module = importlib.import_module(modules[-1], package='.'.join(modules[:-1]))
    return module

class AutowiredClass:
    def __init__(self, required, func, kwargs: dict()):
        self.fullname = '.'.join([func.__qualname__])
        self.className = '.'.join(func.__qualname__.split(".")[:-1])
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
            print("Skipping ", self.fullname)
            assert not self.required, "Could not initialize " + self.fullname + " with beans " + str(
                dependencyNotFound)

        kwargs = self.kwargs
        args = dict()
        for (key, value) in kwargs.items():
            fullName = '.'.join([value.__module__, value.__name__])
            if fullName in beanStore:
                bean = beanStore[fullName]
                objectInstance = bean['object']
                # if (objectInstance.__class__.__name__ == "function"):
                #     args[key] = objectInstance()
                # else:
                args[key] = copy.deepcopy(objectInstance) if bean['newInstance'] else objectInstance

        if self.className in beanStore:
            self.func(beanStore[self.className], **args)
        else:
            self.func(**args)

    def calculateDependencies(self):
        return list(map(lambda dependency: '.'.join([dependency.__module__, dependency.__name__]), self.kwargs.values()))

def Component(func: object):
    annotations = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    components.append(ComponentClass(**{
        'fullname': wrapper.__qualname__,
        'func': wrapper,
        'args': annotations
    }))

    return wrapper

def Bean(newInstance=False):
    def inner_function(func):
        annotations = func.__annotations__
        returnType = annotations['return']
        del annotations['return']

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        annotations = dict(map(lambda key: (key , '.'.join([annotations[key].__module__ , annotations[key].__qualname__])), annotations))
        beans.append({
            'name': '.'.join([returnType.__module__, returnType.__name__]),
            'newInstance': newInstance,
            'object': wrapper,
            'fullname': wrapper.__qualname__,
            'kwargs':  annotations,
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

        autowires.append(AutowiredClass(required=required,**{
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

class AppInitilizer:
    def run(self):
        global autowires
        workOrderBeans = workOrder(beans)
        print(list(map(lambda x: x['name'], workOrderBeans)))
        for bean in workOrderBeans:
            print("Registering Bean", bean['fullname'])
            kwargs = dict()
            for key, className in bean['kwargs'].items():
                tempBean = beanStore[className]
                kwargs[key] = copy.deepcopy(tempBean['object']) if tempBean['newInstance'] else tempBean['object']

            bean['object'] = bean['object'](**kwargs)
            beanStore[bean['name']] = bean

        for component in components:
            print(component.getInnerAutowiredClasses(autowires)[0])
            componentStore[component.fullname] = component
            beanStore[component.fullname] = component.func()

        for autowire in autowires:
            autowire.dependencyInject()
