from helper import *

"""

There are 3 groups of entities:
    metaclass   = object to create TYPE-OBJECTS instances                       TYPE, subclass of OBJECT
    class       = instance of metaclass, object to create DATA instances        OBJECT, instance of TYPE
    instance    = instance of class which contains data, NON-TYPE-OBJECT                      

Possible relationships:

    'is a unit of' = instance / type      ..  [dash] ..  horizontal relations              
        type(smth)
        smth.__class__
        isinstance(instance, class)
    
    'is a kind of' = subclass / superclass  ..  [solid] ..   vertical relations              
        smth.__bases__
        issubclass(sub, super)
    
"""

# instance / type
print(type(type))               # = 'type' = TYPE is instance of TYPE           [1]
print(type(object))             # = 'type' = OBJECT is instance of TYPE         [2]

# subtype / supertype
print(type.__bases__)           # = 'object' = TYPE is subtype of OBJECT        [3]
print(object.__bases__)         # = [empty]  = OBJECT has not supertypes        [4]


"""

DASH rules:
    (1)   A is instance of B  ::  B is subtype of C  ::  then A is instance of C  
    (2)   X is instance of Y  ::  Z is subtype of X  ::  then Z is instance of Y  

SOLID rule: 
    (3)  A is subtype of B   ::  B is subtype of C  ::  then A is subtype of C
        
These rules 
    - are important for understanding relations while inheritance
    - might be used to 'revert' TYPE vs OBJECT relations  (see example below and don't take it in mind)
 
"""

# [1] TYPE is instance of TYPE       \
# [3] TYPE is subtype of OBJECT       >  TYPE is instance of OBJECT    (consistent logic, but is not used in Python)
# (1) TYPE is instance of OBJECT     /
print(isinstance(type, object))

# [1] OBJECT is instance of TYPE     \
# [2] TYPE is subtype of OBJECT       >  OBJECT is instance of OBJECT  (consistent logic, but is not used in Python)
# (1) OBJECT is instance of OBJECT   /
print(isinstance(object, object))


"""

All objects are of two categories:
    TYPE-OBJECT = object which might be a type for instance                     instances of TYPE, subclass of OBJECT
    NON-TYPE-OBJECT = instance which cannot be a type for another instance      instances of instances of TYPE

"""


class TypeObject:
    pass


nonTypeObject = TypeObject()
print("TypeObject = instance of type:", type(TypeObject), ", subclass of class:", TypeObject.__bases__)
print("nonTypeObject = instance of:", type(nonTypeObject))


"""

METACLASS = special object is used to creating TYPE-OBJECTS
TYPE is DEFAULT METACLASS which is used if no user METACLASS is provided

Steps to create METACLASS:
    1. choose class which metaclass is used for
    2. define it's base class                           (see 1.)
    3. define type of it's base class                   (see 2.)
    4. declare metaclass derived from defined type      (see 3.)
    5. use __metaclass__ attribute in chosen class      (see 1. and 4.)

Example:
    1. Want to create 'class MyClass' 
    2. MyClass derived only from OBJECT
    3. Get type(OBJECT) = TYPE
    4. class MyMetaclass(TYPE)
    5. class MyClass: ... __metaclass__ = MyMetaclass  

"""

