from Sloppy.Lib.Props import Prop, Container


class TupleRangeProp(Prop):

    def __init__(self,length,default=None,types=None, blurb=None,doc=None):
        self.length = length
        self.default = default or tuple([None for i in range(length)])
        Prop.__init__(default=default,types=types,blurb=blurb,doc=doc)
    
    def check_type(self, val):        
        
        if val is None:
            return self.default

        if isinstance(val,(list,tuple)) and len(val) == self.length:
            lrange, rrange = val
        else:
            val = str(val)

            if val.find(':') > -1:
                lrange,rrange = val.split(':')
            else:
                lrange = val
                rrange = None

            if isinstance(lrange,basestring):
                lrange = int(lrange)
            if isinstance(rrange,basestring):
                rrange = int(rrange)

        # type checking
        if lrange is not None and not isinstance(lrange,int):
            raise TypeError("Left Range must be None or an integer (was %s,%s)" % (lrange, type(lrange)))
        if rrange is not None and not isinstance(rrange, int):
            raise TypeError("Right Range must be None or an integer (was %s,%s)" % (rrange,type(rrange)))
                    
        # debugging
        print lrange, rrange

        return val


class mycontainer(Container):    
    myindex = TupleRangeProp(length=2,types=int)



mc = mycontainer(myindex='5:1')
mc.myindex = 5
mc.myindex = 10,5
#mc.myindex = 'Niklas',1

