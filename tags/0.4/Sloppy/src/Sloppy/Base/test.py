from Sloppy.Lib.Props import Prop, Container




class mycontainer(Container):


    def check_type(self, val):        

        if val is None:
            return self.default

        val = str(val)

        print "Value is ", val, " and type is ", type(val)

        index = val.find(':')
        if index > -1:
            colindex = val[:index]
            index = val[index+1:]
        else:
            colindex = val
            index = None

        # check index

        # debugging
        print colindex, index

        return val

    
    myindex = Prop(types=check_type,default=None)



mc = mycontainer(myindex='hallo:1')
mc.myindex = 5

