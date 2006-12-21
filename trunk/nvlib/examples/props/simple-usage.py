
"""
This example illustrates setting and getting values via the Property
mechanism. The attributes of a SimpleRecipe are set in a number of
different ways and are then retrieved.
"""

from cookbook import *


def main():
    print globals()['__doc__']
    
    # set prop values during initialization
    r = SimpleRecipe(name=5.0, difficulty=3)

    # set using attribute notation
    r.author = "Niklas"
    
    # or use the 'set' method
    r.set(date_entered='2006-12-21')
    r.set('comment', 'very tasty!')


    # retrieve all prop values
    for k in r._props.keys():
        v = getattr(r, k)
        print "%12s : %s (%s)" % (k, v, type(v))
    


if __name__ == "__main__":
    main()
    
