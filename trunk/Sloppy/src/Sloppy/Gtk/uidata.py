

uistring_appwindow = 
"""
<ui>
  <menubar name='MainMenu'>
    <menu action='FileMenu'>
      <menuitem action='FileNew'/>
      <menuitem action='FileOpen'/>
      <menu action='RecentFilesMenu'>
        <placeholder name='RecentFilesList'/>
        <separator/>
        <menuitem action='RecentFilesClear'/>            
      </menu>
      <separator/>
      <menuitem action='FileSave'/>
      <menuitem action='FileSaveAs'/>
      <separator/>
      <menuitem action='FileClose'/>
      <menuitem action='Quit'/>
    </menu>
    <menu action='EditMenu'>        
      <menuitem action='Undo'/>
      <menuitem action='Redo'/>
      <separator/>
      <menuitem action='Edit'/>
      <menuitem action='RenameItem'/>          
      <menuitem action='Delete'/>
      <separator/>
      <menuitem action='Preferences'/>
    </menu>
    <menu action='DatasetMenu'>
      <menuitem action='NewDataset'/>   
      <menuitem action='DatasetImport'/>
      <separator/>
      <menuitem action='DatasetToPlot'/>
      <menuitem action='DatasetAddToPlot'/>
    </menu>
    <menu action='PlotMenu'>
      <menuitem action='Plot'/>
      <menu action='PlotBackendMenu'>
         <menuitem action='PlotBackendGnuplot'/>
         <menuitem action='PlotBackendMatplotlib'/>
      </menu>
      <menuitem action='ExportViaGnuplot'/>
      <separator/>
      <menuitem action='NewPlot'/>
      <menuitem action='DatasetToPlot'/>
      <separator/>
      <menuitem action='ExperimentalPlot'/>
    </menu>
    <menu action='ViewMenu'>
      <menuitem action='ToggleToolbox'/>
      <menuitem action='ToggleLogwindow'/>          
      <separator/>
    </menu>        
    <menu action='HelpMenu'>
      <menuitem action='About'/>
    </menu>
  </menubar>
  <toolbar name='MainToolbar'>
    <toolitem action='FileNew'/>
    <toolitem action='FileOpen'/>
    <toolitem action='FileSave'/>
    <separator/>
    <toolitem action='Undo'/>
    <toolitem action='Redo'/>
    <separator/>
    <toolitem action='Quit'/>
  </toolbar>
  <popup name="popup_plot">
    <menuitem action='Plot'/>
    <menu action='PlotBackendMenu'>
       <menuitem action='PlotBackendGnuplot'/>
       <menuitem action='PlotBackendMatplotlib'/>
    </menu>
    <menuitem action='ExportViaGnuplot'/>
    <separator/>
    <menuitem action='Edit'/>
    <menuitem action='RenameItem'/>
    <menuitem action='ViewMetadata'/>        
    <separator/>        
    <menuitem action='Delete'/>
  </popup>
  <popup name="popup_dataset">
    <menuitem action='Edit'/>
    <menuitem action='RenameItem'/>
    <menuitem action='ViewMetadata'/>
    <separator/>      
    <menuitem action='DatasetToPlot'/>
    <menuitem action='DatasetAddToPlot'/>
    <separator/>
    <menuitem action='Delete'/>
    <separator/>
  </popup>
  <popup name="popup_empty">
    <menuitem action='NewDataset'/>
    <menuitem action='NewPlot'/>
  </popup>
</ui>
"""
