
import gtk
from Sloppy.Gtk import tools
from Sloppy.Base import globals

class LabelsTool(tools.BackendTool):

    name = "Labels"
    stock_id = gtk.STOCK_EDIT



    def init(self):
        pass
#         self.set_size_request(-1,200)
       
#         #
#         # treeview
#         #
#         model = gtk.ListStore(object)
#         treeview = gtk.TreeView(model)
#         treeview.set_headers_visible(False)
        
#         cell = gtk.CellRendererText()
#         column = gtk.TreeViewColumn('label', cell)

#         def render_label(column, cell, model, iter):
#             label = model.get_value(iter, 0)
#             text = "'%s': (%s,%s) %s" % (label.text, label.x, label.y, label.halign)
#             cell.set_property('text', text)
#         column.set_cell_data_func(cell, render_label)
        
#         treeview.append_column(column)
#         treeview.connect("row-activated", (lambda a,b,c:self.on_edit(a)))
#         treeview.show()

#         #
#         # buttons
#         #

#         buttons = [(gtk.STOCK_ADD, self.on_new),
#                    (gtk.STOCK_REMOVE, self.on_remove),
#                    (gtk.STOCK_EDIT, self.on_edit)]

#         btnbox = uihelper.construct_buttonbox(buttons, labels=False)
#         btnbox.show()        

#         # put everything together
#         self.pack_start(treeview,True,True)
#         self.pack_end(btnbox, False, True)        

#         # save variables for reference and update view
#         self.treeview = treeview        
        

#     def set_layer(self, layer):
#         if layer == self.layer:
#             return
        
#         for cb in self.layer_cblist:
#             cb.disconnect()
#         self.layer_cblist = []
#         self.layer = layer
        
#         if layer is not None:
#             self.layer_cblist.append(
#                 self.layer.sig_connect("update::labels", self.on_update_labels)
#                 )
#         self.on_update_layer()
        
#     #------------------------------------------------------------------------------
        
#     def on_update_layer(self):       
#         model = self.treeview.get_model()        
#         model.clear()
            
#         if self.layer is None:
#             self.treeview.set_sensitive(False)
#             return
#         else:
#             self.treeview.set_sensitive(True)            

#         # check_in
#         for label in self.layer.labels:
#             model.append((label,))


#     def edit(self, label):
#         dialog = options_dialog.OptionsDialog(label)
#         try:           
#             response = dialog.run()
#             if response == gtk.RESPONSE_ACCEPT:
#                 dialog.check_out()
#                 return dialog.owner
#             else:
#                 raise error.UserCancel

#         finally:
#             dialog.destroy()
        
#     #----------------------------------------------------------------------
#     # Callbacks
#     #
    
#     def on_edit(self, sender):
#         self.check_layer()
        
#         (model, pathlist) = self.treeview.get_selection().get_selected_rows()
#         if model is None or len(pathlist) == 0:
#             return
#         project = self.get_data('project')
            
#         label = model.get_value( model.get_iter(pathlist[0]), 0)
#         new_label = self.edit(label.copy())
#         print "new label", new_label, label
#         changeset = label.create_changeset(new_label)
        
#         ul = UndoList().describe("Update label.")
#         changeset['undolist'] = ul
#         uwrap.set(label, **changeset)
#         uwrap.emit_last(self.backend.layer, 'update::labels',
#                         updateinfo={'edit' : label},
#                         undolist=ul)
        
#         logger.info("Updateinfo: documentation = %s" % ul.doc)
#         project.journal.append(ul)
#         logger.info("Journal text: %s" % project.journal.undo_text())

#         self.on_update_layer()
                

#     def on_new(self, sender):
#         self.check_layer()
        
#         label = objects.TextLabel(text='newlabel')
#         self.edit(label)
#         project = self.get_data('project')
            
#         ul = UndoList().describe("New label.")
#         ulist.append(self.layer.labels, label, undolist=ul)
#         uwrap.emit_last(self.layer, "update::labels",
#                         updateinfo={'add' : label},
#                         undolist=ul)
#         project.journal.append(ul)


#     def on_remove(self, sender):
#         self.check_layer()
        
#         (model, pathlist) = self.treeview.get_selection().get_selected_rows()
#         if model is None:
#             return
#         project = self.get_data('project')
#         label = model.get_value( model.get_iter(pathlist[0]), 0)

#         ul = UndoList().describe("Remove label.")
#         ulist.remove(self.layer.labels, label, undolist=ul)
#         uwrap.emit_last(self.layer, "update::labels",
#                         updateinfo={'remove' : label},
#                         undolist=ul)
#         project.journal.append(ul)
        
        
#     def on_update_labels(self, layer, updateinfo=None):
#         self.on_update_layer()


#------------------------------------------------------------------------------
tools.register_tool(LabelsTool)
