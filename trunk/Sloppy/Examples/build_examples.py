
import Sloppy
Sloppy.init()

from Sloppy.Base.dataset import *
from Sloppy.Base.objects import *
from Sloppy.Base.project import *
from Sloppy.Base.projectio import *
from Sloppy.Base.dataio import read_table_from_file

import logging
logging.basicConfig()

def demo_zno():

    ds = Dataset(key = "Zn10Abs1")
    ds.data = read_table_from_file("Data/sample_data_01.dat", "ASCII", delimiter='\s*')

    tbl = ds.data
    tbl.column(0).set_values('key', 'Wavelength', 'label', 'Wavelength (nm)')
    tbl.column(1).set_values(key='Absorption', designation = 'Y', label='Optical Absorption (arb. units)')
    
    layer = Layer(type='line2d',
                  lines=[Line(source=ds)],
                  xaxis = Axis(label="Wavelength [nm]"),
                  yaxis = Axis(label="Absorption [a.u.]"))
                          
    pl = Plot(title=u"Optical Absorption of ZnO Quantum Dots",
              layers=[layer], key=ds.key)
    
    spj = Project(plots=[pl], datasets=[ds])

    save_project(spj, 'example_01.spj')


if __name__ == "__main__":
    demo_zno()
