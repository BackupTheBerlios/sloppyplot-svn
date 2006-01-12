
from Sloppy.Lib.Props import *


(MODE_CONSTANT, MODE_CYCLE, MODE_RANGE, MODE_CUSTOM) = range(4)

class Group(HasProperties):
    prop = VP(VInstance(VP),None)
    allow_override = Boolean(True)    

    mode = VP(range(4))
    
    constant_value = Property()

    cycle_list = Property()    

    range_start = Float(1)
    range_step = Float(1)
    range_maxsteps = VP(Integer, None)    

    on_custom = VP(default=lambda i:None)

    
    def __init__(self, prop, **kwargs):
        HasProperties.__init__(self, prop=prop)

        # The next properties need to be adjusted so that
        # they do the same type check as the Property
        # that they refer to.
        self.props.constant_value = self.prop
        self.props.cycle_list = List(self.prop)

        self.set_values(**kwargs)
        
        
    def get_constant(self, index):
        return self.constant_value

    def get_cycle(self, index):
        return self.cycle_list[ index % len(self.cycle_list) ]

    def get_range(self, index):
        if self.range_maxsteps is None:
            return self.range_start + index * self.range_step
        else:
            return self.range_start + (index % self.range_maxsteps) * self.range_step

    def get_custom(self, index):
        return self.on_custom(index)

    
    def get(self, index, check_first=None, mode=None):
        if check_first is not None and self.allow_override is True:
            return check_first
        
        mapping = { MODE_CONSTANT: self.get_constant,
                    MODE_CYCLE: self.get_cycle,
                    MODE_RANGE: self.get_range,
                    MODE_CUSTOM: self.get_custom }
        
        return mapping[mode or self.mode](index)



    

def test():
    class TestContainer(HasProperties):
        an_int = Integer()
        a_string = String()

        group_int = Group(an_int)

        
    tc = TestContainer(an_int=5, a_string="Niklas")

    tc.group_int.set_values(constant_value=7,
                            cycle_list=[5,3,1],
                            range_start=10, 
                            on_custom=lambda i:i**2)

    for i in range(5):
        print "i = ", i
        print "  constant: ", tc.group_int.get_constant(i)
        print "  cycle: ", tc.group_int.get_cycle(i)
        print "  range: ", tc.group_int.get_range(i)
        print "  custom: ", tc.group_int.get_custom(i)
        


if __name__ == "__main__":
    test()
    
