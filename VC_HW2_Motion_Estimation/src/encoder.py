#!/usr/bin/env python3
"""HW2 advanced student encoder. Implement inter-frame encoding yourself.

REQUIRED CLI (TA grader calls this exactly):
python encoder.py --reference REF.png --current CUR.png \
  --method full_search|four_step_search|four_step_rdo --output OUT.bin

This file is intentionally unfinished; code structure may be changed, but not
CLI, bitstream syntax, RDO objective, HW1 transform tables, or image semantics.
"""
import argparse


def encode(reference, current, method, output):
    # TODO: 16x16 macroblock loop; Q1/Q2 use only one 16x16 MV;
    # Q3 tries both one 16x16 MV and four independent 8x8 MVs;
    # Q3 RDO via reconstructed SSD + 64 * (macroblock syntax bits);
    # ALL Q1/Q2/Q3 ME searches: MAD ONLY; no MVD bit cost during MV selection.
    # MVD is still Signed Exp-Golomb coded and written for every chosen MV.
    # For Q3 only, block-size RDO uses SSD + 64 * actual macroblock syntax bits.
    # write mode+MVD+four HW1 coded residuals per macroblock;
    # write 4-byte big-endian valid payload bits header, final zero padding.
    raise NotImplementedError('Implement HW2 Advanced encoder and bitstream')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--reference', required=True)
    p.add_argument('--current', required=True)
    p.add_argument('--method', required=True, choices=['full_search', 'four_step_search', 'four_step_rdo'])
    p.add_argument('--output', required=True)
    a = p.parse_args()
    encode(a.reference, a.current, a.method, a.output)


if __name__ == '__main__':
    main()
