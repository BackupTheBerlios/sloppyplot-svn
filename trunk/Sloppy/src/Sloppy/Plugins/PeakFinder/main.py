
""" The peak finding functions were designed after the PeakListDialog
from LabPlot!  """


def find_peaks(data_x, data_y, threshold, accuracy):
    """
    data_x, data_y = 1-d array with x and y coordinates
    threshold = y range
    accuracy = x range

    Returns list of found peaks (x,y).
    """
    xmin, xmax = 0, 1
    ymin, ymax = 0, 1

    peaks = []
    for i in range(len(data_x)):

        j = 1
        peak_found = False
        while j <= accuracy:
            # test to the left side
            if i-j > 0:
                if (data_y[i] > data_y[i-j]+threshold) and \
                   (data_y[i] > data_y[i-1]) and \
                   (data_y[i] > data_y[i+1]):                    
                    peak_found = True
                    break

            # test to the right side:
            if i+j < len(data_y):
                if (data_y[i] > data_y[i+j]+threshold) and \
                   (data_y[i] > data_y[i-1]) and \
                   (data_y[i] > data_y[i+1]):                    
                    peak_found = True
                    break
            j+=1

        if peak_found is True:
            x, y = data_x[i], data_y[i]
            peaks.append((x,y))

            if len(peaks) == 1:
                xmin = xmax = x
                ymin = ymax = y
            else:
                xmin = min(x, xmin)
                xmax = max(x, xmax)
                ymin = min(y, ymin)
                ymax = max(y, ymax)

    return peaks




# This is my own work...
def match_patterns(datax, datay, patterns, xerr=0.2, yerr=0.2):    
    """ Identify a pattern (=a list of x-values with corresponding
    relative intensities) from a list of x/y values.

    xerr, yerr are relative error for each mass position and
    relative error for each isotopic intensity. """
    
    # check all patterns
    for key, pattern in patterns.iteritems():
        print "Checking ", key
        matches =  [] # list of indices that best fit the isotopic x-values
        for refx, abundancy in pattern:
            match_err = xerr+0.1
            match_index = None

            i = 0
            for x in datax:
                deltax = abs(x-refx)
                rel_err = deltax
                if rel_err < match_err:
                    match_err = rel_err
                    match_index = i
                i+=1

            # if nothing was found for this isotope, abort the pattern
            if match_index is None:
                break
            else:
                ##print "Closest match: ", datax[match_index]
                matches.append(match_index)
        else:
            # found a value for each isotope! Now compare the intensities
            ##print "Found matches for all isotopes!"

            # calculate total intensity y
            y = 0
            for index in matches:
                y += datay[index]
                ##print "sum is ", y
            
            # now see if the actual ratio of the y-value/y-total does not
            # differ from the theoretical isotopic abundancies more than
            # the given yerr.

            # collect abundancies
            i = 0
            for refx, abundancy in pattern:
                yvalue = datay[matches[i]]
                i += 1
                
                ratio = yvalue/y
                ##print "ratio is %s and should be %s" % (ratio, abundancy)
                delta = abs(ratio - abundancy)
                rel_err = delta/abundancy
                ##print "relative error", rel_err
                if rel_err > yerr:
                    break
            else:
                print "Found Element ", key
                i = 0
                for index in matches:
                    print "   %.2f  (%.2f%%, should be around %.2f%%)" % (datay[index], (datay[index]/y)*100, (pattern[i][1])*100)
                    i +=1
                print
            


if __name__ == "__main__":
    import numpy
    
    # assume that the isotopes are ordered by decreasing abundance
    patterns = {
        'Li': [(7.0, 1)],
        'Zn': [(63.0, 0.70), (65.0, 0.20), (67.0, 0.10)]
        }
    
    
    data = [(0.0, 27),
            (6.1, 270),
            (6.97, 1300),
            (23.0, 4500),
            (60.1, 10000),
            (62.9, 38000),
            (65.1, 12000),
            (66.8, 4100)]

    a = numpy.array(data, 'f4,f4')
    match_patterns(a['f1'], a['f2'], patterns)

