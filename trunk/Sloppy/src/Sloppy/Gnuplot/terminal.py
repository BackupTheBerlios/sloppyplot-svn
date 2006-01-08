# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL$
# $Id$



from Sloppy.Lib.Props import *

import logging
import os.path



class Terminal:
    def build(self, backend): pass
                  


class DumbTerminal(Terminal):

    def build(self, backend):
        return  ["set terminal dumb"]


class XTerminal(Terminal):

    def build(self, backend):
        cmd_list = []
        cmd_list.append( "set mouse" )
        cmd_list.append( 'set terminal X11 enhanced font "arial,15" raise title "%s"' % backend.window_title )        
        return cmd_list

   
class PostscriptTerminal(Terminal, HasProperties):

    mode = VP(\
      ['eps', 'landscape', 'portrait'],
      blurb="mode",
      doc="Output mode"
      )    
    enhanced = VP(\
      ['enhanced', 'noenhanced'],
      blurb="PS mode",
      doc="Enable subscripts, superscripts, mixed fonts"
      )    
    color = VP(\
      ['color','monochrome'],
      blurb="color mode",
      doc="Color mode"
      )
    blacktext = Boolean(\
      blurb="black text only",
      doc="all text in black, even in color mode"
      )
    solid = VP(\
      ['solid', 'dashed'],
      blurb="Line style"
      )
    dashlength = FloatRange(\
      0.0, None,
      blurb="dash length",
      doc = "Scales the length of dashed-line segments"
      )
    linewidth = FloatRange(\
      0.0, None,
      blurb="line width",
      doc = "Scales all linewidths"
      )
    duplexing = VP(\
      ['defaultplex', 'simplex', 'duplex']
      )
    rounded = VP(\
      ['rounded', 'butt'],
      blurb="Cap style",
      doc="Whether line caps and line joins should be rounded"
      )
    fontname = String(\
      blurb="font name",
      doc="Name of a valid PostScript font"
      )
    fontsize = FloatRange(
      0.0, None,
      blurb="font size",
      doc="Size of the font in PostScript points."
      )
    timestamp = Boolean(\
      blurb="add timestamp",
      doc="Whether to add a timestamp"
      )

    public_props = ['mode', 'enhanced',
                    'duplexing', 'fontname', 'fontsize',
                    'solid', 'color', 'rounded', 'timestamp']

    def build_filename(mode, project, plot):
        if mode == 'eps':
            ext = '.eps'
        else:
            ext = '.ps'

            
        return os.path.join(project.get_directory(), plot.key + ext)
    build_filename = staticmethod(build_filename)


    def build(self, backend):
        """
        from the gnuplot help command:

        set terminal postscript {<mode>} {enhanced | noenhanced}
                                {color | colour | monochrome}
                                {blacktext | colortext | colourtext}
                                {solid | dashed} {dashlength | dl <DL>}
                                {linewidth | lw <LW>}
                                {<duplexing>}
                                {rounded | butt}
                                {fontfile [add | delete] "<filename>"}
                                {palfuncparam <samples>{,<maxdeviation>}}
                                {"<fontname>"} {<fontsize>}

        set timestamp
        """

        if self.blacktext is not None: blacktext = ("colortext", "blacktext")[self.blacktext]
        else: blacktext = ""
        
        if self.dashlength is not None: dashlength = "dl %s" % self.dashlength
        else: dashlength = ""

        if self.linewidth is not None: linewidth = "lw %.2f" % self.linewidth
        else: linewidth = ""

        if self.fontname is not None: fontname = '"%s"' % self.fontname
        else: fontname = ""

        cmd_list = []
        cmd_list.append(
            "set terminal postscript %(mode)s %(color)s %(blacktext)s %(solid)s %(dashlength)s %(linewidth)s %(duplexing)s %(rounded)s %(fontname)s %(fontsize)s" % \
            {'mode' : self.mode,
             'color' : self.color,
             'blacktext' : blacktext,
             'solid' : self.solid,
             'dashlength' : dashlength,
             'linewidth' : linewidth,
             'duplexing' : self.duplexing,
             'rounded' : self.rounded,
             'fontname' : fontname,
             'fontsize' : self.fontsize or ""}
            )

        # The output filename is either taken from backend option 'filename',
        # which must be a valid path, or is constructed from the project's
        # directory and the plot's key.
        if backend.options.has_key('filename'):
            filename = os.path.abspath(backend.options['filename'])
        else:
            filename = self.build_filename(self.mode, backend.project, backend.plot)
        cmd_list.append('set output "%s"' % filename)

        # timestamp
        if self.timestamp is not None:
            cmd_list.append("set timestamp")
            
        return cmd_list

    


if __name__ == "__main__":    
    pt = PostscriptTerminal()
    print pt.build()
        
                   



