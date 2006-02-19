
import Sloppy
Sloppy.init()

from Sloppy.Base.dataset import *
from Sloppy.Base.objects import *
from Sloppy.Base.project import *
from Sloppy.Base.projectio import *
from Sloppy.Base.dataio import read_dataset_from_file

import logging
logging.basicConfig()

def demo_zno():

    tbl = read_dataset_from_file("data/zno.dat", "ASCII", delimiter='\s*')
    tbl.key = "Zn10Abs1"

    info = tbl.get_info(0)
    info.set_values(key='Wavelength', label='Wavelength (nm)')

    info = tbl.get_info(1)
    info.set_values(key='Absorption', designation = 'Y', label='Optical Absorption (arb. units)')
    
    layer = Layer(type='line2d',
                  lines=[Line(source=tbl,cx=0,cy=1)],
                  xaxis = Axis(label="Wavelength [nm]"),
                  yaxis = Axis(label="Absorption [a.u.]"))
                          
    pl = Plot(title=u"Optical Absorption of ZnO Quantum Dots",
              layers=[layer], key=tbl.key)
    
    spj = Project(plots=[pl], datasets=[tbl])

    save_project(spj, 'zno.spj')


if __name__ == "__main__":
    demo_zno()
