
"""
Experimental module for an extended HasProps class.
"""



from Sloppy.Lib.Props import *

#------------------------------------------------------------------------------
# SLOPPYOBJECT
#

class SloppyObject(HasProps):

    def __init__(self, *args, **kwargs):
        HasProps.__init__(self, *args, **kwargs)
        self.parent = None

    def get_root(self):
        if self.parent is None:
            return self.parent
        else:
            return self.parent.get_root()


    def detach(self):
        self.parent = None

    def attach(self, sobject):
        if self.parent is not None:
            raise RuntimeError("SloppyObject %s already has a parent (%s) and cannot be reassigned to %s!"
                               % (self, self.parent, sobject) )
        else:
            self.parent = sobject

    

    def __setattr__(self, key, value):
        if key in ('_props','_values'):
            raise RuntimeError("Attributes '_props' and '_values' cannot be altered for HasProps objects.")
        
        prop = object.__getattribute__(self, '_props').get(key,None)
        if prop is not None and isinstance(prop, Prop):
            # detach old object from self            
            old_value = self._values[key]
            if isinstance(old_value, SloppyObject):
                old_value.detach()
            else:
                old_value = None

            try:
                # set new value via meta_attribute
                # (this ensures value checking)
                prop.meta_attribute(key).__set__(self, value)
            except:
                # if something went wrong, reattach to self if necessary
                if old_value is not None:
                    old_value.attach(self)
                raise

            # attach new value to self
            if isinstance(value, SloppyObject):
                value.attach(self)

        else:
            object.__setattr__(self, key, value)


    def tree(self, indent=0):
        rv = [self.__class__.__name__]
        for key, value in self.get_values().iteritems():
            if isinstance(value, SloppyObject):
                rv.append("  %s:" % key)
                rv.append(value.tree(indent+4))
            else:
                rv.append("  %s: %s" % (key, value))

        return "\n".join(rv)
            

#==============================================================================
class PseudoDataset(SloppyObject):
    # a pseudo-Dataset object, which just illustrates how to disable
    # the attach/detach mechanism!
    def attach(self, parent): return
    def detach(self): return


   
class Ingredient(HasProps):
    name = pString()
    amount = pString()
    
class Recipe(SloppyObject):
    first_ingredient = Prop(CheckType(Ingredient))
    second_ingredient = Prop(CheckType(Ingredient))
    third_ingredient = Prop(CheckType(Ingredient))
    a_list = pList(CheckType(str, Ingredient))
    
    
so = Recipe(first_ingredient = Ingredient(name='garlic', amount='2 cloaves'),
            second_ingredient = Ingredient(name='butter', amount='10 tblspoons'),
            a_list = ['Niklas', 'Annekatrin'])

so.a_list.append(Ingredient(name="Water",amount="100 ml"))

print so.first_ingredient
print so.second_ingredient
print so.a_list

so.first_ingredient = so.second_ingredient

#print so.first_ingredient.parent

print so.tree()
