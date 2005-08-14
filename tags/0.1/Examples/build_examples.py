
from Sloppy.Base.dataset import *
from Sloppy.Base.objects import *
from Sloppy.Base.project import *
from Sloppy.Base.projectio import *
from Sloppy.Base.dataio import read_table_from_file

def demo_zno():

    ds = Dataset(key = "ZnO-10-Abs1")
    ds.data = read_table_from_file("Data/zn10abs1.abs", "ASCII", delimiter='\t')

    tbl = ds.data
    tbl.column(0).set_values('key', 'Wavelength', 'label', 'Wavelength (nm)')
    tbl.column(1).set_values(key='Absorption', designation = 'Y', label='Optical Absorption (arb. units)')
    
    layer = Layer(type='line2d',
                  lines=[Line(source=ds)],
                  axes = {'x': Axis(label="Wavelength [nm]"),
                          'y': Axis(label="Absorption [a.u.]")})
                          
    pl = Plot(label=u"Optical Absorption of ZnO Quantum Dots",
              layers=[layer], key=ds.key)
    
    spj = Project(plots=[pl], datasets=[ds])

    save_project(spj, 'zno.spj')


if __name__ == "__main__":
    demo_zno()
