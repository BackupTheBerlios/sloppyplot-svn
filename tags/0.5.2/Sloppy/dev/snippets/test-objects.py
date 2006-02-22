

from Sloppy.Lib.Props import *

class Container(HasProperties):
#    width = VP(FloatRange(0, 10), None, default=None)
    height = FloatRange(0,10)

c = Container()

def dump(validator, indent=0):
    print "  "*indent, validator.__class__.__name__
    indent += 2
    for v in validator.vlist:
        if isinstance(v, ValidatorList):
            dump(v, indent+2)
        else:
            print "  "*indent, v.__class__.__name__

#dump(c.props.width.validator)

print 
dump(c.props.height.validator)

        

