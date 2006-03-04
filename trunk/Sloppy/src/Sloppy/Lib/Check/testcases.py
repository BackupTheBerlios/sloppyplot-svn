
# test fixture -- preparing and cleaning up: TestCase.setUp(), TestCase.tearDown()
# test case -- simple single test
# test suites -- test cases or suites that should run together
# test runner -- graphical/textual representation of the test

from checks import *
import unittest

class Ingredient(HasChecks):
    name = String()
    
class Recipe(HasChecks):
    author = String(strict=True, doc="Name of the author")
    calories = Integer()
    comment = String(required=False)
    skill = Mapping({'easy':1, 'intermediate':2, 'advanced':3}, raw=True)
    category = Choice(['breakfast', 'lunch', 'dinner', 'snack'])
    is_tested = Bool()
    ingredients = List(Instance('Ingredient'))
    reviews = Dict(keys=String(), values=String())
        
class CheckTestCase(unittest.TestCase):

    def setUp(self):
        self.values = {'author': 'Niklas Volbers',
                       'calories': 1024,
                       'comment': 'no comment',
                       'skill': 'easy'}        
        self.recipe = Recipe(**self.values)


    def test_string(self):       
        set = lambda v: self.recipe.set(author=v)
        self.assert_(set, 'Joerg')
        self.assertRaises(ValueError, set, None)
        self.assertRaises(ValueError, set, 5)
        self.assertRaises(ValueError, set, 5.2)

        set = lambda v: self.recipe.set(comment=v)
        self.assert_(set, 'Joerg')
        self.assert_(set, None)

    def test_mapping(self):
        set = lambda v: self.recipe.set(skill=v)

        self.recipe.set(skill='advanced')
        print self.recipe.skill, self.recipe.skill_
        return
        # mapped values must be identical
        self.assert_(self.recipe.set, skill='difficult')
        v1 = self.recipe.skill
        v1_ = self.recipe.skill_

        self.assert_(set, 1)
        v2 = self.recipe.skill
        v2_ = self.recipe.skill_

        self.assertEqual(v1, v2)

        # however, the raw values should stay the same
        self.assertEqual(v1_, 'easy')
        self.assertEqual(v2_, 1)
        

    def test_on_update(self):
        print "ingredients = ", self.recipe.ingredients

        def on_update(sender, updateinfo):
            print "ingredients has changed: ", updateinfo            
        self.recipe.ingredients.on_update = on_update

        def on_update_element(sender, key, value):
            print "item of recipe has changed: ", key, value
        self.recipe.on_update = on_update_element
        
        i = self.recipe.ingredients
        i.append( Ingredient(name="garlic") )
        self.recipe.ingredients = []
        pass
        #print self.recipe.get_values()
        #print self.recipe.__class__.__dict__



if __name__ == "__main__":
    unittest.main()
