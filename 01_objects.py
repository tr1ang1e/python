class Class:
    pass


def example():

    # every entity in Python is 'object'
    print(Class.__class__)          # 'Class'    is object  -  instance of type 'type' (type of types!)
    print(Class().__class__)        # 'Class()'  is object  -  instance of type 'Class'

    # __class__ and 'type' are the same
    print(Class.__class__ is type(Class) is type)
    print(Class().__class__ is type(Class()) is Class)      # ignore warning, this 'strong' comparison is correct


if __name__ == '__main__':
    example()
