# This file is part of SloppyPlot, a scientific plotting tool.
# (C)opyright Niklas Volbers 2005.

__all__ = ['Application', 'app',
           'Dataset', 'Project',
           'Plot', 'Axis', 'Layer', 'Line',
           'Table']

from Sloppy.Base.application import Application, test_application

from Sloppy.Base.dataset import Dataset
from Sloppy.Base.objects import Line, Layer, Axis, Plot
from Sloppy.Base.project import Project
from Sloppy.Base.table import Table

from Sloppy.Base.dataio import read_table_from_file
import Numeric


# set up Application
print "Setting up Application object 'app'."
app = test_application()

