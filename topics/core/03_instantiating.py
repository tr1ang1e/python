"""
Class instance creating is done in two steps:
    1 = creating object         :     class.__new__()
    2 = initializing object     :     class.__init__()

If there are no definition of these methods in class
(or one of them), the method of base class is called
(at least 'object' class is always base for all of).

Function 'super()' is used to find necessary attributes
of class' base classes.
"""


# call 'object' methods
class A:
    pass


# call explicitly defined methods
class B:

    # creating instance object
    def __new__(cls, *args, **kwargs):  # args and kwargs are recommended to be used
        obj = super().__new__(cls)      # in this case, same as 'object.__new__(cls)' or 'super(B, cls)'
        print("calling __new__() :", obj)
        return obj

    # initializing instance object
    def __init__(self):
        # super().__init__()            # if necessary to call super class
        print("calling __init__() :", self)


a = A()     # no output, same as 'a = super(A, A).__new__(A)' + 'super(A, A).__init__(a)'
b = B()     # same as 'B.__new__()' + 'b.__init__()'

c = B.__new__(B)
c.__init__()


"""
Can create SINGLETON using __new__() and super()
    - create instance only once
    - keep it inside class member
    - return it every time when required
"""


class Singleton:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance


inst1 = Singleton()
inst2 = Singleton()
print(inst1 is inst2)
