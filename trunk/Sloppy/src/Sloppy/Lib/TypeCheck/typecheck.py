import inspect
from containers import TypedList, TypedDict


__all__ = ['Undefined', 'Integer', 'Float', 'Bool', 'String', 'Unicode',
           'Instance', 'List', 'Dict', 'Choice', 'Mapping']


# bool is not like the bool in VP, because strings are not treated properly.
# therefore we would have to check for this in projectio.


#------------------------------------------------------------------------------
class Undefined:
    def __repr__(self): return __str__
    def __str__(self): return "Undefined value"



class Descriptor(object):

    def __init__(self, **kwargs):
        self.key = None
        self.doc = None
        self.blurb = None
        self.keepraw = False
        
        self.on_update = kwargs.pop('on_update', lambda obj, key, value: Undefined)

        # the on_init is a lambda function returning the
        # init value for a given object. You can either
        # specify a keyword 'init' which will be translated
        # to (lambda obj: init) or you can specify a direct
        # lambda function using the keyword 'on_init'.
        # If nothing is given, then Undefined is set as init-
        init = kwargs.pop('init', Undefined)
        self.on_init = kwargs.pop('on_init', lambda obj: init)
        
        self.__dict__.update(kwargs)
        
        
    def __get__(self, obj, type=None):
        # if obj is None, return self
        if obj is None:
            return self
        else:
            return obj.__dict__[self.key]

    def __set__(self, obj, value):
        obj.__dict__[self.key] = self.check(value)
        if self.keepraw is True:
            obj.__dict__[self.key+"_"] = value

        self.on_update(obj, self.key, value)

    def __delete__(self, obj):
        raise AttributeError("Can't delete attribute %s" % self.key)


    def init(self, obj, key, initval=Undefined):
        self.key = key
        
        if initval is Undefined:
            initval = self.on_init(obj)

        obj.__dict__[key] = Undefined
        if self.keepraw is True:
            obj.__dict__[key+"_"] = Undefined

        if initval is not Undefined:
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
Bool = new_type_descriptor(bool, 'a boolean value')


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
            
    def check(self, value):
        if value in self.adict.keys():
            return self.adict[value]
        elif self.reverse is True:
            if value in self.adict.values():
                return value
            else:
                raise ValueError("Value %s must be one of %s or one of %s" % (value, str(self.adict.keys()), str(self.adict.values())))
        else:
            raise ValueError("Value %s must be one of %s" % (value, str(self.adict.keys())))



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
        if kwargs.has_key('on_init') is False and \
           kwargs.has_key('init') is False:
            kwargs['init'] = []
        Descriptor.__init__(self, **kwargs)

    def check(self, value):
        if isinstance(value, TypedList):
            value.descr = self.descr
            return value
        elif isinstance(value, list):
            return TypedList(self.descr, value)
        else:
            raise TypeError("A list required.")


class Dict(Descriptor):

    def __init__(self, keys, values, **kwargs):
        self.key_descr = keys
        self.value_descr = values
        if kwargs.has_key('on_init') is False and \
           kwargs.has_key('init') is False:
            kwargs['init'] = {}
        Descriptor.__init__(self, **kwargs)

    def check(self, value):
        if isinstance(value, TypedDict):
            value.value_descr = self.value_descr
            value.key_descr = self.key_descr
            return value
        elif isinstance(value, dict):
            return TypedDict(self.key_descr, self.value_descr, value)
        else:
            raise TypeError("A dict required.")


#------------------------------------------------------------------------------
class HasDescriptors(object):
    def __init__(self, **kwargs):
        object.__init__(self)
        
        # We need to iterate over all descriptor instances and
        # (a) set their key attribute to their name, 
        # (b) init the descriptor
        
        # To support inheritance, we need to take all base classes
        # into account as well. To give meaningful error messages, we
        # reverse the order and define the base class descriptors
        # first.
        
        klasslist = list(self.__class__.__mro__[:-1])
        klasslist.reverse()

        descriptors = {}
        for klass in klasslist:
            for key, item in klass.__dict__.iteritems():
                if isinstance(item, Descriptor):
                    item.init(self, key, kwargs.pop(key, Undefined))
                    descriptors[key] = item
       
        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)

        # quick property retrieval: self._descr[key]
        self._descr = descriptors        


class SloppyObject(HasDescriptors):
    
    def set(self, *args, **kw):
        # TODO: somehow it should be possible to _collect_
        # TODO: update informations...
        # TODO: But maybe the problem would be solved if
        # TODO: we could improve the signal mechanism
        # TODO: to block (and maybe store them for later
        # TODO: retrieval) certain signals.
        for arg in args:
            arglist = list(args)
            while len(arglist) > 1:
                key = arglist.pop(0)
                value = arglist.pop(0)
                self.__setattr__(key, value)
            
        for key, value in kw.iteritems():
            self.__setattr__(key, value)

    def get(self, *keys, **kwargs):
        default = kwargs.pop('default', Undefined)
        if len(keys) == 1:
            value = object.__getattribute__(self, keys[0])
            if value is Undefined:
                value = default
            return value
        else:
            values = []
            for key in keys:
                value = object.__getattribute__(self, key)
                if value is Undefined:
                    value = default
                values.append(value)
            return tuple(values)
        

class Example(SloppyObject):

    an_int = Integer()
    another_int = Integer(strict=True, none=True)
    a_choice = Choice(['eggs', 'bacon', 'cheese'])
    a_bool = Bool()
    another_bool = Bool(strict=True)
    a_mapping = Mapping({6:'failed miserably',5:'failed',4:'barely passed',
                         3:'passed',2:'good',1:'pretty good'}, keepraw=True)

    another_mapping = Mapping({6:'failed miserably',5:'failed',4:'barely passed',
                         3:'passed',2:'good',1:'pretty good'}, reverse=True)

    an_instance = Instance('Example', none=True)

    a_list = List(Integer())
    another_list = List(Mapping({'good':1,'evil':-1}))

    a_dict = Dict(keys=Integer(), values=String())
    


        



###############################################################################
print "---"
e = Example(an_int=10.5)
print e.an_int
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
print "MAPPED VALUE", e.a_mapping
print "RAW VALUE:", e.a_mapping_

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

print e._descr['another_list'].on_init(e)


def list_was_updated(sender, key, value):
    print "list '%s' was updated to", value
e._descr['another_list'].on_update = list_was_updated

def listitems_were_updated(sender, action, items):
    print "list items were ", action, items
e.another_list.descr.on_update = listitems_were_updated
e.another_list.append('evil')
e.another_list.remove(1)
e.another_list.extend(['good','evil'])

e.another_list = ['good']
print e.another_list

def dictitems_were_updated(sender, action, items):
    print "dict items were ", action, items

e._descr['a_dict'].value_descr.on_update = dictitems_were_updated
e.a_dict = {}

print "----------"

def notify(sender, key, value):
    print "notify", key, value
e._descr['a_bool'].on_update = notify
e._descr['a_choice'].on_update = notify
e.a_bool = True
e.a_bool = False
e.a_choice = 'bacon'


e.set('a_bool', False, a_choice='eggs')

print "*"*80

print e.get('a_bool')
print e.get('a_bool','a_choice')
print "*"*80

print "CREATING A"
print "=========="
a = Example(an_int=5, a_dict={'Hallo':5})

print a.a_dict
print a.a_bool
print a.an_int
print a.get('a_bool', 'an_int')
