
import inspect
from containers import TypedList, TypedDict


__all__ = ['Undefined', 'Integer', 'Float', 'Bool', 'String', 'Unicode',
           'Instance', 'List', 'Dict', 'Choice', 'Mapping']


# list/dict notification problem:
#  what if we implemented that list/dict would call some function,
#  on_notify, and then the main object has to take care that
#  this notification reaches the correct place?


#------------------------------------------------------------------------------
class Undefined:
    def __str__(self):
        return "Undefined value"



class Descriptor(object):

    def __init__(self, **kwargs):
        self.key = None
        self.doc = None
        self.blurb = None

        # the on_default is a lambda function returning the
        # default value for a given object. You can either
        # specify a keyword 'default' which will be translated
        # to (lambda obj: default) or you can specify a direct
        # lambda function using the keyword 'on_default'.
        # If nothing is given, then Undefined is set as default-
        default = kwargs.pop('default', Undefined)
        self.on_default = kwargs.pop('on_default', lambda obj: default)
        
        self.__dict__.update(kwargs)
        
        
    def __get__(self, obj, type=None):
        # if obj is None, return self
        if obj is None:
            return self
        else:
            return obj.__dict__[self.key]

    def __set__(self, obj, value):
        obj.__dict__[self.key] = self.check(value)

    def __delete__(self, obj):
        raise AttributeError("Can't delete attribute %s" % self.key)


    def init(self, obj, key, initval=Undefined):
        self.key = key
        
        if initval is Undefined:
            initval = self.on_default(obj)

        if initval is Undefined:
            obj.__dict__[key] = Undefined
        else:
            self.__set__(obj, initval)
            



def new_type_descriptor(_type, _typename):
    
    class TypeDescriptor(Descriptor):

        def __init__(self, **kwargs):
            self.strict = False
            self.none = True
            self.min = None
            self.max = None
            Descriptor.__init__(self, **kwargs)

        def check(self, value):
            
            if value is None:
                if self.none is True:
                    return None
                else:
                    raise ValueError("Value %s must be %s." % (value, _typename) )

            if self.strict is True:
                if not isinstance(value, _type):       
                    raise ValueError("Value %s must be %s" % (value, _typename) )
            else:
                value = _type(value)

            if (self.min is not None and value < self.min):
                raise ValueError("Value must be at least %s" % self.min)
            if  (self.max is not None and value > self.max):
                raise ValueError("Value may be at most %s" % self.max)
            
            return value

    return TypeDescriptor


Integer = new_type_descriptor(int, 'an integer')
Float = new_type_descriptor(float, 'a float')
Unicode = new_type_descriptor(unicode, 'an unicode string')
String = new_type_descriptor(str, 'a string')


class Bool(Descriptor):

    def __init__(self, **kwargs):
        self.strict = False
        self.none = True
        Descriptor.__init__(self, **kwargs)
    
    def __set__(self, obj, value):
        if value is None:
            if self.none is True:
                obj.__dict__[self.key] = None
                return
            else:
                raise ValueError("Value %s must be a boolean value." % value)

        if self.strict is True:
            if not isinstance(value, bool):       
                raise ValueError("Value %s must be a boolean value" % value)
        else:
            if isinstance(value, bool):
                obj.__dict__[self.key] = bool(value)
            elif isinstance(value, basestring):
                if "true".find(value.lower()) > -1:
                    obj.__dict__[self.key] = True
                elif "false".find(value.lower()) > -1:
                    obj.__dict__[self.key] = False
            elif isinstance(value, (int,float)):
                obj.__dict__[self.key] = bool(value)
            else:
                raise ValueError("Value %s must be a valid True/False value (bool or a 'true'/'false' string)" % value )

class Choice(Descriptor):

    def __init__(self, alist, **kwargs):
        self.alist = alist
        Descriptor.__init__(self, **kwargs)
        
    def check(self, value):
        if value in self.alist:
            return value
        else:
            raise ValueError("Value %s must be one of %s" % (value, str(self.alist)))

class Mapping(Descriptor):

    def __init__(self, adict, **kwargs):
        self.adict = adict
        self.reverse = False
        Descriptor.__init__(self, **kwargs)

    def __set__(self, obj, value):
        obj.__dict__[self.key] = self.check(value)
        if hasattr(self, '_setmap'):
            obj.__dict__[self.mapkey] = self._setmap
            del self._setmap
            
    def check(self, value):
        if value in self.adict.keys():
            self._setmap = value
            return self.adict[value]
        elif self.reverse is True:
            if value in self.adict.values():
                self._setmap = value
                return value
            else:
                raise ValueError("Value %s must be one of %s or one of %s" % (value, str(self.adict.keys()), str(self.adict.values())))
        else:
            raise ValueError("Value %s must be one of %s" % (value, str(self.adict.keys())))


    def init(self, obj, key, initval=Undefined):
        self.key = key
        self.mapkey = key+"_"
        
        if initval is Undefined:
            initval = self.on_default(obj)

        if initval is Undefined:
            obj.__dict__[key] = Undefined
            obj.__dict__[self.mapkey] = Undefined
        else:
            self.__set__(obj, initval)            


