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
from Sloppy.Base import globals, dataio, version

from Sloppy.Gtk import uihelper, widget_factory
from Sloppy.Lib.Props import Keyword


DS={
'template_immutable':
"<i>This is an internal template\nwhich cannot be edited.</i>"
}


class ConfigurationDialog(gtk.Dialog):

    def __init__(self):

        gtk.Dialog.__init__(self, "Preferences", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_size_request(640,480)

        #
        # frame above notebook that holds the current tab name
        #
        
        self.tab_label= gtk.Label()

        label = self.tab_label
        label.set_use_markup(True)
        topframe = gtk.Frame()
        topframe.add(label)

        def on_switch_page(notebook, page, page_num, tab_label):
            tab = notebook.get_nth_page(page_num)
            text = "\n<big><b>%s</b></big>\n" % tab.title
            tab_label.set_markup(text)

        #
        # construct notebook
        #
        
        self.notebook = gtk.Notebook()

        nb = self.notebook
        nb.set_property('tab-pos', gtk.POS_LEFT)
        nb.connect("switch-page", on_switch_page, self.tab_label)
        
        for page in [InformationPage(), ImportTemplatesPage(), PluginPage()]:
            nb.append_page(page)
            nb.set_tab_label_text(page, page.title)
            # some pages show only information and
            # might not provide a check_in.
            if hasattr(page, 'check_in'): 
                page.check_in()        

        # TODO: This does not work
        nb.set_current_page(0)

        #
        # put everything together
        #
        self.vbox.pack_start(topframe,False,True)
        self.vbox.pack_start(nb,True,True)               
        self.show_all()


    def run(self):
        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_ACCEPT:
            for page in self.notebook.get_children():
                # some pages show only information and
                # might not provide a check_out.
                if hasattr(page, 'check_out'): 
                    page.check_out()
        return response


#------------------------------------------------------------------------------
#
# Page implementations
#
#------------------------------------------------------------------------------



class InformationPage(gtk.VBox):

    title = "Information"

    def __init__(self):
        gtk.VBox.__init__(self)

        vbox = gtk.VBox()
        vbox.set_spacing(uihelper.SECTION_SPACING)
        vbox.set_border_width(uihelper.SECTION_SPACING)

        label = gtk.Label("SloppyPlot - %s" % version.DESCRIPTION )
        label.set_alignment(0.0,0.0)
        vbox.pack_start(label,False,True)
        
        label = gtk.Label("Version: %s" % version.VERSION )
        label.set_alignment(0.0,0.0)
        vbox.pack_start(label,False,True)

        description = gtk.TextView()
        description.set_property('editable', False)
        description.set_property('cursor-visible', False)
        
        description.get_buffer().set_text(version.LONG_DESCRIPTION)
        vbox.pack_start(description,False,True)

        frame = uihelper.new_section("About SloppyPlot", vbox)
        self.add(frame)

        

class ImportTemplatesPage(gtk.VBox):

    title = "ASCII Import"


    (MODEL_KEY, MODEL_OBJECT) = range(2)
    (COLUMN_KEY, COLUMN_BLURB) = range(2)
    
    def __init__(self):
        gtk.VBox.__init__(self)
    
        # We create copies of all templates and put these into the
        # treeview.  This allows the user to reject the modifications
        # (RESPONSE_REJECT).  If however he wishes to use the
        # modifications (RESPONSE_ACCEPT), then we simply need to
        # replace the current templates with these temporary ones.

        # check in
        self.model = gtk.ListStore(str, object) # key, object
        model = self.model # TBR

        #
        # create gui
        #
        # columns should be created in the order given by COLUMN_xxx
        # definitions above.
        tv = gtk.TreeView(model)
        tv.set_headers_visible(True)
        
        cell = gtk.CellRendererText()        
        column = gtk.TreeViewColumn("Key", cell)
        column.set_attributes(cell, text=self.MODEL_KEY)
        column.set_resizable(True)        
        tv.append_column(column)

        def render_blurb(column, cell, model, iter):
            object = model.get_value(iter, self.MODEL_OBJECT)
            blurb = object.blurb or ""
            if object.is_internal:
                blurb += " (immutable)"            
            cell.set_property('text', blurb)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Description", cell)        
        column.set_cell_data_func(cell, render_blurb)
        column.set_resizable(True)
        tv.append_column(column)

        self.treeview = tv

        sw = uihelper.add_scrollbars(tv)

        tv.connect("row-activated", (lambda a,b,c: self.on_edit_item(a,c)))
                    
        buttons=[(gtk.STOCK_EDIT, self.on_edit_item),
                 ('sloppy-rename', self.on_rename_item),
                 (gtk.STOCK_ADD, self.on_add_item),
                 (gtk.STOCK_COPY, self.on_copy_item),
                 (gtk.STOCK_DELETE, self.on_delete_item)]

        btnbox = uihelper.construct_vbuttonbox(buttons)
        btnbox.set_spacing(uihelper.SECTION_SPACING)
        btnbox.set_border_width(uihelper.SECTION_SPACING)

        sw.set_border_width(uihelper.SECTION_SPACING)


        hbox = gtk.HBox()
        hbox.pack_start(sw,True,True)
        hbox.pack_start(btnbox,False,True)
        
        frame = uihelper.new_section("Import Templates", hbox)
        self.add(frame)
        self.show_all()


    def check_in(self):
        for key,template in globals.import_templates.iteritems():
            if template.importer_key == 'ASCII':
                self.model.append((key, template.copy()))

    def check_out(self):

        # replace templates by the temporary ones
        templates = {}
        iter = self.model.get_iter_first()
        while iter is not None:
            key = self.model.get_value(iter, self.MODEL_KEY)
            template = self.model.get_value(iter, self.MODEL_OBJECT)
            templates[key] = template
            iter = self.model.iter_next(iter)

            # Note that this is an application specific operation,
            # and there is no undo available for this.
            globals.import_templates = templates



    def do_edit(self, template, allow_edit=True):
        importer = template.new_instance()

        dlg = gtk.Dialog("Edit Template Options",None,
                         gtk.DIALOG_MODAL,
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                          gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        factorylist = []

        factory1 = widget_factory.CWidgetFactory(template)
        factory1.add_keys('blurb','extensions','skip_options')
        factorylist.append(factory1)
        
        factory2 = widget_factory.CWidgetFactory(importer)
        factory2.add_keys(importer.public_props)
        factorylist.append(factory2)        

        table1 = factory1.create_table()
        table2 = factory2.create_table()
        
        dlg.vbox.pack_start(table1, True, True)
        dlg.vbox.pack_start(gtk.HSeparator(), False, True)
        dlg.vbox.pack_start(table2, True, True)

        for factory in factorylist:
            factory.check_in()

        if allow_edit is False:
            notice = gtk.Label()
            notice.set_markup(DS['template_immutable'])
            dlg.vbox.pack_start(notice,False,True)
            dlg.vbox.pack_start(gtk.HSeparator(), False, True)
            
            for factory in factorylist:
                for c in factory.clist:
                    c.widget.set_sensitive(False)

        dlg.show_all()

        try:
            response = dlg.run()

            if response == gtk.RESPONSE_ACCEPT:                

                # check out
                for factory in factorylist:
                    factory.check_out()

                # move importer data to template
                values = importer.get_values(importer.public_props, default=None)
                template.set_values(defaults=values)                    

        finally:
            dlg.destroy()

        return response


    def input_key(self, key):
        " Let the user enter a valid key.  The given key is always valid. "
        dlg = gtk.Dialog("Rename Template",None, gtk.DIALOG_MODAL,
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                          gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                         
        entry = gtk.Entry()
        entry.set_text(unicode(key))
        entry.set_activates_default(True)

        hint = gtk.Label()
        
        dlg.vbox.add(entry)
        dlg.vbox.add(hint)
        dlg.set_default_response(gtk.RESPONSE_ACCEPT)        
        dlg.show_all()
        
        hint.hide()

        try:
            while True:
                response = dlg.run()
                if response == gtk.RESPONSE_ACCEPT:
                    # check if key itself is valid                
                    new_key = entry.get_text()
                    try:
                        new_key = Keyword().check(new_key)
                    except PropertyError:
                        hint.set_text("Key is invalid. Try again.")
                        hint.show()
                        continue

                    # if key is equal to the suggested key, use it
                    if key == new_key:
                        return key

                    # otherwise check if key does not yet exist
                    model = self.treeview.get_model()
                    iter = model.get_iter_first()
                    while iter is not None:
                        if new_key == model.get_value(iter, self.MODEL_KEY):
                            hint.set_text("Key already exists. Try again.")
                            hint.show()
                            continue
                        iter = model.iter_next(iter)

                    return new_key
                else:
                    break
        finally:
            dlg.destroy()

        return None



    #
    # Callbacks
    #
    def on_edit_item(self, sender, column=None):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            return

        # perform action based on the column clicked on
        if column is not None:
            index = self.treeview.get_columns().index(column)
        else:
            index = self.COLUMN_BLURB
            
        if index == self.COLUMN_KEY:
            key = model.get_value(iter, self.MODEL_KEY)
            new_key = self.input_key(key)
            if new_key is not None:
                model.set_value(iter, self.MODEL_KEY, new_key)
        elif index == self.COLUMN_BLURB:             
            template = model.get_value(iter, self.MODEL_OBJECT)
            self.do_edit(template, allow_edit=not template.is_internal)
        

    def on_rename_item(self, sender):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            return

        key = model.get_value(iter,self.MODEL_KEY)
        new_key = self.input_key(key)

        if new_key is not None:
            model.set_value(iter, self.MODEL_KEY, new_key)
        
    
    def on_delete_item(self, sender):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            return            

        template = model.get_value(iter, self.MODEL_OBJECT)
        if template.is_internal is True:
            pass
            # TODO: print error message, but we need the app for this!
            #self.error_msg("This is an internal template that cannot be edited or deleted.")
        else:
            model.remove(iter)

        

    def on_add_item(self, sender):
        # set up new template        
        template = dataio.IOTemplate(importer_key='ASCII')

        # let user input key
        key = self.input_key("New Template")
        if key is None:
            return

        # edit template
        response = self.do_edit(template)        
        
        if response == gtk.RESPONSE_ACCEPT:
            new_item = (key, template)
            model = self.treeview.get_model()            
            model.append(new_item)

    def on_copy_item(self, sender):
        model,iter = self.treeview.get_selection().get_selected()
        if iter is None:
            return
        source = model.get_value(iter, self.MODEL_OBJECT)

        # set up new template        
        template = dataio.IOTemplate(importer_key='ASCII')
        template.defaults = source.defaults.copy()

        # Let user input key.
        # TODO: We must make sure that the new key is unique!
        key = 'New Template'            
        key = self.input_key(key)
        if key is None:
            return        

        # edit template
        response = self.do_edit(template)        
        
        if response == gtk.RESPONSE_ACCEPT:
            new_item = (key, template)
            model.append(new_item)


class PluginPage(gtk.VBox):

    title = "Plugins"

    def __init__(self):
        gtk.VBox.__init__(self)

        vbox = gtk.VBox()
        vbox.set_spacing(uihelper.SECTION_SPACING)
        vbox.set_border_width(uihelper.SECTION_SPACING)

        #
        # Create informational label
        #
        note = "Custom plugins are not yet supported. "
        label = gtk.Label(note)

        #
        # Create TreeView with the Plugin Information
        #
        
        # model: plugin object
        model = gtk.ListStore(object)
        for plugin in globals.app.plugins.itervalues():
            model.append( (plugin,) )
            
        treeview = gtk.TreeView(model)

        treeview.set_headers_visible(True)

        def add_column(attr):
            cell = gtk.CellRendererText()
            column = gtk.TreeViewColumn(attr, cell)
            column.set_cell_data_func(cell, self.cell_data_func, attr)
            column.set_resizable(True)        
            treeview.append_column(column)

        for attr in ['name', 'blurb']:
            add_column(attr)

        vbox.pack_start(label, False, True)
        vbox.pack_start(treeview, True, True)        

        frame = uihelper.new_section("Available Plugins", vbox)
        self.add(frame)


    def cell_data_func(self, column, cell, model, iter, attr):
        """ Display the attribute plugin.attr """
        plugin = model.get_value(iter, 0)
        try:
            value = plugin.__dict__[attr]
        except KeyError:
            value = ""
        cell.set_property('text', value)
        
