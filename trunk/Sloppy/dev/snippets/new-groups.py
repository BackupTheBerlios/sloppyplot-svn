
# Re-implementation of the Group class using the Check classes.

from Sloppy.Lib.Check import *


(MODE_CONSTANT, MODE_CYCLE, MODE_RANGE, MODE_CUSTOM) = range(4)

        
class Group(HasChecks):
    """

    """
    
    check = Instance(Check)
    allow_override = Bool(init=True, required=True)

    mode = Choice(range(4))
    
    constant_value = Check()

    cycle_list = Check()    

    # TODO: replace with tuple??? or Range???
    # Range(min, max, steps) => but where should these be stored?
    range_start = Float(init=1)
    range_step = Float(init=1)
    range_maxsteps = Integer(init=None)

    on_custom = Check(on_init=lambda o,i:None)

    
    def __init__(self, check, **kwargs):
        HasChecks.__init__(self, check=check)

        # The next checks need to be adjusted so that
        # they do the same type check as the Check
        # that they refer to.
        cview = CheckView(self)
        cview.constant_value = self.check
        cview.cycle_list = List(self.check)

        self.set(**kwargs)


    def get(self, obj, index, override_value=Undefined, mode=None):
        """ Return the group value for the object `obj` at position `index`.

        `override_value` should be the value to use if the group allows an override.
        Otherwise the group determines the value from the given `obj`, `index`
        and `mode`.  If no mode is given, then the preset mode is used.

        TODO: It is not possible to specify an override value of None!
        """

        if override_value is not Undefined and self.allow_override is True:
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
    class TestContainer(HasChecks):
        an_int = Integer()
        a_string = String()

        group_int = Group(an_int)

        
    tc = TestContainer(an_int=5, a_string="Niklas")

    tc.group_int.set(constant_value=7,
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
    
