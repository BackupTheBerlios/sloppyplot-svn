
"""
This example illustrates setting and getting values via the Property
mechanism.
"""

from cookbook import *


def main():
    r = SimpleRecipe(name=5.0, difficulty=3)

    for k in r._props.keys():
        v = getattr(r, k)
        print "%12s : %s (%s)" % (k, v, type(v))
    


if __name__ == "__main__":
    print globals()['__doc__']
    main()
    
