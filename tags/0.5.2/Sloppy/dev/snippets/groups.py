
from Sloppy.Lib.Props import *


"""
color_iter = layer.groups.new_iter(gp_color)
for line in layer:
    ...
    color = color_iter.advance()

- Saving and Loading
"""    




class Group(HasProperties):
    key = String()
    prop = VP(VInstance(VP),None)

    allow_override = Boolean(True)    
    
    def __init__(self, container, key):
        HasProperties.__init__(self, key=key, prop=container.get_prop(key))
        
    def new_iter(self):
        return None

class GroupIter:
    pass




class GroupFixed(Group):
    value = Property()
    
    def __init__(self, container, key, **kwargs):
        Group.__init__(self, container, key=key)
        self.props.value = self.prop
        self.set_values(**kwargs)

    def new_iter(self):
        return GroupFixedIter(self)

class GroupFixedIter(GroupIter):
    def __init__(self, group):
        self._value = group.value
           
    def current(self):
        return self._value
    
    advance = current
    restart = current



    
class GroupCycle(Group):
    values = List()

    def __init__(self, container, key, **kwargs):
        Group.__init__(self, container, key)
        self.props.values = List(self.prop)
        self.set_values(**kwargs)        

    def new_iter(self):
        return GroupCycleIter(self)

class GroupCycleIter(GroupIter):
    def __init__(self, group):
        self._values = group.values
        self._last_index = len(self._values)
        self._index = 0
        
    def restart(self):
        self._index = 0
        return self.current()
        
    def advance(self):
        self._index = (self._index + 1) % self._last_index
        
        return self.current()

    def current(self):
        return self._values[self._index]

    

    
    

class GroupRange(Group):
    start = Property()
    stop = Property()
    step = Property()

    def __init__(self, container, key, **kwargs):
        Group.__init__(self, container, key)
        self.props.start = VP(self.prop)
        self.props.stop = VP(self.prop)
        self.props.step = VP(self.prop)
        self.set_values(**kwargs)

    def new_iter(self):
        return GroupRangeIter(self)
    
            
class GroupRangeIter(GroupIter):

    def __init__(self, group):
        self.group = group
        self.restart()

    def restart(self):
        self._value = self.group.start
        return self._value

    def advance(self):
        new_value = self._value + self.group.step
        if new_value <= self.group.stop:
            self._value = new_value
            return self._value            
        else:
            return self.restart()

    def current(self):
        return self._value
        



class TestContainer(HasProperties):
    an_int = Integer()
    a_string = String()


tc = TestContainer(an_int=5, a_string="Niklas")

gf_int = GroupFixed(tc, 'an_int', value=3)
gf_string = GroupFixed(tc, 'a_string')

#gf_int.value = 'Annekatrin' # fails
gf_string.value = 5 # o.k., converted to string

#gf_int.value = 5
gf_string.value = "Annekatrin"

print gf_int.value
print gf_string.value

print gf_int.props.value
##print gf_int.props.value.checks


iter = gf_int.new_iter()
print iter.current()
print iter.advance()
print iter.advance()
print iter.advance()

####
gc_int = GroupCycle(tc, 'an_int')

gc_int.values = [5,6,7]
print gc_int.values

#gc_int.values = [5,6,'Annekatrin'] # fails

iter = gc_int.new_iter()
print iter.current()
print iter.advance()
print iter.advance()
print iter.advance()


####
gr_int = GroupRange(tc, 'an_int')
gr_int.start = 1
gr_int.stop = 10
gr_int.step = 2

iter = gr_int.new_iter()
print iter.current()
print iter.advance()
print iter.advance()
print iter.advance()
print iter.advance()
print iter.advance()

