#!/usr/bin/python2

from __future__ import print_function

import sys
import string
import os
import argparse
import subprocess

from utils.lexer import lex
from utils.syntax import synt
from utils.gen import find_vars, gen_code
from utils.const import NAMES

VERSION = (0,1)

def print_tree(t, n=0, f=sys.stdout):
    if isinstance(t,list):
        for x in reversed(t):
            print_tree(x, n, f=f)
    elif isinstance(t,tuple):
        if t[0] in NAMES:
            print("--"*n, NAMES[t[0]], file=f)
        else:
            print("--"*n, t[0], file=f)
        print_tree(t[1], n=n+1, f=f)
    else:
        print("--"*n,t, file=f)

def print_header():
    print("pyCompiler %d.%d" % VERSION)
    print('-------------------')

def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--simple', action='store_true')
    parser.add_argument('file', metavar="FILE", type=str)
    parser.add_argument('-l', '--lex', action="store_true")
    parser.add_argument('-s', '--synt', action="store_true")
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-c', '--asm', action="store_true")
    parser.add_argument('-no', '--no-optimize', action="store_true")

    print_header()

    args = parser.parse_args()
    #print(args)

    fl = args.file

    parts = fl.split('.')
    parts[-1] = 'lex'
    lex_file = string.join(parts,'.')

    parts[-1] = 'synt'
    tree_file = string.join(parts,'.')

    parts[-1] = 'asm'
    asmfile_name = string.join(parts,'.')

    parts[-1] = 'o'
    ofile_name = string.join(parts,'.')

    parts[-1] = 'bin'
    binfile_name = string.join(parts,'.')

    try:
        if args.verbose: print("Lexical analysis: ", end="")
        lex_l = lex(file(fl).read())
        if args.lex:
            lexf = open(lex_file, 'w')
            print(lex_l, file=lexf)
            lexf.close()
        if args.verbose: print("Done")
        
        if args.verbose: print("Syntax analysis: ", end="")
        tree = synt(lex_l)
        if args.synt:
            tree_f = open(tree_file, 'w')
            print(tree, file=tree_f)
            print_tree(tree, f=tree_f)
        if args.verbose: print("Done")

        if args.verbose: print("Find variables and strings: ", end="")
        stat = find_vars(tree)

        if args.synt:
            print("vars =", stat.vars, file=tree_f)
            print("strs =", stat.strs, file=tree_f)
            tree_f.close()
        if args.verbose: print("Done")

        if args.verbose: print("Generate NASM code: ", end="")
        asmfile = open(asmfile_name, 'w')
        gen_code(tree, os.path.basename(fl), stat, f=asmfile)
        asmfile.close()
        if args.verbose: print("Done")

        # stdout = sys.stdout if args.verbose else None
        
        if args.verbose: print("Compiling: ", end="")
        params = ["nasm","-f", "elf", "-o", ofile_name, '-O2' if not args.no_optimize else '', '-l', '1.txt', asmfile_name]
        try:
            if args.verbose: print('\n', ' '.join(params))
            res = subprocess.check_output(params)
        except subprocess.CalledProcessError:
            print("NASM Error!", file=sys.stderr)
            print(res)
            sys.exit(-1)
        if args.verbose: print("Done")

        # sleep(1)

        if args.verbose: print("Linking: ", end="")
        params = ["ld", '-s',  "-lc", '-dynamic-linker', '/lib/ld-linux.so.2', '-o', binfile_name, ofile_name]

        try:
            if args.verbose: print('\n', ' '.join(params))
            res = subprocess.check_output(params)
        except subprocess.CalledProcessError:
            print("ld Error!", file=sys.stderr)
            print(res)
            sys.exit(-1)
        if args.verbose: print("Done")

    except IOError:
        print("ERROR: File not found", file=sys.stderr)
        sys.exit(-1)

if __name__ == '__main__':
    main()