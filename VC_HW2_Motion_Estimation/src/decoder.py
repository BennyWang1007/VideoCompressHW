#!/usr/bin/env python3
"""HW2 advanced student decoder. Reconstruct only from Reference + bitstream.

REQUIRED CLI:
python decoder.py --reference REF.png --input IN.bin \
  --method full_search|four_step_search|four_step_rdo --output OUT.png
"""
import argparse


def decode(reference, encoded, method, output):
    # TODO: parse header and mode bit for each 16x16 macroblock;
    # recover MV via fixed predictor + MVD; decode four residual 8x8 blocks;
    # MC + inverse HW1 transform; round/clip/uint8; save PNG.
    # Do NOT use current/original image in the decoder.
    raise NotImplementedError('Implement HW2 Advanced decoder')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--reference', required=True)
    p.add_argument('--input', required=True)
    p.add_argument('--method', required=True, choices=['full_search', 'four_step_search', 'four_step_rdo'])
    p.add_argument('--output', required=True)
    a = p.parse_args()
    decode(a.reference, a.input, a.method, a.output)


if __name__ == '__main__':
    main()
