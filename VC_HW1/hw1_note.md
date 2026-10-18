# Video Compression Homework

This repository contains a grayscale 8x8-block DCT image codec. The standard
codec implementation is in [`VC_HW1/`](./VC_HW1/).

## 1. Running the codec

Run the commands below from the repository root. The syntax is POSIX/Bash
syntax and works on Linux, macOS, WSL, and Git Bash on Windows.

### Encoder

```bash
python encoder.py \
  <input_png> \
  <output_bin> \
  --trace <trace_file> \
  --block-index <index>
```

Example:

```bash
python encoder.py \
  lena_gray.png \
  results/lena.bin \
  --trace results/lena_encoder_trace.txt \
  --block-index 0
```

### Decoder

```bash
python3 decoder.py \
  <input_bin> \
  <output_png> \
  [--trace <trace_file>] \
  [--block-index <index>]
```

Example:

```bash
python3 decoder.py \
  results/lena.bin \
  results/lena_reconstructed.png \
  --trace results/lena_decoder_trace.txt \
  --block-index 0
```

### Evaluation

```bash
python3 evaluate.py \
  <original_png> \
  <reconstructed_png> \
  <bitstream_bin>
```

Example:

```bash
python3 evaluate.py \
  lena_gray.png \
  results/lena_reconstructed.png \
  results/lena.bin
```

The encoder and decoder traces intentionally retain the original text format.
Create the results directory before running commands:

```bash
mkdir -p results
```

All generated bitstreams, reconstructed images, traces, and experiment
artifacts belong in [`results/`](./results/).

Install the runtime dependencies if needed:

```bash
python -m pip install numpy pillow
```

## 2. Implemented standard codec

The TODOs in [`encoder.py`](./encoder.py) and
[`decoder.py`](./decoder.py) are implemented:

- Level shifting, two-stage 1D DCT, quantization, coefficient validation, and
  zigzag scanning.
- VALUE(0), signed VALUE amplitudes, and EOB symbol generation.
- MSB-first Huffman-style payload writing and reading.
- Inverse zigzagging, dequantization, two-stage 1D IDCT, level restoration,
  rounding, and clipping to `[0, 255]`.
- Input validation for block sizes, coefficient categories, payload length, and
  trailing padding.

### Huffman coding and token payload format

For a coefficient value `v`, its magnitude category is

$$
\operatorname{category}(v)=
\begin{cases}
0, & v=0,\\
\lfloor\log_2(|v|)\rfloor+1, & v\ne0.
\end{cases}
$$

Amplitude bits use the following representation:

- `VALUE(0)` has no amplitude bits.
- A positive value is written as an unsigned `s`-bit integer.
- A negative value is written as `v + (2^s - 1)` as an unsigned `s`-bit
  integer.
- All bits are written most-significant bit first.

Examples:

| Symbol | Bit pattern |
|---|---|
| `VALUE(0)` | `00` |
| `VALUE(1)` | `010 \| 1` |
| `VALUE(-1)` | `010 \| 0` |
| `VALUE(5)` | `100 \| 101` |
| `VALUE(-2)` | `011 \| 01` |
| `EOB` | `111111111` |

Internal zero coefficients are encoded as `VALUE(0)`. `EOB` is emitted after
the last nonzero coefficient when trailing coefficients are zero. An all-zero
block is represented by `EOB` alone.

## 3. Standard evaluation results

(Note: The evaluation results are obsolete, and the DCT time varies with the Python runtime and CPU.)

The supplied reference traces were reproduced for block index `0`.

| Image | MSE | PSNR | Valid payload bits | BPP |
|---|---:|---:|---:|---:|
| `lena_gray.png` | 17.069725 | 35.808538 dB | 219548 | 0.837646 |
| `mandril_gray.png` | 24.699440 | 34.203933 dB | 381276 | 1.454590 |

## 4. Ablation experiments

The following results were measured on `lena_gray.png`. The temporary
ablation harness used for these measurements is not part of the submission.

### 4.1 Custom quantization table

The standard quantization table was multiplied by `2`.

| Configuration | MSE | PSNR | Payload bits | BPP |
|---|---:|---:|---:|---:|
| Standard table | 17.069725 | 35.808538 dB | 219548 | 0.837646 |
| Table multiplied by 2 | 27.706783 | 33.704943 dB | 149952 | 0.572144 |

A larger quantization step maps more DCT coefficients to zero or to smaller
magnitudes. This produces more short symbols and earlier EOB markers, so the
bitrate decreases. The trade-off is greater quantization error, which increases
MSE and decreases PSNR.

### 4.2 Zigzag scan versus raster scan

The raster configuration traverses coefficients in ordinary row-major order.
The same traversal is used by both encoder and decoder, so reconstruction
quality is unchanged.

| Configuration | MSE | PSNR | Payload bits | BPP |
|---|---:|---:|---:|---:|
| Zigzag scan | 17.069725 | 35.808538 dB | 219548 | 0.837646 |
| Raster scan | 17.069725 | 35.808538 dB | 265342 | 1.012329 |

Zigzag ordering places low-frequency coefficients first and high-frequency
coefficients later. Quantization makes many high-frequency coefficients zero,
so zigzag reaches the trailing zero run earlier and benefits from EOB. Raster
ordering interleaves more nonzero high-frequency coefficients before the final
zeros, increasing the payload without changing the decoded coefficients.

### 4.3 Two-stage 1D DCT versus direct 2D DCT

The direct implementation used the required double summation:

$$
F_{u,v}=\sum_{x=0}^{7}\sum_{y=0}^{7}C_{u,x}f_{x,y}C_{v,y}.
$$

Timing was measured for 8192 blocks (two passes over the 4096 blocks in the
512x512 image), using only the DCT computation.

| Configuration | Time for 8192 blocks | Payload bits | BPP | PSNR |
|---|---:|---:|---:|---:|
| Two-stage 1D DCT | 0.032807 s | 219548 | 0.837646 | 35.808538 dB |
| Direct 2D DCT | 12.668392 s | 219544 | 0.837616 | 35.808498 dB |

The direct method is approximately 386 times slower in this Python
measurement because it performs 64 multiply-accumulate terms for every output
coefficient. The two-stage method reuses matrix operations and therefore has
much less Python-level loop overhead. The tiny payload and PSNR differences
come from floating-point rounding near quantization boundaries; they are
within the grading tolerances.

## 5. Grading policy

- **70%: Standard implementation.** Two public test images and hidden tests
  are used. Compare block index `0` and final evaluation metrics with
  `lena_reference_output.txt` and `mandril_reference_output.txt`.
- **30%: Lab report.** Include the three ablation tables and explanations
  above in the report. Ablation code should not be submitted.

Allowed differences are:

- Floating-point values: `0.01`
- PSNR: `0.01 dB`
- MSE: `0.01`
- BPP: `0.0001`
- Payload length: `max(16, 0.0001 * W * H)` bits
