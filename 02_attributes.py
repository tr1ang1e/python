# 'class' is a keyword to create new type = new instance of type 'type'
class Class:
    attr_type = None
    at = 'class'

    def __init__(self):
        self.attr_instance = None
        self.at = 'instance'


def example():

    # every object has __dict__ attribute to keep all objects attributes
    # __dict__['attribute'] = value
    print("\n:: __dict__ examples ")
    print(Class.__dict__)           # keeps only class-specific attributes (no 'self' attributes)
    print(Class().__dict__)         # keeps only instance-specific attributes (no 'cls' attributes)
    print(Class().attr_instance)    # access to class-specific attribute is allowed

    # type and instance attributes might have same name
    print("\n:: class and instance attributes ")
    print(Class.at)
    print(Class().at)
    print(Class().__class__.at)

    # built-in types not necessary have '__dict__' attr
    # print((42).__dict__)  # uncomment to cause the error

    ''' 
    variants of how to deal with attributes
    example for class object  >>  the same is for instance object
    '''
    print("\n:: working with attributes ")

    # get attribute value
    print(Class.attr_type == getattr(Class, "attr_type", None))     # last arg is not necessary but might be helpful

    # set value for existent or new attribute
    Class.new_attr_1 = 42
    setattr(Class, "new_attr_2", 42)
    print(Class.new_attr_1 == Class.new_attr_2)

    # delete attributes
    del Class.new_attr_1
    delattr(Class, "new_attr_2")
    print(getattr(Class, "new_attr_1", None) is getattr(Class, "new_attr_2", None))

    # delete attributes, pay attention!
    # 'del' and 'delattr' work with __dict__
    # so the following code will cause error
    # delattr(Class, "attr_instance")   # the same is for 'del'
    # delattr(Class(), "attr_type")     # the same is for 'del'


if __name__ == '__main__':
    example()
