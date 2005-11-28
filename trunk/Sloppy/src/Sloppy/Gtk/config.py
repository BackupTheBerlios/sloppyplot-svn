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

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/application.py $
# $Id: application.py 309 2005-11-24 20:29:55Z niklasv $


"""
Configuration dialog and widgets.
"""


import gtk
from Sloppy.Base import dataio

import uihelper, pwglade


class ConfigurationDialog(gtk.Dialog):

    def __init__(self):

        gtk.Dialog.__init__(self, "Configuration", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))

        nb = self.notebook = gtk.Notebook()
        nb.set_property('tab-pos', gtk.POS_LEFT)

        for page in [InformationPage(), ImportTemplatesPage()]:
            nb.append_page(page)
            nb.set_tab_label_text(page, page.title)
            page.check_in()
        
        self.vbox.add(nb)        
        self.set_size_request(640,480)
        self.show_all()

    def run(self):
        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_ACCEPT:
            for page in self.notebook.get_children():
                page.check_out()
        return response
    

class ConfigurationPage(gtk.VBox):

    title = "<blank page>"
    
    def __init__(self):

        gtk.VBox.__init__(self)

        label = gtk.Label()
        label.set_markup("\n<big><b>%s</b></big>\n" % self.title)
        label.set_use_markup(True)

        frame = gtk.Frame()
        frame.add(label)
        
        self.pack_start(frame,False,True)
    
    def check_in(self): pass
    def check_out(self): pass



#------------------------------------------------------------------------------
#
# Page implementations
#
#------------------------------------------------------------------------------



class InformationPage(ConfigurationPage):

    title = "Information"

    def __init__(self):
        ConfigurationPage.__init__(self)

        vbox = gtk.VBox()
        vbox.set_spacing(uihelper.SECTION_SPACING)
        vbox.set_border_width(uihelper.SECTION_SPACING)
        
        label = gtk.Label("Version: xxx")
        label.set_alignment(0.0,0.0)
        vbox.pack_start(label,False,True)

        label = gtk.Label("Whatever: yyy")
        label.set_alignment(0.0,0.0)
        vbox.pack_start(label,False,True)        

        frame = uihelper.new_section("About SloppyPlot", vbox)
        self.add(frame)

        

class ImportTemplatesPage(ConfigurationPage):

    title = "ASCII Import"

    def __init__(self):
        ConfigurationPage.__init__(self)
    
        # We create copies of all templates and put these into the
        # treeview.  This allows the user to reject the modifications
        # (RESPONSE_REJECT).  If however he wishes to use the
        # modifications (RESPONSE_ACCEPT), then we simply need to
        # replace the current templates with these temporary ones.

        # check in
        self.model = gtk.ListStore(str, object, str) # key, object, blurb
        model = self.model # TBR

        # create gui
        tv = gtk.TreeView(model)
        column = gtk.TreeViewColumn("Available Templates")
        cell = gtk.CellRendererText()
        column.pack_start(cell,expand=True)
        column.set_attributes(cell, text=2)
        tv.set_headers_visible(False)
        tv.append_column(column)

        self.treeview = tv

        sw = uihelper.add_scrollbars(tv)

        tv.connect("row-activated", (lambda a,b,c: self.on_edit_item(a)))
                    
        buttons=[(gtk.STOCK_EDIT, self.on_edit_item),
                 (gtk.STOCK_ADD, self.on_add_item),
                 (gtk.STOCK_DELETE, self.on_delete_item)]

        btnbox = uihelper.construct_buttonbox(buttons,
                                              horizontal=False,
                                              layout=gtk.BUTTONBOX_START)
        btnbox.set_spacing(uihelper.SECTION_SPACING)
        btnbox.set_border_width(uihelper.SECTION_SPACING)

        sw.set_border_width(uihelper.SECTION_SPACING)


        hbox = gtk.HBox()
        hbox.pack_start(sw,True,True)
        hbox.pack_start(btnbox,False,True)
        
        self.pack_start(hbox,True,True)
        self.show_all()


    def check_in(self):
        for key,template in dataio.import_templates.iteritems():
            if template.importer_key == 'ASCII':
                self.model.append((key, template.copy(),"%s: %s" % (key, template.blurb)))

    def check_out(self):

        # replace templates by the temporary ones
        templates = {}
        iter = self.model.get_iter_first()
        while iter is not None:
            key = self.model.get_value(iter, 0)
            template = self.model.get_value(iter, 1)
            templates[key] = template
            iter = self.model.iter_next(iter)

            # Note that this is an application specific operation,
            # and there is no undo available for this.
            dataio.import_templates = templates



    def do_edit(self, template, allow_edit=True):
        importer = template.new_instance()

        dlg = gtk.Dialog("Edit Template Options",None,
                         gtk.DIALOG_MODAL,
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                          gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))


        # WHERE IS THE KEY?
        # template doesn't know about its key, so we need to pass the key...
        # _OR_ we would manipulate the key in the list box...
        
        clist1 = pwglade.smart_construct_connectors(template, include=['blurb','extensions','skip_options'])
#        c_key = clist[0] # for reference below
        clist2 = pwglade.smart_construct_connectors(importer, include=importer.public_props)
        clist = clist1 + clist2
        table = pwglade.construct_table(clist)

        if allow_edit is False:
            notice = gtk.Label("This is an internal template\nwhich cannot be edited.")
            dlg.vbox.pack_start(notice,False,True)
            hseparator = gtk.HSeparator()
            dlg.vbox.pack_start(hseparator,False,True)
            for c in clist:
                c.widget.set_sensitive(False)

        dlg.vbox.pack_start(table,True,True)            
        dlg.show_all()

        for c in clist:
            c.check_in()

        try:
            response = dlg.run()

            if response == gtk.RESPONSE_ACCEPT:                
                # check key before checking out 
 #               new_key = c_key.get_data()
 #               print "NEW KEY = ", new_key
                
                # check out                
                for c in clist:
                    c.check_out()

                # move importer data to template
                values = importer.get_values(importer.public_props, default=None)
                template.set_values(defaults=values)                    

        finally:
            dlg.destroy()

        return response


    #
    # Callbacks
    #
    def on_edit_item(self, sender):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            return

        template = model.get_value(iter,1)
        if template.is_internal is True:
            self.do_edit(template, allow_edit=False)
        else:
            self.do_edit(template)

    def on_delete_item(self, sender):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            return            

        template = model.get_value(iter, 1)
        if template.is_internal is True:
            # TODO: error message
            pass
            #self.error_message("This is an internal template that cannot be edited or deleted.")
        else:
            model.remove(iter)


    def on_add_item(self, sender):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            print "INSERT AT BEGINNING"
            # TODO: insert at beginning
            pass
        else:
            key = model.get_value(iter,1)
            print "INSERT AT A POSITION, using the old one as template"
            template = dataio.IOTemplate(importer_key='ASCII')
            response = self.do_edit(template)
            if response == gtk.RESPONSE_ACCEPT:
                model.insert_after(iter, ('key?', template, template.blurb))

