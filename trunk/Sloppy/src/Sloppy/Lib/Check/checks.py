# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL$
# $Id$


import inspect
from containers import TypedList, TypedDict
from defs import Undefined, CheckView, EventView

__all__ = ['Undefined', 'Integer', 'Float', 'Bool', 'Boolean',
           'String', 'Unicode', 'Keyword',
           'Instance', 'List', 'Dict', 'Choice', 'Mapping', 'HasChecks',
           'AnyValue', 'Check',
           'CheckView', 'EventView',
           'values_as_dict']


#------------------------------------------------------------------------------

class Check(object):

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
        self.on_init = kwargs.pop('on_init', lambda obj, key: init)        
        
        self.__dict__.update(kwargs)

    def __call__(self, value):
        return self.check(value)

    def check(self, value):
        " overwrite this method for your own custom check. "
        return value
    
    def get(self, obj, key):
        try:
            return obj.__dict__['_values'][key]
        except KeyError:
            return Undefined

    def set(self, obj, key, value):
        try:
            obj.__dict__['_values'][key] = self.check(value)
            if self.raw is True:
                obj.__dict__['_raw_values'][key] = value
        except ValueError, msg:
            raise ValueError("Value (%s) for attribute '%s' is invalid, it %s." % (value, key, msg))


class AnyValue(Check):
    def check(self, value):
        return value

   
class TypeCheck(Check):

    def __init__(self, _type, _init, _typename, **kwargs):
        self.min = kwargs.pop('min', None)            
        self.max = kwargs.pop('max', None)            
        self.strict = kwargs.pop('strict', False)            
        self.required = kwargs.pop('required', False)

        if self.required is False:
            if kwargs.has_key('init') is False:
                kwargs['init'] = _init
        self._type = _type
        self._typename = _typename

        Check.__init__(self, **kwargs)

    def check(self, value):

        if value is None:
            if self.required is False:
                return None
            else:
                raise ValueError("is required and may not be None")

        if self.strict is True:
            if not isinstance(value, self._type):       
                raise ValueError("must be %s" %  self._typename)
        else:
            try:
                value = self._type(value)
            except ValueError:
                raise ValueError("cannot be converted to %s" % self._typename)

        if (self.min is not None and value < self.min):
            raise ValueError("must be at least %s" % self.min)
        if  (self.max is not None and value > self.max):
            raise ValueError("may be at most %s" % self.max)

        return value


class Integer(TypeCheck):
    def __init__(self, **kwargs):
        TypeCheck.__init__(self, int, 0, 'an integer', **kwargs)
        
class Float(TypeCheck):
    def __init__(self, **kwargs):
        TypeCheck.__init__(self, float, 0.0, 'a float', **kwargs)

class Boolean(TypeCheck):
    def __init__(self, **kwargs):
        TypeCheck.__init__(self, bool, None, 'a boolean value', **kwargs)

    def check(self, value):
        # if checking is not strict, allow any string like
        # "FaLs", "FALSE", "TRUe", "T", ...
        if isinstance(value, basestring) and self.strict is False:
            v = value.lower()
            if "false".startswith(v):
                return False
            elif "true".startswith(v):
                return True
        else:
            return TypeCheck.check(self, value)
        
Bool = Boolean


# TODO: these might contain regular expressions
class Unicode(TypeCheck):
    def __init__(self, **kwargs):
        TypeCheck.__init__(self, unicode, None, 'an unicode string', **kwargs)
class String(TypeCheck):
    def __init__(self, **kwargs):
        TypeCheck.__init__(self, str, None, 'a string', **kwargs)

# TODO:
Keyword = String

class Choice(Check):

    def __init__(self, choices, **kwargs):
        self.choices = choices
        if kwargs.has_key('init') is False:
            if len(choices) > 0:
                kwargs['init'] = choices[0]
        Check.__init__(self, **kwargs)
        
    def check(self, value):
        if value in self.choices:
            return value
        else:
            raise ValueError("must be one of %s" % str(self.choices))

class Mapping(Check):

    def __init__(self, mapping, **kwargs):
        self.mapping = mapping
        Check.__init__(self, **kwargs)        
            
    def check(self, value):
        if value in self.mapping.values():
            return value
        elif value in self.mapping.keys():
            return self.mapping[value]
        else:
            raise ValueError("must be one of %s or one of %s" %  (str(self.mapping.keys()), str(self.mapping.values())))


class Instance(Check):

    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.required = kwargs.get('required',False)
        Check.__init__(self, **kwargs)

    def check(self, value):
        if value is None:
            if self.required is False:
                return None
            else:
                raise ValueError("is required and may not be None")

        # self.instance may be a class or the name of a class
        # in the first case we use isinstance() for the check,
        # in the second case we compare the class names.
        if inspect.isclass(self.instance):
            if isinstance(value, self.instance):
                return value
            else:
                raise ValueError("must be an instance of %s" % self.instance.__name__)
        else:
            if value.__class__.__name__ == self.instance:
                return value
            else:
                raise ValueError("must be an instance of %s" % self.instance)
            


