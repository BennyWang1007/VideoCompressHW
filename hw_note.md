
# 

## Encoder
```bash
python encoder.py \
  <input_png> \
  <output_bin> \
  --trace <trace_file> \
  --block-index <index>
```
e.g. 
```bash
python encoder.py \
  lena_gray.png \
  output.bin \
  --trace encoder_trace.txt \
  --block-index 0
```
## Decoder
```bash
python decoder.py \
  <input_bin> \
  <output_png> \
  [--trace <trace_file>] \
  [--block-index <index>]
```
e.g.
```bash
python decoder.py \
  output.bin \
  reconstructed.png \
  --trace decoder_trace.txt \
  --block-index 0
```

## Evaluation
```bash
python evaluate.py \
  <original_png> \
  <reconstructed_png> \
  <bitstream_bin>
```
e.g.
```bash
python evaluate.py \
  lena_gray.png \
  reconstructed.png \
  output.bin
```


### Huffman Coding& Token Payload Format
For a coefficient value v, define its magnitude category as:
$$
category(v) =
\begin{cases}
0, & v = 0 \\
\lfloor \log_2(|v|) \rfloor + 1, & v \neq 0
\end{cases}
$$

EOB (End of Block): indicates that the remaining coefficients in the current block are all zero.

Amplitude bits for VALUE
- For s = 0, VALUE(0) has no amplitude bits.
- For positive v, write v as an unsigned s
bit binary integer.
- For negative v, write v + (2𝑠 1) as an unsigned s bit binary integer.
- All bits are written MSB
first.

Examples:
VALUE(0) = 00\
VALUE(1) = 010 | 1\
VALUE(-1) = 010 | 0\
VALUE(5) = 100 | 101\
VALUE(-2 ) = 011 | 01\
EOB = 111111111


## TODO
### encoder.py
- transform_block()
    - Level shift, DCT, quantization, coefficient range validation, and zigzag scan
- encode_block_symbols(zigzag)
    - Internal VALUE(0) symbols and correct EOB handling
- write_symbol(...)
    - VALUE/EOB bitstream writing
### decoder.py
- read_value(reader, s)
    - Signed coefficient recovery from amplitude bits
- read_block(reader)
    - VALUE/EOB decoding into 64 zigzag coefficients
- reconstruct_block(zigzagged)
    - Inverse zigzag, dequantization, IDCT, level restoration, rounding, and clipping

Please do not modify the output txt format.

## Grading Policy
70%: Standard Implementation
Two test cases are provided, and hidden test cases will be used.
Use **lena_reference_output.txt** and **mandril_reference_output.txt** to compare the intermediate
results for block index 0 and the final evaluation metrics.
Your implementation does not need to be bit-for-bit identical to the reference.
Allowed differences: Floating point values : 0.01 , PSNR: 0.01 dB , MSE: 0.01 , BPP: 0.0001 , Payload
length: $max(16, [0.0001 𝑊 × 𝐻])$ bits



30%: Lab Report
Please conduct the following ablation experiments, observe whether the specified metrics change, and analyze the reason:
- (10%) Custom modifications to the Quantization table --> bpp , PSNR
- (10%) Zigzag vs. Raster $\rightarrow$ bpp , PSNR
- (10%) Two stage 1D DCT vs. Direct 2D DCT $\rightarrow$ Time, bpp \
(It is recommended to measure DCT computation time only. Use any timing tool, such as `time.perf_counter()`.)

$$ Direct\ 2D\ DCT: F_{u,v} = \sum_{x=0}^{7} \sum_{y=0}^{7} C_{u,x} f_{x,y} C_{v,y} $$

Implement the direct 2D DCT using the double summation formula, not C @ f @ C.T

For ablation experiments, you may modify any provided source file or create additional files as needed.
Include the experimental results and analysis in your report only. Do not submit ablation code.