
from Sloppy.Lib.Props import *


"""
color_iter = layer.groups.new_iter(gp_color)
for line in layer:
    ...
    color = color_iter.advance()

- Saving and Loading
"""    



(MODE_CONSTANT, MODE_CYCLE, MODE_RANGE, MODE_CUSTOM) = range(4)

class Group(HasProperties):
    key = String()
    prop = VP(VInstance(VP),None)
    allow_override = Boolean(True)    

    mode = VP(range(4))
    
    constant_value = Property()

    cycle_list = Property()    

    start = Float(1)
    step = Float(1)
    max_steps = VP(Integer, None)    

    on_custom = VP(default=lambda i:None)

    
    def __init__(self, prop, **kwargs):
        HasProperties.__init__(self, prop=prop)

        self.props.constant_value = self.prop

        self.props.cycle_list = List(self.prop)

        self.set_cycle_list(**kwargs)
        
        
    def get_fixed(self, index):
        return self.constant_value

    def get_cycle(self, index):
        return self.cycle_list[ index % len(self.cycle_list) ]

    def get_increment(self, index):
        if self.max_steps is None:
            return self.start + index * self.step
        else:
            return self.start + (index % self.max_steps) * self.step

    def get_custom(self, index):
        return self.on_custom(index)

    
    def get(self, index):
        mapping = { MODE_CONSTANT: self.get_constant,
                    MODE_CYCLE: self.get_cycle,
                    MODE_INCREMENT: self.get_increment,
                    MODE_CUSTOM: self.get_custom }

        
        return mapping[self.mode](index)



    

def test():
    class TestContainer(HasProperties):
        an_int = Integer()
        a_string = String()

        group_int = Group(an_int)
        
    tc = TestContainer(an_int=5, a_string="Niklas")

    tc.group_int.set_values(constant_value=7,
                            cycle_list=[5,3,1],
                            start=10, step=1,
                            on_custom=lambda i:i**2)

    for i in range(5):
        print "i = ", i
        print "  fixed: ", tc.group_int.get_fixed(i)
        print "  cycle: ", tc.group_int.get_cycle(i)
        print "  increment: ", tc.group_int.get_increment(i)
        print "  custom: ", tc.group_int.get_custom(i)
        


if __name__ == "__main__":
    test()
    