def analyze_check_object(obj):
    """ Return a valid Check instance.

    - obj is a Check => return obj
    - obj is an uninitialized Check class => return obj()
    - obj is another class object => return Instance(obj)

    Everything else raises a TypeError.    
    """

    if isinstance(obj, Check):
        return obj
    elif inspect.isclass(obj):
        if issubclass(obj, Check):
            return obj()
        else:
            return Instance(obj)
    else:
        raise TypeError("unknown check")
    
    
class List(Check):

    def __init__(self, check=AnyValue, **kwargs):        
        self._check = analyze_check_object(check)
            
        if kwargs.has_key('on_init') is False and \
           kwargs.has_key('init') is False:
            kwargs['init'] = []
        Check.__init__(self, **kwargs)

    def set(self, obj, key, value):        
        # Container objects like the 'List' should not simply replace
        # their item (the TypedList), because these might contain an
        # on_update notification.

        # Therefore, unless the current value is Undefined, we check
        # the value and then simply set the list items of the
        # existing TypeDict.
        
        cv = self.check(value)
        try:
            v = self.get(obj, key)
        except KeyError:
            v = Undefined

        if v is Undefined:
            obj.__dict__['_values'][key] = cv
        else:
            v.set_data(cv.data)


    def check(self, value):
        if isinstance(value, TypedList):
            value._check = self._check
            return value
        elif isinstance(value, list):
            return TypedList(self._check, value)
        else:
            raise TypeError("a list.")


class Dict(Check):

    def __init__(self, values=AnyValue, keys=AnyValue, **kwargs):
        self.key_check = analyze_check_object(keys)
        self.value_check = analyze_check_object(values)
        
        if kwargs.has_key('on_init') is False and \
           kwargs.has_key('init') is False:
            kwargs['init'] = {}

        Check.__init__(self, **kwargs)

    def set(self, obj, key, value):
        # see the comments on List.set
        cv = self.check(value)
        try:
            v = self.get(obj, key)
        except KeyError:
            v = Undefined

        if v is Undefined:
            obj.__dict__['_values'][key] = cv           
        else:
            v.set_data(cv.data)
            
    def check(self, value):
        if isinstance(value, TypedDict):
            value.value_check = self.value_check
            value.key_check = self.key_check
            return value
        elif isinstance(value, dict):
            return TypedDict(self.key_check, self.value_check, value)
        else:
            raise TypeError("a dict.")


#------------------------------------------------------------------------------
class HasChecks(object):
    
    def __init__(self, **kwargs):

        # Initialize check dict and on_update slot
        object.__setattr__(self, '_checks', {})
        object.__setattr__(self, '_values', {})
        object.__setattr__(self, '_raw_values', {})        
        object.__setattr__(self, 'on_update', lambda sender, key, value: None)
        
        # We need to iterate over all Check instances and
        # set default values for them.
        
        # To support inheritance, we need to take all base classes
        # into account as well. To give meaningful error messages, we
        # reverse the order and define the base class checks
        # first.
        
        klasslist = list(self.__class__.__mro__[:-1])
        klasslist.reverse()

        checks = {}
        for klass in klasslist:
            for key, item in klass.__dict__.iteritems():
                if isinstance(item, Check):
                    # TESTING: It is possible to redefine checks defined by base classes
                    ##if checks.has_key(key):
                    ##    raise KeyError("%s defines Check '%s', which has already been defined by a base class!" % (klass,key))
                    checks[key] = item

                    if kwargs.has_key(key):
                        value = kwargs.pop(key)
                    else:
                        value = item.on_init(self, key)

                    if value is not Undefined:
                        item.set(self, key, value)
                        
        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)

        # check retrieval
        self._checks = checks


    def __getattribute__(self, key):
        check = object.__getattribute__(self, '_checks')
        if check.has_key(key):
            return check[key].get(self, key)
        return object.__getattribute__(self, key)

    def __setattr__(self, key, value):
        checks = self._checks
        if checks.has_key(key):
            checks[key].set(self, key, value)
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
        returns a list of values if more than one name is given.
        The keyword argument 'default' may be given as a value
        to be displayed for Undefined values.
        """
        
        default = kwargs.pop('default', Undefined)
        checks = self._checks
        if len(keys) == 1:
            value = checks[keys[0]].get(self, keys[0])
            if value is Undefined:
                value = default
            return value
        else:
            values = []
            for key in keys:
                value = checks[key].get(self, key)
                if value is Undefined:
                    value = default
                values.append(value)
            return values





def values_as_dict(obj, keys, default=None):
    rv = {}
    for key in keys:
        rv[key] = obj.get(key, default=default)
    return rv
