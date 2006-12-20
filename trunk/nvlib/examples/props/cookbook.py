
""" Sample classes for props examples. """

from nvlib.props import HasProperties, vprop, validators


class SimpleRecipe(HasProperties):

    name = vprop(validators.String())
    difficulty = vprop(validators.Integer())



