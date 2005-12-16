
from Sloppy.Lib.Props.props import HasProperties, Property, List
from Sloppy.Lib.Props.common import *

    

#------------------------------------------------------------------------------
# TESTING

class Group(HasProperties):
    key = String()

class GroupFixed(Group):
    value = Property()
    
    def __init__(self, container, key):
        Group.__init__(self, key=key)
        self.props.value = Property(container.get_prop(key).check)

class GroupCycle(Group):
    values = List()

    def __init__(self, container, key):
        Group.__init__(self, key=key)
        self.props.values = List(container.get_prop(key).check)
        
        

class TestContainer(HasProperties):
    an_int = Integer()
    a_string = String()


tc = TestContainer(an_int=5, a_string="Niklas")

gf_int = GroupFixed(tc, 'an_int')
gf_string = GroupFixed(tc, 'a_string')

print gf_int.props.value.get_description()
print gf_string.props.value.get_description()

#gf_int.value = 'Annekatrin' # fails
gf_string.value = 5 # o.k., converted to string

gf_int.value = 5
gf_string.value = "Annekatrin"

print gf_int.value
print gf_string.value

print gf_int.props.value
print gf_int.props.value.checks


gc_int = GroupCycle(tc, 'an_int')

gc_int.values = [5,6,7]
print gc_int.values

#gc_int.values = [5,6,'Annekatrin'] # fails
