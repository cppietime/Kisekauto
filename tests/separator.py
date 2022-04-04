'''
kisekauto/separator.py
c Yaakov Schectman 2022

A utility to split codes into components
'''

import argparse
import sys
from os import path

from kisekauto import imagegen

def main(argv):
    parser = argparse.ArgumentParser(description='A utility to split codes into components')
    parser.add_argument('-s', '--save', nargs='*', help=
        '''A list of specifiers with characters specifying the components to extract,
        optionally followed by a colon and a name to append to the result.
        c - clothes
        u - underwear
        b - body
        f - face
        h - hair
        d - decorations
        e - expression
        p - pose''')
    parser.add_argument('-o', '--outputdir', action='store', nargs='?', help=
        'A prefix path for the output files. End with a / for a directory''')
    parser.add_argument('-i', '--inputdir', required=True, help='The path to the input code file''')
    args = parser.parse_args(argv)
    specfilepath = args.inputdir
    code = imagegen.custom_codes(specfilepath)
    if len(code) == 0:
        print(f'Failed to load code at {specfilepath}')
        return
    code = code[0]
    for speccol in args.save:
        split = speccol.split(':')
        spec = split[0]
        retain = set()
        if 'c' in spec:
            retain.add('Clothing')
        elif 'u' in spec:
            retain = retain.union(('Clothing', 'ka', 'kb', 'kc', 'kd', 'ke', 'jc', 'ja', 'jb'))
        if 'e' in spec:
            retain.add('Expression')
        if 'f' in spec:
            retain.add('Face')
        if 'h' in spec:
            retain.add('Hair')
        if 'b' in spec:
            retain = retain.union(('Appearance', 'ca', 'da', 'db', 'dd', 'dh', 'di', 'qa', 'qb', 'dc', 'eh'))
        if 'd' in spec:
            retain = retain.union(('Appearance', 'pb', 'pc', 'pd', 'pe'))
        if 'p' in spec:
            retain.add('Pose')
        newcode = code.copy().filter(retain)
        if len(split) > 1:
            if args.outputdir is None:
                dirname = (lambda x: f'{x[0]}_{split[1]}.kkl')(path.splitext(specfilepath))
            else:
                dirname = f'{args.outputdir}{split[1]}.kkl'
        else:
            if args.outputdir != None:
                dirname = args.outputdir + path.splitext(path.basename(specfilepath))[0]
            else:
                dirname = specfilepath
            dirname = (lambda x: f'{x[0]}_{spec}.kkl')(path.splitext(dirname))
        with open(dirname, 'w') as file:
            file.write(str(newcode))

if __name__ == '__main__':
    main(sys.argv[1:])