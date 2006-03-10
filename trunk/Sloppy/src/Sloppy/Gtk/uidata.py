

uistring_appwindow = \
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
      <menuitem action='DatasetImport'/>      
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
      <menuitem action='Preferences'/>
    </menu>
    <placeholder name='PlotMenu'/>
    <placeholder name='AnalysisMenu'/>    
    <placeholder name='DisplayMenu'/>        
    <menu action='ViewMenu'>
      <menuitem action='ToggleLogwindow'/>
      <menuitem action='ToggleSidepane'/>          
      <separator/>
      <menuitem action='ToggleFullscreen'/>
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
  </toolbar>
</ui>
"""

uistring_mplwidget = \
"""
<ui>    
  <menubar name='MainMenu'>
    <placeholder name='PlotMenu'>
      <menu action='PlotMenu'>
        <menuitem action='Replot'/>
        <separator/>
        <menuitem action='ExportViaMPL'/>
        <menuitem action='ExportViaGnuplot'/>
      </menu>                
    </placeholder>

    <placeholder name='AnalysisMenu'>    
    <menu action='AnalysisMenu'>
      <menuitem action='DataCursor'/>
    </menu>
    </placeholder>
    <placeholder name='DisplayMenu'>    
    <menu action='DisplayMenu'>
      <menuitem action='ZoomRect'/>
      <menuitem action='ZoomIn'/>
      <menuitem action='ZoomOut'/>
      <menuitem action='ZoomFit'/>
      <menuitem action='ZoomAxes'/>          
      <separator/>
      <menuitem action='MoveAxes'/>
      <menuitem action='SelectLine'/>
    </menu>
    </placeholder>
  </menubar>      

  <toolbar name='MainToolbar'>
    <placeholder name='MainToolbarEdit'>
    </placeholder>
    <toolitem action='ZoomRect'/>
    <separator/>              
    <toolitem action='Replot'/>
  </toolbar>
</ui>
"""

uistring_project_view = \
"""
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
"""                      

uistring_datawin = \
"""
 <ui>
   <menubar name='MainMenu'>
     <menu action='DatasetMenu'>
       <menuitem action='EditInfos'/>
       <separator/>
       <menuitem action='Close'/>
     </menu>
     <menu action='AnalysisMenu'>
     </menu>
     <menu action='ColumnMenu'>        
      <menuitem action='ColumnInsert'/>
      <menuitem action='ColumnAppend'/>      
      <menuitem action='ColumnRemove'/>
      <separator/>
     </menu>
     <menu action='RowMenu'>
      <menuitem action='RowInsert'/>
      <menuitem action='RowAppend'/>
      <menuitem action='RowRemove'/>
      <separator/>
    </menu>
   </menubar>              
   <toolbar name='Toolbar'>
     <toolitem action='EditInfos'/>           
     <separator/>
     <toolitem action='RowInsert'/>
     <toolitem action='RowAppend'/>
     <separator/>
     <toolitem action='RowRemove'/>
     <separator/>
   </toolbar>
   <popup name='popup_column'>
     <menuitem action='ColumnInfo'/>
     <menu action='DesignationMenu'>
       <menuitem action='DesignationX'/>
       <menuitem action='DesignationY'/>
       <separator/>
       <menuitem action='DesignationXErr'/>
       <menuitem action='DesignationYErr'/>                    
       <separator/>
       <menuitem action='DesignationLabel'/>
       <menuitem action='DesignationDisregard'/>
     </menu>     
     <separator/>
     <menuitem action='ColumnCalculator'/>
     <separator/>
     <menuitem action='ColumnAppend'/>                          
     <menuitem action='ColumnInsert'/>
     <menuitem action='ColumnRemove'/>
     <separator/>
     <menuitem action='RowInsert'/>
     <menuitem action='RowAppend'/>
     <menuitem action='RowRemove'/>
     <separator/>
   </popup>
 </ui>
 """
