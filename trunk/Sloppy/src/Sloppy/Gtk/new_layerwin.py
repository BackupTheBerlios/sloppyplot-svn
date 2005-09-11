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

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/layerwin.py $
# $Id: layerwin.py 124 2005-09-11 13:40:54Z niklasv $


import logging
logger = logging.getLogger('Gtk.layerwin')


try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk, gtk.glade

import pwglade
from Sloppy.Lib.Props.Gtk import pwconnect



class LayerWindow(gtk.Window):

    """
    The LayerWindow allows to edit the properties of a plot layer.
    Different aspects of the layer are grouped as tabs in a notebook
    widget.  Changes are not applied immediately but only when you
    confirm your changes.    
    """

    def __init__(self, app, plot, layer=None, initial_tab=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(550, 500)

        self.app = app
        self.plot = plot
        if layer is not None:
            self.layer = layer
        else:
            self.layer = self.plot.layers[0]

        self.set_title("[Edit Plot Layer]")

        #
        # init UI
        #
        
        # list of tabs with a check_in/check_out method
        self.tabs = []
        self.tablabels = []
        
        nb_main = gtk.Notebook() ; nb_main.show()        
        nb_main.set_property('tab-pos', gtk.POS_LEFT)

        # tabs: general
        tree = gtk.glade.XML('./Glade/layer_editor.glade', 'tab-general')        
        tabwidget = tree.get_widget('tab-general')
        tabwidget.show()

        cf = pwglade.ConnectorFactory()
        connectors = cf.create_from_glade_tree(self.layer, tree)
        pwglade.check_in(connectors)

        nb_main.append_page(tabwidget)
        nb_main.set_tab_label_text(tabwidget, "Layer")

        self.tabs.append(tabwidget)
        self.tablabels.append("General")

        # if requested, set the page with the name `tab` as current page
        if initial_tab is not None:
            try:
                index = self.tablabels.index(initial_tab)
            except ValueError:
                raise KeyError("There is no Tab with the label %s" % initial_tab)
            nb_main.set_current_page(index)


        #btnbox = self._construct_btnbox()
        #btnbox.show()

        separator = gtk.HSeparator()
        separator.show()
        
        vbox = gtk.VBox()
        vbox.pack_start(nb_main, True, True)
        vbox.pack_start(separator, False, False, padding=4)
        #vbox.pack_end(btnbox, False, False)
        vbox.show()
        self.add(vbox)

        self.notebook = nb_main
        

import Sloppy
from Sloppy.Base import const
import application

def test():
    const.set_path(Sloppy.__path__[0])
    filename = const.internal_path(const.PATH_EXAMPLE, 'example.spj')
    app = application.GtkApplication(filename)
    plot = app.project.get_plot(0)
    win = LayerWindow(app, plot)
    win.show()
    gtk.main()
    

if __name__ == "__main__":
    test()
    
