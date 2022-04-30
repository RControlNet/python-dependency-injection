class ComponentClass:
    def __init__(self, fullname, func, annotations):
        self.fullname = fullname
        self.func = func
        self.annotations = annotations

    def getInnerAutowiredClasses(self, autowires):
        return list(filter(
            lambda autowire: autowire.className == self.fullname,
            autowires
        ))