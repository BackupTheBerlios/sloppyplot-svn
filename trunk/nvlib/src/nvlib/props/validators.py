# This file is part of nvlib.
# Copyright (C) 2005-2006 Niklas Volbers
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


class Validator(object):

    """ A class that validates or transforms a given value and either
    returns the value on success or
    """
    
    def __call__(self, value, instance=None, key=None):
        return value



class AnyValue(Validator):

    def __call__(self, value, instance=None, key=None):
        return value


class OneOf(Validator):

    def __init__ (self, *validator_list, **kwargs):
        Validator.__init__(self, **kwargs)
        self.required = kwargs.pop('required', False)        
        
        if len(validator_list) == 0:
            raise ValueError("OneOf requires at least one Validator object.")

        self.validator_list = []
        for v in validator_list:
            if inspect.isclass(v):
                if issubclass(v, Validator):
                    v = v()
                else:
                    v = Instance(v)
            else:
                if not isinstance(v, Validator):
                    raise ValueError("Unknown validator object for OneOf.")

            self.validator_list.append(v)


    def __call__(self, value, instance=None, key=None):
        if value is None:
            if self.required is False:
                return None
            else:
                raise ValueError("is required and may not be None")
            
        exceptions = []
        for v in self.validator_list:
            try:
                new_value = v(value, instance=instance, key=key)
            except ValueError, obj:
                exceptions.append(obj)
            else:
                return new_value

        raise ValueError("is not accepted by any of the validators (%s)" % (self.validator_list) )

                        
            
    
        
class TypeValidator(Validator):

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

        Validator.__init__(self, **kwargs)

    def __call__(self, value, instance=None, key=None):

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



class Integer(TypeValidator):
    def __init__(self, **kwargs):
        TypeValidator.__init__(self, int, 0, 'an integer', **kwargs)
        
class Float(TypeValidator):
    def __init__(self, **kwargs):
        TypeValidator.__init__(self, float, 0.0, 'a float', **kwargs)

class Boolean(TypeValidator):
    def __init__(self, **kwargs):
        TypeValidator.__init__(self, bool, None, 'a boolean value', **kwargs)

    def __call__(self, value, instance=None, key=None):
        # if checking is not strict, allow any string like
        # "FaLs", "FALSE", "TRUe", "T", ...
        if isinstance(value, basestring) and self.strict is False:
            v = value.lower()
            if "false".startswith(v):
                return False
            elif "true".startswith(v):
                return True
        else:
            return TypeValidator.__call__(self, value, instance=instance, key=key)
        
Bool = Boolean


# TODO: these might contain regular expressions
class Unicode(TypeValidator):
    def __init__(self, **kwargs):
        TypeValidator.__init__(self, unicode, None, 'an unicode string', **kwargs)
class String(TypeValidator):
    def __init__(self, **kwargs):
        TypeValidator.__init__(self, str, None, 'a string', **kwargs)

# TODO:
Keyword = String
