
# just some hand-written testing

import testcases

recipe = testcases.Recipe()
recipe2 = testcases.Recipe()

def on_update(sender, key, value):
    print "on update of ", sender
    print "  ", key, "=", value
recipe.on_update = on_update

recipe.author = "Niklas Volbers"
recipe2.author = "Fred Weasley" # should not emit an update notification


#=== LIST ===

def on_update_list(sender, updateinfo):
    print "list update: ", updateinfo
recipe.ingredients.on_update = on_update_list

# should emit a list update
recipe.ingredients.append( testcases.Ingredient(name="Butter") )

# should emit an update
recipe.ingredients = []

# should still emit a list update, because TypedList objects are persistent.
recipe.ingredients.append( testcases.Ingredient(name="Garlic") )



#=== DICT ===
def on_update_dict(sender, updateinfo):
    print "dict update: ", updateinfo
recipe.reviews.on_update = on_update_dict

recipe.reviews = {}
recipe.reviews['Niklas'] = 'pretty good'




