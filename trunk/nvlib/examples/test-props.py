
from nvlib.props.props import HasProperties, vprop
from nvlib.props import validators


class Recipe(HasProperties):

    name = vprop(validators.String())
    difficulty = vprop(validators.Integer())


def main():
    r = Recipe(name=5.0, difficulty=3)

    for k in r._props.keys():
        v = getattr(r, k)
        print "%12s : %s (%s)" % (k, v, type(v))
    


if __name__ == "__main__":
    main()
    
