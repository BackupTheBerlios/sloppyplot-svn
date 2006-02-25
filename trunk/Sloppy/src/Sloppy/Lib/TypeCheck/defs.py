
class Undefined:
    def __repr__(self): return "Undefined"



class DictionaryLookup(object):
    """ Helper class to allow access to members of a dictionary.

    >>> mydict = {'One': 1, 'Two': 2}
    >>> dl = DictionaryLookup(mydict)
    >>> print dl.One
    >>> print dl.Two
    """
    
    def __init__(self, adict):
        object.__setattr__(self, '_adict', adict)

    def __getattribute__(self, key):
        adict = object.__getattribute__(self, '_adict')         
        return adict[key]
    __getitem__ = __getattribute__
    
    def __setattr__(self, key, value):
        adict = object.__getattribute__(self, '_adict')
        if adict.has_key(key) is False:
            raise KeyError("'%s' cannot be set, because it doesn't exist yet." % key)
        adict[key] = value
    
    def __str__(self):
        adict = object.__getattribute__(self, '_adict')
        return "Available items: %s" % str(adict)



class View:

    def __init__(self, obj):
        self.obj = obj
        self.refresh()
        
    def refresh(self):
        self.descr = DictionaryLookup(self.obj._descr)
        self.values = DictionaryLookup(self.get_values())                                     

    def get_values(self):
        valuedict = {}
        keys = self.obj._descr.keys()
        for key in keys:
            valuedict[key] = self.obj.get(key)
        return valuedict
    
