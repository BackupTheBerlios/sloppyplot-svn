from props import *
import unittest


class SimpleTestCase(unittest.TestCase):

    def setUp(self):
        
        class Recipe(Container):
            name = Prop(Coerce(unicode))
            ingredients = DictProp(CheckType(str))
            difficult = BoolProp()
            keyword = KeyProp()
            year_month = Prop(CheckTuple(2))
            rating = Prop(CheckValid(['gross', 'yummy', 'soso']))
            how_often_cooked = Prop(Coerce(int), CheckBounds(start=0))
        
        self.recipe = Recipe()

        

class TestValidity(SimpleTestCase):
              
    def runTest(self):

        # assign valid values which
        self.testdict = {"flour" : '500 g',
                         "yeast" : 'one portion',
                         "tomatoes" : 'plenty'}

        self.recipe.name = 'Pizza'
        self.recipe.ingredients = self.testdict
        self.recipe.difficult = False
        self.recipe.keyword = 'keyword'
        self.recipe.year_month = (2005,9)
        self.recipe.rating = 'yummy'
        self.recipe.how_often_cooked = 42.1
        
        # name
        self.assert_(isinstance(self.recipe.name, unicode))        
        self.assertEqual(self.recipe.name,  u'Pizza')

        # ingredients
        self.assert_(isinstance(self.recipe.ingredients, TypedDict))
        self.assertEqual(self.recipe.ingredients, self.testdict)
        self.assertNotEqual(self.recipe.ingredients, {})

        # difficult
        self.assert_(isinstance(self.recipe.difficult, bool))
        self.assertEqual(self.recipe.difficult, False)

        # keyword
        self.assert_(isinstance(self.recipe.keyword, str))
        self.assertEqual(self.recipe.keyword, "keyword")
        
        # year_month
        self.assert_(isinstance(self.recipe.year_month, tuple))
        self.assertEqual(self.recipe.year_month, (2005,9))

        # rating

        # how_often_cooked
        self.assert_(isinstance(self.recipe.how_often_cooked, int))
        self.assertEqual(self.recipe.how_often_cooked, 42)



class TestInvalidity(SimpleTestCase):

    def runTest(self):

        set = self.recipe.set_value

        
        # name
        self.assertRaises(TypeError, set('name',10))

        # why does this not work?
        ## rating
        ##self.assertRaises(ValueError, set('rating', "don't know"))

        ## how_often_cooked
        #self.assertRaises(ValueError, set('how_often_cooked', -1))
        

if __name__ == '__main__':
    unittest.main()
    
            
