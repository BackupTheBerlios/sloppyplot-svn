

TODO: TypedDict now has 'updated', 'added', 'removed' ? But if it was 'updated',
  then we don't know which values were updated, only which keys were. Is that ok? 

TODO: descr.help

TODO: del attribute!
            
# --- compatibility ----

# HasProperties methods:
# - set_value, set_values aka set => set
# - get_value, get_values aka get => get
# - get_prop, get_props -> use obj._descr.items() or DictionaryLookup(obj._descr)
# - get_keys => obj._descr.keys()
    
# - copy => obj.__class__(**obj.__dict__)
# - create_changeset => maybe class that compares two states?




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

Widgets to program:

Bool: checkbox or ComboBox
Choice: ComboBox
Mapping: ComboBox
String/Unicode: Entry
Float/Integer: Entry
Instance: Button





