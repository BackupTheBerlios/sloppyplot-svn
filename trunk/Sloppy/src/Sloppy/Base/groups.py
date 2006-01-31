
from Sloppy.Lib.Props import *


(MODE_CONSTANT, MODE_CYCLE, MODE_RANGE, MODE_CUSTOM) = range(4)

        
class Group(HasProperties):
    """

    """
    
    prop = VP(VInstance(VP),None)
    allow_override = Boolean(True)

    mode = VP(range(4))
    
    constant_value = Property()

    cycle_list = Property()    

    # TODO: replace with tuple??? or Range???
    # Range(min, max, steps) => but where should these be stored?
    range_start = Float(1)
    range_step = Float(1)
    range_maxsteps = VP(Integer, None)

    on_custom = VP(default=lambda o,i:None)

    
    def __init__(self, prop, **kwargs):
        HasProperties.__init__(self, prop=prop)

        # The next properties need to be adjusted so that
        # they do the same type check as the Property
        # that they refer to.
        self.props.constant_value = self.prop
        self.props.cycle_list = List(self.prop)

        self.set_values(**kwargs)


    def get(self, obj, index, override_value=None, mode=None):
        """ Return the group value for the object `obj` at position `index`.

        `override_value` should be the value to use if the group allows an override.
        Otherwise the group determines the value from the given `obj`, `index`
        and `mode`.  If no mode is given, then the preset mode is used.

        TODO: It is not possible to specify an override value of None!
        """

        if override_value is not None and self.allow_override is True:
            return override_value
        
        mapping = { MODE_CONSTANT: self.get_constant,
                    MODE_CYCLE: self.get_cycle,
                    MODE_RANGE: self.get_range,
                    MODE_CUSTOM: self.get_custom }

        return mapping[mode or self.mode](obj, index)

    #----------------------------------------------------------------------
    # get method implementations
    #
        
    def get_constant(self, obj, index):
        return self.constant_value

    def get_cycle(self, obj, index):
        return self.cycle_list[ index % len(self.cycle_list) ]

    def get_range(self, obj, index):
        if self.range_maxsteps is None:
            return self.range_start + index * self.range_step
        else:
            return self.range_start + (index % self.range_maxsteps) * self.range_step

    def get_custom(self, obj, index):
        return self.on_custom(obj, index)






    

def test():
    class TestContainer(HasProperties):
        an_int = Integer()
        a_string = String()

        group_int = Group(an_int)

        
    tc = TestContainer(an_int=5, a_string="Niklas")

    tc.group_int.set_values(constant_value=7,
                            cycle_list=[5,3,1],
                            range_start = 10,
                            on_custom=lambda obj,i:i**2)

    for i in range(5):
        print "i = ", i
        print "  constant: ", tc.group_int.get_constant(tc, i)
        print "  cycle: ", tc.group_int.get_cycle(tc, i)
        print "  range: ", tc.group_int.get_range(tc, i)
        print "  custom: ", tc.group_int.get_custom(tc, i)
        


if __name__ == "__main__":
    test()
    
