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


#------------------------------------------------------------------------------
# What about the on_update stuff?  If the Descriptor is independent,
# then it doesn't make sense to let it call on_update.  

# !!! It would make much more sense to let the parent object call
# on_update (i.e. the HasDescriptors class calls on_update, or
# whatever we like).  

# But what about List and Dict? They can be considered top-level
# objects as well, because they contain sub-objects.  So the List/Dict
# must emit its signals itself, independent of any other object!  We
# just need a way to access the List object, so that we can set the
# on_update method.


#------------------------------------------------------------------------------
# TODO: somehow it should be possible to _collect_	
# TODO: update informations...
# TODO: But maybe the problem would be solved if
# TODO: we could improve the signal mechanism
# TODO: to block (and maybe store them for later
# TODO: retrieval) certain signals.
