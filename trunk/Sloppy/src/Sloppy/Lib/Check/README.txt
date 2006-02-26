

TODO: TypedDict now has 'updated', 'added', 'removed' ? But if it was 'updated',
  then we don't know which values were updated, only which keys were. Is that ok? 

TODO: descr.help


USE CASES FOR ACCESSING DESCRIPTORS AND/OR VALUES
=================================================

(1) Iterate over all descriptors incl. their keys:

  for key, descr in obj._descr.iteritems():

(2) Get all keys of an object:

  keys = obj._descr.iterkeys()

(3) Iterate over all values:

  for key in obj._descr.iterkeys():
      value = obj.get(key)

(4) Use a value dictionary to create changesets etc.

  adict = {}
  for key in obj._descr.iterkeys():
      adict[key] = obj.get(key)

  This is the only use case that is complicated enough to be
  put into its own method.  It used to be called get_values,
  but I don't like the name so much.

Another possibility would be to have two dictionaries: _values, _raw_values
and let the object itself set the values, not the Descriptor.

Then we don't need any extra methods to access the value dict, we can
simply iterate over the value dict.  The only problem: we cannot use
the postfix _ notation anymore to access the raw value, unless we translated
it.

I could also rename _descr to _checks and Descriptor to Check (or
Validator again?).

Using this _values dictionary we might even get rid of the Undefined thingy:
__getattribute__ returns Undefined if the object doesn't exist in the Dictionary!

            
# --- compatibility ----

# HasProperties methods:
# - set_value, set_values aka set => set
# - get_value, get_values aka get => get
# - get_prop, get_props -> use obj._descr.items() or DictionaryLookup(obj._descr)
# - get_keys => obj._descr.keys()
    
# - copy => obj.__class__(**obj.__dict__)
# - create_changeset => maybe class that compares two states?

class Changes:

      def __init__(self, initial):

      def compare_to(self, final):


descriptors = _descr => dict of descriptors
values ???? => dict of values (but what about raw values?)
keys ==> list of available keys

view.descriptors
view.values
view.keys


#------------------------------------------------------------------------------
== on_update of List ==

The updateinfo provided by on_update may is a dict that may contain
3 different keys: 'removed', 'added' or 'reordered'

 updateinfo = {'removed': (i, n, items)}

means: n items beginning at index i have been removed and for reference reasons they
 are stored in the list items.

 updateinfo = {'added': (i, n, items)}

means: n items beginning at index i have been added and for reference reasons they
 are stored in the updateinfo.

If both, 'removed' and 'added' are given, then 'removed' should be interpreted first.

If 'reordered' is given, then all elements of the list are unchanged
but their order is changed. This is e.g. the case for
reverse(). 'reordered' is mutually exclusive with all other keys, i.e. if you 
first check for 'reordered', you don't have to check the other two keys.

 updateinfo = {'reordered':-1}

Reordered has no additional arguments at the moment, because I don't
consider that so useful. So to leave open the possibility of
specifying permutations later on, the -1 will be considered a complete
reordering which cannot be tracked.



== on_update of Dict == 











#------------------------------------------------------------------------------
# bool is not like the bool in VP, because strings are not treated properly.
# therefore we would have to check for this in projectio.


#------------------------------------------------------------------------------
# The python class 'object' calls the '__set__' method of the Descriptor
# with the arguments (obj, value).  However the key, i.e. the attribute
# name, is not passed to the Descriptor and it is therefore not possible
# for the descriptor to set the value in the object.

# There are two possible solutions for this problem:
# (1) Overwrite the object.__setattr__ method to not call __set__,
#     but to call set(obj, key, value) of the Descriptor. The
#     Descriptor would be totally indepent of the object that
#     it belongs to and could easily be used more than once!
#     The disadvantage is that I would have to rewrite the __setattr__
#     and the __getattribute__ methods and that might be slower than
#     the pythonic object.

# (2) init the Descriptor and pass the attribute name to the Descriptor.
#     The Descriptor can then use self.key as attribute name.

# Hmmm, I guess I will use the first method; it already worked.