class Instance(Descriptor):

    def __init__(self, instance, **kwargs):
        self.instance = instance
        Descriptor.__init__(self, **kwargs)

    def check(self, value):
        if value is None:
            if self.none is True:
                return None
            else:
                raise ValueError("Value %s may not be None." % value)

        # self.instance may be a class or the name of a class
        # in the first case we use isinstance() for the check,
        # in the second case we compare the class names.
        if inspect.isclass(self.instance):
            if isinstance(value, self.instance):
                return value
            else:
                raise ValueError("Value %s must be an instance of %s" % (value, self.instance.__name__))
        else:
            if value.__class__.__name__ == self.instance:
                return value
            else:
                raise ValueError("Value %s must be an instance of %s" % (value, self.instance))
            

class List(Descriptor):

    def __init__(self, descr, **kwargs):
        self.descr = descr
        Descriptor.__init__(self, **kwargs)

    def check(self, value):

        def check_item(v):
            try:
                return self.descr.check(v)
            except Exception, msg:
                # TODO:
                raise

        if isinstance(value, TypedList):
            value.check = check_item
            return value
        elif isinstance(value, list):
            return TypedList(check_item, value)
        else:
            raise TypeError("A list required.")


class Dict(Descriptor):

    def __init__(self, descr, **kwargs):
        self.descr = descr
        Descriptor.__init__(self, **kwargs)

    def check(self, value):

        def check_item(v):
            try:
                return self.descr.check(v)
            except Exception, msg:
                # TODO:
                raise

        if isinstance(value, TypedDict):
            value.check = check_item
            return value
        elif isinstance(value, dict):
            return TypedDict(check_item, value)
        else:
            raise TypeError("A dict required.")
        


#------------------------------------------------------------------------------
class Example(object):

    an_int = Integer()
    another_int = Integer(strict=True, none=True)
    a_choice = Choice(['eggs', 'bacon', 'cheese'])
    a_bool = Bool()
    another_bool = Bool(strict=True)
    a_mapping = Mapping({6:'failed miserably',5:'failed',4:'barely passed',
                         3:'passed',2:'good',1:'pretty good'})

    another_mapping = Mapping({6:'failed miserably',5:'failed',4:'barely passed',
                         3:'passed',2:'good',1:'pretty good'}, reverse=True)

    an_instance = Instance('Example', none=True)

    a_list = List(Integer())
    another_list = List(Mapping({'good':1,'evil':-1}))
    
    def __init__(self, **kwargs):

        # We need to iterate over all descriptor instances and
        # (a) set their key attribute to their name, 
        # (b) create the corresponding instance attribute for them,
        # (c) set this attribute either to default or to the value
        #     given by the keyword argument
        
        # To support inheritance, we need to take all base classes
        # into account as well. To give meaningful error messages, we
        # reverse the order and define the base class descriptors
        # first.
        
        klasslist = list(self.__class__.__mro__[:-1])
        klasslist.reverse()

        descriptors = {}
        for klass in klasslist:
            for key, item in self.__class__.__dict__.iteritems():
                if isinstance(item, Descriptor):
                    item.init(self, key, kwargs.pop(key,Undefined))
                descriptors[key] = item
       
        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)

        # quick property retrieval: self._descr[key]
        self._descr = descriptors

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if hasattr(self, 'on_notify') and self._descr.has_key(key):
            self.on_notify(self, key, value)
        



###############################################################################
print "---"
e = Example(an_int=10.5)
e.another_int = 11
#e.another_int=10.5
print e.an_int,":",e.another_int

e.a_choice = 'eggs'
#e.a_choice = 'jam'

e.a_bool = True
e.a_bool = 'True'
e.a_bool = 'true'
e.a_bool = 'fals'
#e.a_bool = 'MIST'

e.another_bool = None
#e.another_bool = 'True'


e.a_mapping = 2
print e.a_mapping
print e.a_mapping_

e.another_mapping = 2
print e.another_mapping

print "REVERSE IS ", e.__class__.another_mapping.reverse
e.another_mapping = 'failed'
print e.another_mapping

e.an_instance = e
#e.an_instance = 5

e.a_list = [2]
#e.a_list = [2,'niki']
e.a_list.append(5)
#e.a_list.append('niki')

e.another_list = ['good']

print e._descr['another_list'].on_default(e)


def was_notified(sender, key, value):
    print "The object %s has set its attribute '%s' to '%s'" % (sender, key, value)
e.on_notify = was_notified
e.a_bool = False

e.another_list.append('evil')
e.another_list.remove(1)
e.another_list.extend(['good','evil'])
print e.another_list
