
from Sloppy.Lib.Props.props import HasProperties, Property, List
from Sloppy.Lib.Props.common import *


"""
------------------------
I have a new idea for group properties, which would have
a different user interface and would be 100% extensible, in
case there ever were any new line properties:

A Layer has a ListProperty called 'group_properties' or maybe just 'groups',
where each list item is of type 'Group'.  There are subclasses of 'Group' 
which represent the different uses of the group: 'GroupCycle', 'GroupFixed',
'GroupRange', 'GroupFunction'.  Each Group has a function 'create_runner'
which creates a 'GroupRunner' instance with the functions 'reset' and 'next'.

So if a backend e.g. needs to use the color and would like to incorporate
the group properties, it could do so:

gp_color = layer.groups.new_runner(gp_color)
for line in layer:
    ...
    color = gp_color.next()


The idea of such a GroupRunner, which might also be called iterator, is 
independent of the idea of just having 'groups'. The current advantage of the
individual 'GroupLineColor', 'GroupLineStyle', ... is definitely, that we
can individually define what is allowed and what is not.

class GroupLineWidth(HasProperties):
    type = Integer(mapping=MAP['group_type'], reset=GROUP_TYPE_FIXED)
    allow_override = Boolean(reset=True)        
    value = Property(Line.width.check, reset=Line.width.on_default)
    cycle_list = List(Line.width.check)
    range_start = Float(reset=1.0)
    range_stop = Float(reset=None)
    range_step = Float(reset=1.0)

But on the other hand, we need to define all variables, even though
the group type does not allow all types.

LineWidth:
  type = cycle,fixed,range
  ...
 

The value is simple:
  value = Property(prop.check, reset=prop.on_default)

The cycle list as well:
  cycle_list = List(prop.check)

The range only makes sense if we have a numeric value and could actually be expressed as tuple:
  range = Tuple(3, prop.check)
  

(I need to implement the Tuple Property, the Check is already there)

In all three cases we could simply use a variable 'value':

Group:
  property_key  (e.g. 'color')
  value (e.g. 'blue')

the type is defined by the Group subclass.



Some problems I see:
- Saving and Loading

- GroupFixed, ... are classes, so if I want to dynamically change
  the checks for their properties, then I would need to introduce
  dynamic typing, i.e. I need to change the Props of the instance.
  
"""    

#------------------------------------------------------------------------------
# TESTING

class GroupRunner:
    pass

class GroupFixedRunner:
    def __init__(self, value): self.value = value
    def restart(self): pass
    def current(self): return self.value
    next = current
    

class GroupCycleRunner:
    def __init__(self, values):
        self.values = values
        self.last_index = len(values)
        self.index = 0
        
    def restart(self):
        self.index = 0
        
    def next(self):
        if self.index < self.last_index - 1:
            self.index += 1
        return self.current()

    def current(self):
        return self.values[self.index]

    
class Group(HasProperties):
    key = String()
    allow_override = Boolean(True)

    def new_runner(self):
        return None

    

class GroupFixed(Group):
    value = Property()
    
    def __init__(self, container, key, **kwargs):
        Group.__init__(self, key=key)
        self.props.value = Property(container.get_prop(key))
        self.set_values(**kwargs)

    def new_runner(self):
        return GroupFixedRunner(self.value)

class GroupCycle(Group):
    values = List()

    def __init__(self, container, key):
        Group.__init__(self, key=key)
        self.props.values = List(container.get_prop(key))

    def new_runner(self):
        return GroupCycleRunner(self.values)
    

class GroupRange(Group):
    start = Property()
    stop = Property()
    step = Property()

    def __init__(self, container, key):
        Group.__init__(self, key=key)
        self.props.start = Property(container.get_prop(key))
        self.props.stop = Property(container.get_prop(key))
        self.props.step = Property(container.get_prop(key))
        
        

class TestContainer(HasProperties):
    an_int = Integer()
    a_string = String()


tc = TestContainer(an_int=5, a_string="Niklas")

gf_int = GroupFixed(tc, 'an_int', value=3)
gf_string = GroupFixed(tc, 'a_string')

gf_int.value = 'Annekatrin' # fails
gf_string.value = 5 # o.k., converted to string

#gf_int.value = 5
gf_string.value = "Annekatrin"

print gf_int.value
print gf_string.value

print gf_int.props.value
##print gf_int.props.value.checks


runner = gf_int.new_runner()
print runner.current()
print runner.next()
print runner.next()
print runner.next()

####
gc_int = GroupCycle(tc, 'an_int')

gc_int.values = [5,6,7]
print gc_int.values

#gc_int.values = [5,6,'Annekatrin'] # fails

runner = gc_int.new_runner()
print runner.current()
print runner.next()
print runner.next()
print runner.next()


####
gr_int = GroupRange(tc, 'an_int')
gr_int.start = 1
gr_int.stop = 10
gr_int.step = 2

#runner = gr_int.new_runner()
#print runner.current()
#print runner.next()
