
"""

Test of bidirectional interfacing with gnuplot.
Main feature:
  - get variables from (very recent CVS) gnuplot.
  - even allows to wait for a mouse-click and read
    the coordinates back to python
    (thanks to the recent change of gnuplot by Ethan the `pause mouse`
     can be used from a pipe as now - thanks!)

See the gnuplot help,
  - `help mouse` 
  -  help mouse variables`
for further details on the behaviour of `pause mouse`

No capture of stderr (using popen3 should allow this....)

This has only been tested under linux (debian, testing).
I have no idea about M$Windows or Mac.


Version 0.0.1, 31.07.2003, Arnd Baecker
Version 0.0.2, 04.10.2003, Arnd Baecker
Version 0.0.3, 07.01.2004, Arnd Baecker
Version 0.0.4, 12.01.2004, Arnd Baecker

"""

from subprocess import Popen, PIPE, STDOUT
import string

class Gnuplot:
    """Interface to gnuplot."""

    def __init__(self):
        " Create a pipe to gnuplot. "
        # Note that due to 'close_fds=False', we will keep the connection
        # alive until we actively disconnect it.
        # TODO: how do we actually disconnect?        
	p = Popen(["gnuplot"],shell=True,stdin=PIPE,stdout=PIPE,stderr=STDOUT,close_fds=False )
	(self.gpwrite,self.gpout) = (p.stdin, p.stdout)
        self.p = p

    def __call__(self, s):
        """Send string to gnuplot"""

        self.gpwrite.write(s+"\n")
        self.gpwrite.flush()
        
    def getvar(self,var,convert_method=string.atof):
        """
	Get a gnuplot variable. 
	
	Returns a string containing the variable's value or None,
        if the variable is not defined.
	
	You may specify a method to convert the resultant parameter, e.g.
	>>> gp = Gnuplot()
	>>> gp("a = 10")
	>>> gp.getvar("a") # implies string.atof
	>>> gp.getvar("a", string.atof)
	>>> gp.getvar("a", string.atoi)
	>>> go.getvar("a", None) # no conversion -> returns String
        """
        self(" set print \"-\"\n")      # print output to stdout
        self(" if (defined(%s)) print %s ; else print \"None\" \n" % (var,var))
        result=self.gpout.readline()
        self(" set print\n")            # print output to default stderr
        if result[0:4]=="None":
            return None
	elif convert_method is not None:
	    return convert_method(result)
	else:
	    return(result)

    # ----------------------------------------------------------------------
    # COMMANDS

    def cd(self,path):
        self('cd "%s"' % path)

    def reset(self):
        self('reset')

    def set_terminal(self,terminal,options):
        if not terminal:
            self('unset terminal')
        else:
            self('set terminal %s %s' % (terminal,options))

    def set_title(self,label):
        if not label:
            self('unset title')
        else:
            self('set title "%s"' % label)

    def set_mouse(self,bool=True):
        if not bool:
            self('unset mouse')
        else:
            self('set mouse')
            
    # ----------------------------------------------------------------------


def test1():
    gp=Gnuplot()
    gp("set mouse")
    gp("plot sin(x)")
    gp("a=10")
    print "string for `a` as received from gnuplot: ",\
      gp.getvar("a",None)

    print "string for `b` as received from gnuplot: ",\
      gp.getvar("b",None)

    print "a as received from gnuplot, converted to float ",\
      gp.getvar("a")

    # one more test:
    gp("c=11")
    gp("this_command_is_not_known_to_gnuplot_but_no_problem_to_recover_c")
    print "string for `c` as received from gnuplot: ",gp.getvar("c")

    # Even this works now !!!
    gp("set title 'click with the mouse'")
    gp("plot sin(x)")
    print "var=",gp.getvar("a")  
    print "Now get coordinates of a mouse-click:"
    gp("pause mouse 'click with mouse' ")

    print "MOUSE_BUTTON:",gp.getvar("MOUSE_BUTTON")
    print "MOUSE_SHIFT :",gp.getvar("MOUSE_SHIFT")
    print "MOUSE_ALT   :",gp.getvar("MOUSE_ALT")
    print "MOUSE_CTRL  :",gp.getvar("MOUSE_CTRL")
   
    print "Clicked mouse coords: x,y= %f,%f",\
      gp.getvar("MOUSE_X"), gp.getvar("MOUSE_Y")
    print "Clicked mouse coords: x2,y2= %f,%f",\
      gp.getvar("MOUSE_X2"), gp.getvar("MOUSE_Y2")

    #gp("show xrange")
    #gp("show yrange")
    raw_input("")


def test2():
    gp = Gnuplot()
    gp.set_title("Niki")
    gp.set_mouse(False)

    # example on how to catch errors!
    def safe_call(gp, cmd):
        gp.gpout.flush()
        gp(cmd + '; print "<--END-->"')
        result = gp.gpout.readline()
        print "RESULT =",  result

    safe_call(gp, "set mouse")    
    safe_call(gp, "plot sin(x)")
    safe_call(gp, "pause mouse")
#    raw_input("")
    
if __name__=="__main__":
    #test1()
    test2()
