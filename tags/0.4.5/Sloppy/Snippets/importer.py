
# Test for a new ASCII import based on regular expressions.

import re


delimiter = {'whitespace': '\s*',
             'tab' : '\t'}

def import_ascii(fd):

    # TBR
    typecodes = 'ff'
    ncols = len(typecodes)
    delimiter = '\s*'
    header_lines = 34
    
    # skip header lines if requested
    while header_lines > 0:
        line = fd.readline()
        header_lines -= 1
    
    
    expmap = {'number' : '([-+]?[\d.]+)',
              'string' : '(\".*?\")',
              'bol' : '\s*',
              'eol' : '\s*$',
              'delimiter' : delimiter}
    
    tcmap = {'d' : expmap['number'],
             'f' : expmap['number']}

    if len(typecodes) > 1:
        regexp = [tcmap[tc] for tc in typecodes]
    else:
        regexp = [tcmap[typecodes] for n in range(ncols)]
                  
    regexp = expmap['bol'] + expmap['delimiter'].join(regexp) + expmap['eol']
    cregexp = re.compile(regexp)
    print
    print regexp
    print

    skipcount = 0
    
    row = fd.readline()        
    while len(row) > 0:
        print "Evaluating ", row,
        matches = cregexp.match(row)
        if matches is None:
            print "Line skipped"            
            skipcount += 1
            if skipcount > 100:
                print "--WARNING--"
                skipcount = 0
        else:
            print matches.groups()

        row = fd.readline()        

#------------------------------------------------------------------------------

# open file for testing

fd = open('test.xps', 'r')


try:
    import_ascii(fd)
finally:
    fd.close()
