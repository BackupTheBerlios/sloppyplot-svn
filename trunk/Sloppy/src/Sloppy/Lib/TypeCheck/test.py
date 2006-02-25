
# just some hand-written testing

import testcases
from defs import *
from typecheck import *

recipe = testcases.Recipe()
recipe2 = testcases.Recipe()

print "Author documentation:", recipe._descr['author'].doc

dl = DictionaryLookup(recipe._descr)
print "Author documentation:", dl.author.doc

#recipe.author = Undefined

print recipe.calories

def on_update(sender, key, value):
    print "on update of ", sender
    print "  ", key, "=", value
recipe.on_update = on_update

recipe.author = "Niklas Volbers"
recipe2.author = "Fred Weasley" # should not emit an update notification


print "\n=== LIST ===\n"
I = lambda name: testcases.Ingredient(name=name)
testcases.Ingredient.__repr__ = lambda self:  ">%s<" % self.name


def on_update_list(sender, updateinfo):
    print "list update: ", updateinfo
recipe.ingredients.on_update = on_update_list

# should emit a list update
recipe.ingredients.append( testcases.Ingredient(name="Butter") )

# should emit an update
recipe.ingredients = []

# should still emit a list update, because TypedList objects are persistent.
recipe.ingredients.append( testcases.Ingredient(name="Garlic") )


recipe.ingredients += [I('onion'), I('salt')]
del recipe.ingredients[1:2]
recipe.ingredients.append(I('sugar'))
recipe.ingredients.pop()
recipe.ingredients[1] = I('olive oil')

recipe.ingredients.reverse()

print "\n=== DICT ===\n"

def on_update_dict(sender, updateinfo):
    print "dict update: ", updateinfo
recipe.reviews.on_update = on_update_dict

recipe.reviews = {}
recipe.reviews['Niklas'] = 'pretty good'
recipe.reviews.update( {'Niklas':'ok', 'Leopold':'disgusting food'} )
del recipe.reviews['Niklas']
recipe.reviews.popitem()


recipe.reviews.copy()

print "\n=== A Complicated Dict ===\n"

class Timeline(HasDescriptors):
    years = Dict( values=String(), doc="Years and their events")


tl = Timeline(years={1974: 'some date', 2002: 'some other date'})

print tl.years

tl.years['2006'] = 'today' # '2006' can be converted to the integer 2006
print tl.years

# this fails:
#tl.years['0BC'] = 'this year does not exist anyway' # '0BC' cannot be casted

view = View(tl)
# print "descr.years.doc", view.descr.years.doc
# print "descr.years.doc", view.descr['years'].doc
# print "years:", view.values.years
# print "years:", view.values['years']
# print "keys:", view.values

#print "possible to copy the dict?"
#cd = tl.__class__(**tl.get_values())
#print "cd has the following values:", cd.get_values()


