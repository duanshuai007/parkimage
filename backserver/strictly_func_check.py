#!/usr/bin/env python3

from functools import wraps
import inspect
#通过修饰器对函数的参数和返回值进行检测

def strictly_func_check(function):
    #获取函数的参数和返回值列表
    annotations = function.__annotations__
    arg_spec = inspect.getfullargspec(function)
#    print("annotations:", annotations)
#    print(type(annotations))
#    print("arg_spec:", arg_spec)
#    print(type(arg_spec))
#    print("arg_spec.args:", arg_spec.args)
#    print("arg_spec_kwonlyargs:", arg_spec.kwonlyargs)

#    inClassFlag = False
    assert "return" in annotations, "missing type for return value"
    for arg in arg_spec.args + arg_spec.kwonlyargs:
#        if arg == 'self':
#            inClassFlag = True
#            continue
        assert arg in annotations, ("missing type for parameter '" + arg +"'")
    @wraps(function)
    def wrapper(*args, **kwargs):
        l1 = list(zip(arg_spec.args, args))
        l2 = list(kwargs.items())
#        print(l1)
#        print(l2)
#        if inClassFlag == True:
#            l1.pop(0)
        for name, arg in (l1 + l2):
            assert isinstance(arg, annotations[name]), (
                "expected argument {} of {} but got {}".format(name, annotations[name], type(arg))
            )
        result = function(*args, **kwargs)
        if result is not None:
            assert isinstance(result, annotations["return"]), (
                "expected return of {} got {}".format(annotations["return"], type(result))
            )
        return result
    return wrapper

'''
@strictly_func_check
def testFunc(name : str, age:int, info:list) -> bool:
    print("name:", name)
    print("age:", age)
    print("info", info)
    return True

if __name__ == "__main__":
    testFunc('duan', 33, ["shenyang", 'tiexi', 'yunfeng', 789])
'''
