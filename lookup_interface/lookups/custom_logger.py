import logging
from types import MethodType
from requests import JSONDecodeError

def handle_method(method, cls_name):
    '''
        Considering that we will apply this decorator manually to each function call, 
        we can simply pass the class name so that we can handle the results better.
    '''
    def inner(*args, **kwargs):
        error_query = f'{method.__name__}  -  {cls_name}' + ': {exc}'
        try:
            data = method(*args, **kwargs)
        except TypeError as ex:
            raise TypeError(error_query.format(exc = ex))
        
        except JSONDecodeError as ex:
            raise JSONDecodeError(error_query.format(exc = ex))
        return data

    return inner

def handle_class(cls):
    '''
        Instead of applying the decorator for each method in the lookup classes,
        we use a handle_class class decorator. 
        If the accessed attribute is of type method, then it applies the decorator and returns the decorated method, 
        else it returns the attribute.
    '''

    class ModifiedClass(object):
        def __init__(self, *args, **kwargs):
            self.oldInstance = cls(*args, **kwargs)
        def __getattribute__(self, name):
            try:
                x = super(ModifiedClass, self).__getattribute__(name)
            except AttributeError:
                pass
            else:
                return x
            
            x = self.oldInstance.__getattribute__(name)
            if isinstance(x, MethodType):
                return handle_method(x, self.__class__.__name__)
            else:
                return x
    return ModifiedClass
