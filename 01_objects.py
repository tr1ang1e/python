class Class:
    class_var = "I'm of Class type"

    def __init__(self):
        self.my_variable = "my variable is form Class.__init__()"


class AnotherClass:
    class_var = "I'm form AnotherClass"

    def __init__(self):
        self.my_variable = "my variable is form AnotherClass.__init__()"


def example():

    # every entity in Python is 'object'
    print("\n:: __class__ examples ")
    print(Class.__class__)          # 'Class'    is object  -  instance of type 'type' (type of types!)
    print(Class().__class__)        # 'Class()'  is object  -  instance of type 'Class'

    # __class__ and 'type' are the same
    print("\n:: __class__ and type()")
    print(Class.__class__ is type(Class) is type)
    print(Class().__class__ is type(Class()) is Class)      # ignore warning, this 'strong' comparison is correct

    # if we change instance '__class__' value,
    # instance will really be of another class
    print("\n:: change object type through the __class__ attribute")
    c = Class()
    c.__class__ = AnotherClass
    print(c.class_var)      # will be from AnotherClass
    print(c.my_variable)    # will be from Class  <<  __init__ wouldn't be called


if __name__ == '__main__':
    example()
