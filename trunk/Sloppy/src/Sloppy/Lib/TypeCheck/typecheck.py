import inspect
from containers import TypedList, TypedDict


__all__ = ['Undefined', 'Integer', 'Float', 'Bool', 'String', 'Unicode',
           'Instance', 'List', 'Dict', 'Choice', 'Mapping']


#------------------------------------------------------------------------------
class Undefined:
    pass


class Descriptor(object):

    def __init__(self, **kwargs):
        self.doc = None
        self.blurb = None
        self.raw = False
        
        # the on_init is a lambda function returning the
        # init value for a given object. You can either
        # specify a keyword 'init' which will be translated
        # to (lambda obj: init) or you can specify a direct
        # lambda function using the keyword 'on_init'.
        # If nothing is given, then the value is Undefined.
        init = kwargs.pop('init', Undefined)        
        self.on_init = kwargs.pop('on_init', lambda obj: init)        
        
        self.__dict__.update(kwargs)
        
        
    def get(self, obj, key):
        return obj.__dict__[key]

    def set(self, obj, key, value):
        obj.__dict__[key] = self.check(value)
        if self.raw is True:
            obj.__dict__[key+"_"] = value
        

    def init(self, obj, key, value):
        " Similar to 'set', but accepts Undefined as valid. "        
        if value is Undefined:
            value = self.on_init(obj)

        if value is Undefined:
            obj.__dict__[key] = Undefined
            if self.raw is True:
                obj.__dict__[key+"_"] = Undefined
        else:
            self.set(obj, key, value)


def new_type_descriptor(_type, _typename):
    
    class TypeDescriptor(Descriptor):

        def __init__(self, **kwargs):
            self.strict = False
            self.required = True
            self.min = None
            self.max = None
            Descriptor.__init__(self, **kwargs)

        def check(self, value):
            
            if value is None:
                if self.required is False:
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
Bool = new_type_descriptor(bool, 'a boolean value')

Unicode = new_type_descriptor(unicode, 'an unicode string')
String = new_type_descriptor(str, 'a string')


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
            if self.required is False:
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
        # TODO: keep the TypedList, only change the contents!
        # TODO: this way, the signals will be kept.
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

        # Initialize props and values dict
        object.__setattr__(self, '_descr', {})
        object.__setattr__(self, 'on_update', lambda sender, key, value: None)
        
        # We need to iterate over all Descriptor instances and
        # set default values for them.
        
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
                    if descriptors.has_key(key):
                        raise KeyError("%s defines Descriptor '%s', which has already been defined by a base class!" % (klass,key))
                    descriptors[key] = item
                    
                    item.init(self, key, kwargs.pop(key, Undefined))

       
        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)

        # descriptor retrieval
        self._descr = descriptors        
        

    def __getattribute__(self, key):
        descr = object.__getattribute__(self, '_descr')
        if descr.has_key(key):
            return descr[key].get(self, key)
        return object.__getattribute__(self, key)

    def __setattr__(self, key, value):
        descr = self._descr
        if descr.has_key(key):
            descr[key].set(self, key, value)
            self.on_update(self, key, value)
        else:
            object.__setattr__(self, key, value)
    
    def set(self, *args, **kw):
        """ Set the given attribute(s) to specified value(s).

        You may pass an even number of arguments, where one
        argument is the attribute name and the next one the
        attribute value. You may also pass this as keyword
        argument, i.e. use the key=value notation.
        """        
        for arg in args:
            arglist = list(args)
            while len(arglist) > 1:
                key = arglist.pop(0)
                value = arglist.pop(0)
                self.__setattr__(key, value)
            
        for key, value in kw.iteritems():
            self.__setattr__(key, value)

    def get(self, *keys, **kwargs):        
        """ Retrieve attribute value(s) from object based on the
        attribute names.

        Returns a single value if one attribute name is given and
        returns a tuple of values if more than one name is given.
        The keyword argument 'default' may be given as a value
        to be displayed for Undefined values.
        """
        
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




    # --- compatibility ----

    # HasProperties methods:
    # - set_value aka set
    # - set_values
    # - get_value aka get
    # - get_values
    # - get_prop
    # - get_props
    # - copy
    # - create_changeset
    # - get_keys

    def get_values(self):
        rv = {}
        for key in self._descr.keys():
            rv[key] = self.get(key)
        return rv






###############################################################################


# test fixture -- preparing and cleaning up: TestCase.setUp(), TestCase.tearDown()
# test case -- simple single test
# test suites -- test cases or suites that should run together
# test runner -- graphical/textual representation of the test

import unittest

class Ingredient(HasDescriptors):
    name = String()
    
class Recipe(HasDescriptors):
    author = String(strict=True)
    calories = Integer()
    comment = String(required=False)
    skill = Mapping({'easy':1, 'intermediate':2, 'advanced':3},
                    reverse=True, raw=True)
    category = Choice(['breakfast', 'lunch', 'dinner', 'snack'])
    is_tested = Bool()
    ingredients = List(Instance('Ingredient'))
    reviews = Dict(keys=String(), values=String())
        
class DescriptorTestCase(unittest.TestCase):

    def setUp(self):
        self.values = {'author': 'Niklas Volbers',
                       'calories': 1024,
                       'comment': 'no comment',
                       'skill': 'easy'}        
        self.recipe = Recipe(**self.values)


    def test_string(self):       
        set = lambda v: self.recipe.set(author=v)
        self.assert_(set, 'Joerg')
        self.assertRaises(ValueError, set, None)
        self.assertRaises(ValueError, set, 5)
        self.assertRaises(ValueError, set, 5.2)

        set = lambda v: self.recipe.set(comment=v)
        self.assert_(set, 'Joerg')
        self.assert_(set, None)

    def test_mapping(self):
        set = lambda v: self.recipe.set(skill=v)

        self.recipe.set(skill='advanced')
        print self.recipe.skill, self.recipe.skill_
        return
        # mapped values must be identical
        self.assert_(self.recipe.set, skill='difficult')
        v1 = self.recipe.skill
        v1_ = self.recipe.skill_

        self.assert_(set, 1)
        v2 = self.recipe.skill
        v2_ = self.recipe.skill_

        self.assertEqual(v1, v2)

        # however, the raw values should stay the same
        self.assertEqual(v1_, 'easy')
        self.assertEqual(v2_, 1)
        

    def test_on_update(self):
        print "ingredients = ", self.recipe.ingredients

        def on_update(sender, updateinfo):
            print "ingredients has changed: ", updateinfo            
        self.recipe.ingredients.on_update = on_update

        def on_update_element(sender, key, value):
            print "item of recipe has changed: ", key, value
        self.recipe.on_update = on_update_element
        
        i = self.recipe.ingredients
        i.append( Ingredient(name="garlic") )
        self.recipe.ingredients = []
        pass
        #print self.recipe.get_values()
        #print self.recipe.__class__.__dict__



if __name__ == "__main__":
    unittest.main()
    
    
        
