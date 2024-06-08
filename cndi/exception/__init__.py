class InvalidBeanDefination(Exception):
    def __init__(self, message):
        super().__init__(self, message)

class BeanNotFoundException(Exception):
    def __init__(self, message):
        super(BeanNotFoundException, self).__init__(message)
