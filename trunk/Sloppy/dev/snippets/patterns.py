

import numpy


patterns = {
    'Li': [(7.0, 100)],
    'Zn': [(63.0, 70), (65.0, 20), (67.0, 20)]
    }


data = [(0.0, 27),
        (6.1, 270),
        (6.97, 1300),
        (23.0, 4500),
        (60.1, 10000),
        (62.9, 14000),
        (65.1, 38000),
        (66.8, 4100)]


def match_pattern(datax, datay, patterns):
    for key, pattern in patterns.iteritems():
        print "Checking ", key
        # assume that the isotopes are ordered by decreasing abundance
        for x,y in pattern:
            # TODO: find all x-values that are close
            pass


a = numpy.array(data, 'f4,f4')
match_pattern(a['f1'], a['f2'], patterns)

        
    
