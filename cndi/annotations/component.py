class ComponentClass:
    def __init__(self, fullname, func):
        self.fullname = fullname
        self.func = func

    def getInnerAutowiredClasses(self, autowires):
        return list(filter(
            lambda autowire: autowire.className == self.fullname,
            autowires
        ))