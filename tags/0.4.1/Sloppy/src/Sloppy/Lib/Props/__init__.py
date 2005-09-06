
"""
Implementation of class properties with default values, type checking
(and/or coercion) and documentation string.

The following three aspects are performed (in this order) when a value
is assigned to a prop:

  - Type Checking
  - Transformation (type coercion or value transformation)
  - Value Checking

In addition, a Prop may specify extra documentation, using the 'blurb'
and 'doc' keywords.

Similar libraries:

  - BasicProperty (U{http://basicproperty.sourceforge.net/})
  - Traits (URL?)-- part of the mythical Chaco software
  
"""

from props import *
