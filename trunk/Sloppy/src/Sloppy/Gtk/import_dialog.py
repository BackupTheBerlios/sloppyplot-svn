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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/application.py $
# $Id: application.py 284 2005-11-18 11:43:31Z niklasv $


"""
"""

import logging
logger = logging.getLogger('gtk.application')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk, gtk.glade
import pango

import uihelper
import pwconnect, pwglade

from Sloppy.Base import dataio
from Sloppy.Lib.Props import pKeyword


#------------------------------------------------------------------------------

class ImportDialog(gtk.Dialog):

    def __init__(self, importer, template_key, filenames=[]):
        gtk.Dialog.__init__(self, "%s Import" % "ASCII", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.filenames = filenames
        self.template_key = template_key

        # actual Importer object
        self.importer = importer
        try:
            self.importer_key = [key for key,value in dataio.ImporterRegistry.iteritems() if value == importer.__class__][0]
        except IndexError:
            raise IndexError("The given importer class %s could not be found in the ImporterRegistry." % importer.__class__)

        #
        # Combos for choosing the Template
        #
        label_importer = gtk.Label()
        label_importer.set_markup("<b>ASCII Import</b>")
        label_importer.set_use_markup(True)
        #label_importer.set_alignment(0,0.5)
        #label_importer.show()

        label_template = gtk.Label("Template: ")
        label_template.set_alignment(0,0.5)
        label_template.show()        

        model = gtk.ListStore(str,str,bool) # key, description, is_sensitive
                
        combo_template = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combo_template.pack_start(cell, True)
        combo_template.add_attribute(cell, 'text', 1)
        combo_template.add_attribute(cell, 'sensitive', 2)

        # separator
        def iter_is_separator(model, iter):
            return model[iter][0] == None
        combo_template.set_row_separator_func(iter_is_separator)
        combo_template.show()
        self.combo_template = combo_template
        
        box_template = gtk.VBox()
        box_template.pack_start(label_template,False,True)
        box_template.pack_start(combo_template,True,True)
        box_template.show()

        topbox = gtk.VBox()
        topbox.pack_start(label_importer)
        topbox.pack_end(box_template)
        topbox.show()
        self.topbox = topbox

        #
        # preview widget
        #
        self.preview = self.construct_preview()
        self.preview.show()
        
        #
        # Options
        #
        optionbox = gtk.VBox()
        self.clist = pwglade.construct_connectors(self.importer)
        options_table = pwglade.construct_table(self.clist)
        options_table.show()
        optionbox.pack_start(self.preview,True,True)
        optionbox.pack_start(options_table,False,True)
        optionbox.show()
        self.optionbox = optionbox
        
        expander = gtk.Expander("Options")
        expander.add(optionbox)
        expander.show()
        self.expander = expander

        def on_activate_expander(expander):
            expanded = expander.get_expanded()
            if expanded is True:
                expander.child.hide_all()
            else:
                expander.child.show_all()
        expander.connect('activate', on_activate_expander)

        #
        # put everything together
        #
        self.vbox.pack_start(self.topbox,False,True)
#        self.vbox.pack_start(self.preview,True,True)        
#        separator = gtk.HSeparator() ; separator.show()
#        self.vbox.pack_start(separator,False,True)
        self.vbox.pack_start(self.expander,False,True)

        # fill combobox
        combo_template.connect('changed', self.on_changed_template_key)
        self.update_combobox(template_key)
        
    def update_combobox(self, new_key):
        model = self.combo_template.get_model()
        model.clear()

        n = 0
        index = -1
        
        # limit available templates to given importer class
        template_keys = [tpl for tpl in dataio.ImporterTemplateRegistry.itervalues() if tpl.importer_key == self.importer_key]
        for key, template in dataio.ImporterTemplateRegistry.iteritems():
            model.append( (key, "%s (%s)" % (key, template.blurb), True) )
            if key == new_key:
                index = n
            n+=1

        # add two entries: add new entry and remove this entry
#        model.append( (None, None, True) ) # = separator
#        model.append( ("__ADD__", "Add new template", True) )
#        model.append( ("__REMOVE__", "Remove current template", False) )

        self.combo_template.set_active(index)
        

    def construct_preview(self):
        if len(self.filenames) == 0:
            return gtk.Label()
        
        view = gtk.TextView()
        buffer = view.get_buffer()
        view.set_editable(False)
        view.show()
        
        tag_main = buffer.create_tag(family="Courier")
        tag_linenr = buffer.create_tag(family="Courier", weight=pango.WEIGHT_HEAVY)

        # fill preview buffer with at most 100 lines
        preview_file = self.filenames[0]
        try:
            fd = open(preview_file, 'r')
        except IOError:
            raise RuntimeError("Could not open file %s for preview!" % preview_file)

        iter = buffer.get_start_iter()        
        try:
            for j in range(1,100):
                line = fd.readline()
                if len(line) == 0:
                    break
                buffer.insert_with_tags(iter, u"%3d\t" % j, tag_linenr)
                try:
                    buffer.insert_with_tags(iter, unicode(line), tag_main)
                except UnicodeDecodeError:
                    buffer.insert_with_tags(iter, u"<unreadable line>\n", tag_main)
        finally:
            fd.close()

        return uihelper.add_scrollbars(view)
        

    def on_changed_template_key(self, combobox):
        key = combobox.get_model()[combobox.get_active()][0]

        if key == '__ADD__':

            # use the current options for the new template
            data = {}
            for connector in self.clist:
                data[connector.key] = connector.get_data()

            print "CREATING NEW TEMPLATE WITH"
            print data
            #template = dataio.IOTemplate(defaults=data)

            # ask for name of new template
            dialog = gtk.Dialog("Enter name of new template", self,
              gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
              (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
               gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

            entry = gtk.Entry()
            entry.show()
            
            dialog.vbox.add(entry)
            
            try:
                response = dialog.run()                
                if response == gtk.RESPONSE_ACCEPT:
                    template_key = entry.get_text()                    

                    # check for valid key
                    if template_key == "":
                        print "Empty key. not added."
                        return
                    
                    if dataio.ImporterTemplateRegistry.has_key(template_key):
                        print "KEY %s ALREADY EXISTS. NOT ADDED." % template_key
                        return
                    
                else:
                    print "NOT ADDED!"
                    return
            finally:
                dialog.destroy()
                                                 
            # create new template
            template = dataio.IOTemplate(importer_key=self.importer_key,
                                         blurb="User Profile",
                                         defaults=data)
            dataio.ImporterTemplateRegistry[template_key] = template

            self.update_combobox(template_key)
            
        else:
            # use template that was picked
            self.template_key = key
            self.check_in()


    def check_in(self):
        # apply template
        template = dataio.ImporterTemplateRegistry[self.template_key]
        self.importer.clear(include=self.importer.public_props)
        self.importer.set_values(**template.defaults.data)

        # check in data
        for connector in self.clist:
            connector.check_in()


    def check_out(self):
        for connector in self.clist:
            connector.check_out()
        



class SimpleImportDialog(gtk.Dialog):
    def __init__(self, template_key=None):
        gtk.Dialog.__init__(self, "Import", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        # create GUI                
        model = gtk.ListStore(str,str) # key, description
        combo_template = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combo_template.pack_start(cell, True)
        combo_template.add_attribute(cell, 'text', 1)
        combo_template.show()
        self.combo_template = combo_template

        checkbutton = gtk.CheckButton("Modify import options...")
        checkbutton.set_active(True)
        checkbutton.show()        
        self.checkbutton = checkbutton
        
        self.vbox.pack_start(combo_template,True,True)
        self.vbox.pack_start(checkbutton,True,True)
        
        # return values are stored here
        self.modify_options = None
        self.template_key = None
        
        # set value
        self.update_combobox(template_key)


    def update_combobox(self, new_key):
        model = self.combo_template.get_model()
        model.clear()

        n = 0
        index = -1
        
        # limit available templates to given importer class
        template_keys = dataio.ImporterTemplateRegistry.iterkeys()
        for key, template in dataio.ImporterTemplateRegistry.iteritems():
            model.append( (key, "%s (%s)" % (key, template.blurb)) )
            if key == new_key:
                index = n
            n+=1

        self.combo_template.set_active(index)

    def run(self):
        response = gtk.Dialog.run(self)

        self.modify_options = self.checkbutton.get_active()
        model = self.combo_template.get_model()
        iter = self.combo_template.get_active_iter()
        if iter is not None:
            self.template_key = model.get_value(iter,0)
        
        return response



###############################################################################
# EVERYTHING ABOVE IS PROBABLY DEPRECATED    

class EditTemplate(gtk.Dialog):

    def __init__(self, key, template):
        gtk.Dialog.__init__(self, "Edit template '%s'" % key, None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.key = key
        self.template = template
        self.importer = dataio.ImporterRegistry[template.importer_key]()
        self.importer.set_values(**self.template.defaults.data)

        #
        # key, blurb and more
        #
        self.entry_key = gtk.Entry() ; self.entry_key.show()
        lbl_key = gtk.Label("Template key:") ; lbl_key.show()
        hbox = gtk.HBox()
        hbox.pack_start(lbl_key) ; hbox.pack_start(self.entry_key) 
        hbox.show()

        self.vbox.add(hbox)

        self.entry_blurb = gtk.Entry() ; self.entry_blurb.show()
        lbl_blurb = gtk.Label("Blurb:") ; lbl_blurb.show()
        hbox = gtk.HBox()
        hbox.pack_start(lbl_blurb) ; hbox.pack_start(self.entry_blurb)
        hbox.show()

        self.vbox.add(hbox)

        sep = gtk.HSeparator() ; sep.show()
        self.vbox.pack_start(sep)
        
        
        #
        # set up connectors
        #
        self.connectors = pwglade.construct_connectors(self.importer)
        table_options = pwglade.construct_table(self.connectors)
        table_options.show()
        self.vbox.add(table_options)

        for c in self.connectors:
            c.check_in()

    def run(self):

        response = None
        
        while 1==1:
            response = gtk.Dialog.run(self)

            if response == gtk.RESPONSE_ACCEPT:
                #
                # check key for validity
                #
                key = self.entry_key.get_text()
                if len(key) == 0:
                    continue

                try:
                    key = pKeyword().check(key)
                except:
                    # logger.error ?
                    print "Key contains invalid characters."
                    continue

                if dataio.ImporterTemplateRegistry.has_key(key) is True:
                    print "Key already exists. Choose another."
                    continue

                # blurb
                blurb = self.entry_blurb.get_text()
                self.template.blurb = blurb

                # TODO: extension_list
                extension_list = ["SPC"]
                self.template.extension_list = extension_list                
                
                # if we came till here, then we can save the template
                for c in self.connectors:
                    c.check_out()

                dataio.ImporterTemplateRegistry[key] = self.template
                print ">>> TEMPLATE SAVED <<<"

            break
            

                       

        return response
        
        
        

class ImportOptions(gtk.Dialog):
    
    def __init__(self, template_key, gladefile=None):
        gtk.Dialog.__init__(self, "Importing %s" % template_key, None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        # create a new importer based on the template
        self.template = dataio.ImporterTemplateRegistry[template_key]
        self.importer = self.template.new_importer()
        
        #
        # set up connectors
        #
        if gladefile is not None:
            tree = gtk.glade.XML(gladefile, 'options')
            widget = tree.get_widget('options')
            self.vbox.add(widget)
            self.connectors = pwglade.construct_connectors_from_glade_tree(self.importer, tree)
        else:
            self.connectors = pwglade.construct_connectors(self.importer)
            table_options = pwglade.construct_table(self.connectors)
            table_options.show()
            self.vbox.add(table_options)

        # add button to save options as template
        btn_save = gtk.Button("Save as template...")
        btn_save.connect("clicked", self.on_btn_save_clicked)
        btn_save.show()
        self.vbox.add(btn_save)
        
        for c in self.connectors:
            c.check_in()
        

    def run(self):
        response = gtk.Dialog.run(self)

        if response == gtk.RESPONSE_ACCEPT:
            for c in self.connectors:
                c.check_out()            

        return response

    def on_btn_save_clicked(self, btn):

        data = {}
        for c in self.connectors:
            data[c.key] = c.get_data()

        key = "new_template"
        template = dataio.IOTemplate(\
            importer_key=self.template.importer_key,
            defaults=data)
        dialog = EditTemplate(key, template)

        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                # if user changed any options, use them
                for c in self.connectors:
                    c.set_container(dialog.importer)
                    c.check_in()
            else:
                # don't do anything if user aborted
                pass                
        finally:
            dialog.destroy()
            

            
        
        
##############################################################################
def test1():
    importer = dataio.ImporterRegistry['ASCII']()
    dlg = ImportDialog(importer, 'ASCII::pfc')
    dlg.run()
    
    print dlg.importer.get_values(include=['header_size'])
    dlg.check_out()
    print
    print dlg.importer.get_values(include=['header_size'])



def test2():
    dlg = SimpleImportDialog('ASCII')
    try:
        dlg.run()
        print "options: ", dlg.modify_options
        print "template key:", dlg.template_key
    finally:
        dlg.destroy()

def test3():
    dlg = ImportOptions("ASCII", gladefile='./Glade/ascii.glade')
    dlg.run()
    print "=> ", dlg.importer.get_values()
    dlg.destroy()    
        
if __name__ == "__main__":
    import Sloppy
    Sloppy.init()

    test3()

