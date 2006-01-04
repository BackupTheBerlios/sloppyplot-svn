
# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL$
# $Id$



##
## TODO:
##
## - undo limit
## - better exceptions (whatever that might mean)
## - UndoInfo.check_info


__all__ = ["NullUndo", "UndoInfo", "Journal", "UndoRedo", "UndoList", "UndoError", "FakeUndoInfo"]

import logging
logger = logging.getLogger('Base.undo')

import UserList


class UndoError(Exception):
    pass



class UndoInfo:
   
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.doc = None
        self.check_info()
        
    def describe(self, description):
        self.doc = description
        return self


    def check_info(self):
        """ Raises L{UndoError} if the UndoInfo is invalid.
        @raises: UndoError
        """
        if self.kwargs.has_key('undolist'):
            raise UndoError("Keyword arguments in undoinfo contain an argument 'undolist'. This is reserved as a keyword and may not be used.")

        # TODO: test if function takes keyword arguments and if it takes 'undolist'
        # TODO: how do I introspect the function's definition ?
        
                
    def execute(self, undolist = []):
        """
        Execute the undo operation by calling the method of the UndoInfo
        object with the given arguments and keyword arguments.

        The undolist returned by the called method is stored in this
        method's argument `undolist`.
        
        Returns the called method's return value.
        
        """

        try:
            if self.func == None:
                return

            old_len = len(undolist)
            self.kwargs.update( {'undolist' : undolist} )
            return_value = self.func(*self.args, **self.kwargs)
            undolist.describe(self.doc)
            if len(undolist) == old_len:
                raise UndoError("Undo list unchanged: No redo information returned by function %s" % str(self.func))                            
            return return_value
        except:
            raise

    def simplify(self):
        if self.func is None:
            return NullUndo()
        else:
            return self
        

    def dump(self, detailed=False, indent=0):
        rv = []
        rv.append("%sUndoInfo: '%s' " % (indent*" ",self.doc))

        if detailed is True:            
            rv.append("  func  : %s" % self.func)
            try:
                if len(self.args) > 0:
                    rv.append("  args  : %s" % self.args)
                if len(self.kwargs) > 0:
                    rv.append("  kwargs: %s" % self.kwargs)
            except TypeError:
                rv.append("  (ERROR DURING CONVERSION)")
        return ('\n'+indent*" ").join(rv)


class NullUndo(UndoInfo):

    def __init__(self):
        UndoInfo.__init__(self, None)
        self.doc = "NullUndo"

    def execute(self, undolist=[]):
        undolist.append(self)
        return None


        
class UndoList( UserList.UserList, UndoInfo ):

    def __init__(self, infos=[]):
        if infos is None:
            infos = []
        if not isinstance(infos, (tuple,list)):
            self.infos = infos
        UserList.UserList.__init__(self, infos)
        UndoInfo.__init__(self, None)

    def check_type(self, item):
        if not isinstance(item, UndoInfo):
            raise TypeError("Item '%s' with type %s should be an UndoInfo instance."
                            % (str(item), type(item)))

        
    def append(self, undoinfo):
        self.check_type(undoinfo)
        UserList.UserList.append(self, undoinfo)


    def execute(self, undolist=[]):
        new_list = UndoList()
        infos = self.data[:]
        infos.reverse()
        logger.debug("Executing undo (%d items)" % len(infos))
        for info in infos:
            doc = info.doc or "(undocumented)"
            logger.debug(" undo:%s" % doc)
            if isinstance(info, UndoInfo):
                info.execute(undolist=new_list)
        logger.debug("EOL")
        undolist.append(new_list.simplify())
        if isinstance(undolist, UndoList):
            undolist.describe(self.doc)

    def simplify(self, preserve_list=False):
        """
        Returns a simplified UndoList.

          - Removes all NullUndo items.          
          - Removes empty UndoList instances.

        If the UndoList can be reduced to a NullUndo and if
        preserve_list is 'false' (default), then NullUndo is returned.

        If the UndoList contained documentation, then this
        documentation is used for the returned object.        
        """
        
        infos = list()
        for info in self.data:
            info = info.simplify()
            if not isinstance(info, NullUndo):
                infos.append(info)

        if preserve_list is False:
            if len(infos) == 0:
                return NullUndo()
            elif len(infos) == 1:
                if self.doc is not None:
                    infos[0].doc = self.doc
                return infos[0]

        return UndoList(infos).describe(self.doc)
        

    def dump(self, detailed=False, indent=0):
        rv = []
        rv.append("%sUndoList (%d UndoInfo objects)" % (indent*" ", len(self.data)) )        
        for info in self.data:
            if isinstance(info, UndoInfo):
                rv.append( info.dump(detailed=detailed, indent=indent+2) )
            else:
                rv.append("%s! Invalid element: %s" % (indent*" ", info))
        return ("\n"+indent*" ").join(rv)

    def clear(self):
        self.data = list()
        

class Journal:

    def __init__(self):        
        self.__undolist = UndoList()
        self.__redolist = UndoList()
        self.on_change = None

    def undo(self):       
        if len(self.__undolist) > 0:
            info = self.__undolist.pop()
            redolist = UndoList()
            return_value = info.execute(redolist)
            self.__redolist.append(redolist.simplify())
            self.has_changed()
            return return_value
        
    def redo(self):
        if len(self.__redolist) > 0:
            info = self.__redolist.pop()
            undolist = UndoList()
            return_value = info.execute(undolist)
            self.__undolist.append(undolist.simplify())
            self.has_changed()
            return return_value

    def add_undo(self, undoinfo):
        if not isinstance(undoinfo, NullUndo):
            self.__undolist.append(undoinfo.simplify())
            self.__redolist = UndoList()
            self.has_changed()

    def append(self, item):
        self.add_undo(item)
               
    def can_undo(self):  return len(self.__undolist) > 0
    def can_redo(self):  return len(self.__redolist) > 0

    def undo_text(self):
        if self.can_undo():
            return self.__undolist[-1].doc
        else:
            return "Nothing"
    def redo_text(self):
        if self.can_redo():
            return self.__redolist[-1].doc
        else:
            return "Nothing"

    def has_changed(self):
        if self.on_change is not None:
            self.on_change(self)
    
    def clear(self):
        self.__undolist = UndoList()
        self.__redolist = UndoList()
        logger.debug("Undo/Redo cleared")
        self.has_changed()
        
    def dump(self, detailed=False, indent=0):
        rv = []
        rv.append( "" )
        rv.append( "Dumping Journal object:" )
        rv.append( "" )
        rv.append( "UndoList `undolist`" )
        rv.append( self.__undolist.dump(detailed=detailed, indent=indent+2) )
        rv.append( "UndoList `redolist`" )
        rv.append( self.__redolist.dump(detailed=detailed, indent=indent+2) )
        rv.append( "" )
        rv = [item for item in rv if item is not None]
        return ("\n"+indent*" ").join(rv)


# for backward compatibility, TBR
UndoRedo = Journal


class FakeUndoInfo(UndoInfo):

    def execute(self, undolist=[]):
        try:
            if self.func == None:
                return
            #self.kwargs.update( {'undolist' : UndoInfo} )
            self.kwargs.pop('undolist', None)
            logger.debug("FakeUndoInfo: executing %s, %s, %s" % (self.func, self.args, self.kwargs))
            return_value = self.func(*self.args, **self.kwargs)            
            undolist.append(NullUndo())
            return return_value
        except:
            raise

        
    
        




