from props import *
import unittest



class DummyClass:
    " Used for testing recipe.weak_reference. "
    pass

class Recipe(HasProps):
    name = Prop(Coerce(unicode))
    ingredients = pDict(CheckType(str))
    difficult = pBoolean()
    keyword = pKeyword()
    year_month = Prop(CheckTuple(2))
    rating = Prop(CheckValid(['gross', 'yummy', 'soso']))
    how_often_cooked = Prop(Coerce(int), CheckBounds(min=0))
    weak_reference = pWeakref(CheckType(DummyClass))
    units = Prop(MapValue({'g':'gramm', 'l':'litre'}))

class SimpleTestCase(unittest.TestCase):  

    def setUp(self):        
        self.dc = DummyClass()
        self.recipe = Recipe()

        

class TestValidity(SimpleTestCase):
              
    def runTest(self):

        testdict = {"flour" : '500 g',
                    "yeast" : 'one portion',
                    "tomatoes" : 'plenty'}
               
        # name
        self.recipe.name = 'Pizza'
        self.assert_(isinstance(self.recipe.name, unicode))        
        self.assertEqual(self.recipe.name,  u'Pizza')

        # ingredients
        self.recipe.ingredients = testdict
        self.assert_(isinstance(self.recipe.ingredients, TypedDict))
        self.assertEqual(self.recipe.ingredients, testdict)
        self.assertNotEqual(self.recipe.ingredients, {})

        # difficult
        self.recipe.difficult = False
        self.assert_(isinstance(self.recipe.difficult, bool))
        self.assertEqual(self.recipe.difficult, False)

        # keyword
        self.recipe.keyword = 'keyword'
        self.assert_(isinstance(self.recipe.keyword, str))
        self.assertEqual(self.recipe.keyword, "keyword")
        
        # year_month
        self.recipe.year_month = (2005,9)
        self.assert_(isinstance(self.recipe.year_month, tuple))
        self.assertEqual(self.recipe.year_month, (2005,9))

        # rating
        self.recipe.rating = 'yummy'
        
        # how_often_cooked
        self.recipe.how_often_cooked = 42.1
        self.assert_(isinstance(self.recipe.how_often_cooked, int))
        self.assertEqual(self.recipe.how_often_cooked, 42)
        p = self.recipe.get_prop('how_often_cooked')
        self.assertEqual(p.boundaries(), (0, None))
        print p.description()

        # weak_reference
        self.recipe.weak_reference = self.dc
        self.assert_(isinstance(self.recipe.weak_reference, DummyClass))
        self.assertEqual(self.recipe.weak_reference, self.dc)
        del self.dc
        self.assertEqual(self.recipe.weak_reference, None)

        # units
        self.recipe.units = 'g'        
        self.assert_(isinstance(self.recipe.units, str))
        self.assertEqual(self.recipe.units, 'gramm')

        self.recipe.units = 'litre'        
        

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
    
            
