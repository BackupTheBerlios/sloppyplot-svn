
""" The peak finding functions were designed after the PeakListDialog
from LabPlot!  """


def find_peaks(data_x, data_y, threshold, accuracy):
    """
    data_x, data_y = 1-d array with x and y coordinates
    threshold = y range
    accuracy = x range

    Returns list of found peaks.
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




