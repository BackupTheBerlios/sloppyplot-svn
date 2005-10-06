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

        def add_tab(key, label, object):
            tree = gtk.glade.XML('./Glade/layer_editor.glade', key)
            tabwidget = tree.get_widget(key)

            cf = pwglade.ConnectorFactory()
            connectors = cf.create_from_glade_tree(object, tree)
            pwglade.check_in(connectors)

            nb_main.append_page(tabwidget)
            nb_main.set_tab_label_text(tabwidget, label)

            self.tabs.append(tabwidget)
            self.tablabels.append(label)

            
        add_tab('tab-general', 'General', self.layer)
        add_tab('tab-axes', 'Axes', self.layer)
        add_tab('tab-legend', 'Legend', self.layer.legend)


        # if requested, set the page with the name `tab` as current page
        if initial_tab is not None:
            try:
                index = self.tablabels.index(initial_tab)
            except ValueError:
                raise KeyError("There is no Tab with the label %s" % initial_tab)
            nb_main.set_current_page(index)


        btnbox = self._construct_btnbox()
        btnbox.show()

        separator = gtk.HSeparator()
        separator.show()
        
        vbox = gtk.VBox()
        vbox.pack_start(nb_main, True, True)
        vbox.pack_start(separator, False, False, padding=4)
        vbox.pack_end(btnbox, False, False)
        vbox.show()
        self.add(vbox)

        self.notebook = nb_main


    def _construct_btnbox(self):
        box = gtk.HBox()

        btn_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        #btn_cancel.connect("clicked", self.cb_cancel)
        btn_cancel.show()
        
        btn_revert = gtk.Button(stock=gtk.STOCK_REVERT_TO_SAVED)
        #btn_revert.connect("clicked", self.cb_revert)
        btn_revert.show()

        btn_apply = gtk.Button(stock=gtk.STOCK_APPLY)
        #btn_apply.connect("clicked", self.cb_apply)
        btn_apply.show()        

        btn_ok = gtk.Button(stock=gtk.STOCK_OK)
        #btn_ok.connect("clicked", self.cb_ok)
        btn_ok.show()

        box.pack_start(btn_revert, False, True)
        
        box.pack_end(btn_ok, False, True, padding=2)
        box.pack_end(btn_apply, False, True, padding=2)
        box.pack_end(btn_cancel, False, True, padding=2)
        
        return box
        

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
    
