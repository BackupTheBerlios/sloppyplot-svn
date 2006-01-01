
from Sloppy.Lib.Props.props import HasProperties, Property, List
from Sloppy.Lib.Props.common import *

    

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
