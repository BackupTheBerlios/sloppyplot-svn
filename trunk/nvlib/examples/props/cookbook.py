
""" Sample classes for props examples. """

from nvlib.props import HasProperties, vprop, validators


class SimpleRecipe(HasProperties):

    name = vprop(validators.String())
    difficulty = vprop(validators.Integer())
    author = vprop(validators.String())
    date_entered = vprop(validators.String())
    comment = vprop(validators.String())


