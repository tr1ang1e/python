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
    print(Class.__dict__)       # keeps only class-specific attributes (no 'self' attributes)
    print(Class().__dict__)     # keeps only instance-specific attributes (no 'cls' attributes)

    # type and instance attributes might have same name
    print(Class.at)
    print(Class().at)
    print(Class().__class__.at)

    # built-in types not necessary have '__dict__' attr
    # print((42).__dict__)  # uncomment to cause the error


if __name__ == '__main__':
    example()
