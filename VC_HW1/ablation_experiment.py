import contextlib
import io
import time
from pathlib import Path

import numpy as np
from PIL import Image

import codec_parameters
import decoder
import encoder
import evaluate


RESULTS = Path("results") / "ablation"
BASELINE_RESULTS = Path("results") / "lena" / "lena_evaluation.txt"
IMAGE = Path("lena_gray.png")
BASE_Q = codec_parameters.Q.copy()
BASE_ZIGZAG = codec_parameters.ZIGZAG.copy()
BASE_TRANSFORM = encoder.transform_block


def direct_transform(block, C=codec_parameters.DCT_BASIS):
    shifted = np.asarray(block, dtype=np.float64) - 128.0
    coefficient_matrix = np.empty((8, 8), dtype=np.float64)
    for u in range(8):
        for v in range(8):
            total = 0.0
            for x in range(8):
                for y in range(8):
                    total += C[u, x] * shifted[x, y] * C[v, y]
            coefficient_matrix[u, v] = total
    quantized = np.rint(coefficient_matrix / encoder.Q).astype(np.int32)
    if np.any(np.abs(quantized) > 2047):
        raise ValueError("quantized coefficient out of range (|v| > 2047)")
    return (
        shifted,
        np.empty((8, 8), dtype=np.float64),
        coefficient_matrix,
        quantized,
        quantized.reshape(-1)[encoder.ZIGZAG],
    )


# Precompute the direct 2D DCT kernel once.
# Shape: (u, v, x, y) = (8, 8, 8, 8)
_DIRECT_DCT_KERNEL = (
    codec_parameters.DCT_BASIS[:, None, :, None]
    * codec_parameters.DCT_BASIS[None, :, None, :]
)


def direct_transform_fast(block, C=codec_parameters.DCT_BASIS):
    shifted = np.asarray(block, dtype=np.float64) - 128.0

    if C is codec_parameters.DCT_BASIS:
        kernel = _DIRECT_DCT_KERNEL
    else:
        kernel = C[:, None, :, None] * C[None, :, None, :]

    # Direct 2D DCT:
    # coefficient_matrix[u, v] =
    # sum_x sum_y kernel[u, v, x, y] * shifted[x, y]
    coefficient_matrix = np.einsum(
        "uvxy,xy->uv",
        kernel,
        shifted,
        optimize=False,
    )

    quantized = np.rint(
        coefficient_matrix / encoder.Q
    ).astype(np.int32)

    if np.any(np.abs(quantized) > 2047):
        raise ValueError("quantized coefficient out of range (|v| > 2047)")

    return (
        shifted,
        np.empty((8, 8), dtype=np.float64),
        coefficient_matrix,
        quantized,
        quantized.reshape(-1)[encoder.ZIGZAG],
    )


def benchmark(transform):
    image = np.asarray(Image.open(IMAGE).convert("L"), dtype=np.uint8)
    blocks = [
        image[top:top + 8, left:left + 8]
        for top in range(0, image.shape[0], 8)
        for left in range(0, image.shape[1], 8)
    ]
    start = time.perf_counter()
    for _ in range(2):
        for block in blocks:
            transform(block)
    return time.perf_counter() - start


def run_variant(name, transform=BASE_TRANSFORM, quantization=BASE_Q,
                scan=BASE_ZIGZAG):
    encoder.Q = quantization
    decoder.Q = quantization
    encoder.ZIGZAG = scan
    decoder.ZIGZAG = scan
    encoder.transform_block = transform

    bitstream = RESULTS / f"ablation_{name}.bin"
    reconstructed = RESULTS / f"ablation_{name}_reconstructed.png"
    evaluation = RESULTS / f"ablation_{name}_evaluation.txt"
    encoder.encode(IMAGE, bitstream)
    decoder.decode(bitstream, reconstructed)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        evaluate.evaluate(IMAGE, reconstructed, bitstream)
    evaluation.write_text(output.getvalue(), encoding="utf-8")
    return output.getvalue()


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    lines = ["===== ABLATION RESULTS ====="]
    custom_q_lines = []
    raster_lines = []
    dct_lines = []
    dct_fast_lines = []

    custom_q_lines.append("\n===== QUANTIZATION TABLE X2 =====")
    custom_q_lines.append(run_variant("custom_q", quantization=BASE_Q * 2))

    raster = np.arange(64, dtype=np.int32)
    raster_lines.append("\n===== RASTER SCAN =====")
    raster_lines.append(run_variant("raster", scan=raster))

    encoder.Q = BASE_Q
    decoder.Q = BASE_Q
    encoder.ZIGZAG = BASE_ZIGZAG
    decoder.ZIGZAG = BASE_ZIGZAG

    two_stage_times = [benchmark(BASE_TRANSFORM) for _ in range(11)]
    direct_times = [benchmark(direct_transform) for _ in range(11)]
    direct_times_fast = [benchmark(direct_transform_fast) for _ in range(11)]

    two_stage_time = np.mean(two_stage_times[1:])
    direct_time = np.mean(direct_times[1:])
    direct_time_fast = np.mean(direct_times_fast[1:])

    dct_lines.append("\n===== DIRECT 2D DCT =====")
    dct_lines.append(f"Two-stage 1D DCT time (8192 blocks): {two_stage_time:.6f} s")
    dct_lines.append(f"Direct 2D DCT time (8192 blocks): {direct_time:.6f} s")
    dct_lines.append(run_variant("direct_dct", transform=direct_transform))

    dct_fast_lines.append("\n===== DIRECT 2D DCT (FAST) =====")
    dct_fast_lines.append(f"Two-stage 1D DCT time (8192 blocks): {two_stage_time:.6f} s")
    dct_fast_lines.append(f"Direct 2D DCT time (8192 blocks) - Fast: {direct_time_fast:.6f} s")
    dct_fast_lines.append(run_variant("direct_dct_fast", transform=direct_transform_fast))

    encoder.Q = BASE_Q
    decoder.Q = BASE_Q
    encoder.ZIGZAG = BASE_ZIGZAG
    decoder.ZIGZAG = BASE_ZIGZAG
    encoder.transform_block = BASE_TRANSFORM

    custom_q_line = "\n".join(custom_q_lines)
    raster_line = "\n".join(raster_lines)
    dct_line = "\n".join(dct_lines)
    dct_fast_line = "\n".join(dct_fast_lines)

    with BASELINE_RESULTS.open("r", encoding="utf-8") as f:
        baseline_line = f.read().strip()

    # remove the first line of baseline_line
    baseline_line = "\n".join(baseline_line.split("\n")[1:])
    baseline_line = "===== BASELINE RESULTS =====\n" + baseline_line

    savefile = RESULTS / "ablation_results.txt"
    savefile.parent.mkdir(exist_ok=True)

    with savefile.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")
        f.write(baseline_line + "\n")
        f.write(custom_q_line + "\n")
        f.write(raster_line + "\n")
        f.write(dct_line + "\n")
        f.write(dct_fast_line + "\n")

    print(f"Ablation results saved to {savefile}")

    # save field MSE, DCT, PSNR, Valid payload bits, BPP to a csv file for plotting
    csvfile = RESULTS / "ablation_results.csv"
    csvfile.parent.mkdir(exist_ok=True)

    extract_fields = ["MSE", "DCT", "PSNR", "Valid payload bits", "BPP"]

    def extract_field(lines: str, field):
        for line in lines.split("\n"):
            if line.startswith(field + ":"):
                return line.split(":")[1].strip()
        return None

    with csvfile.open("w", encoding="utf-8") as f:
        f.write("Variant,MSE,DCT,PSNR,Valid payload bits,BPP\n")

        extracted_baseline = [extract_field(baseline_line, field) for field in extract_fields]
        extracted_baseline = [value if value is not None else "" for value in extracted_baseline]
        extracted_baseline[1] = f"{two_stage_time:.6f}"
        print(f"extracted_baseline: {extracted_baseline}")
        f.write(f"baseline,{','.join(extracted_baseline)}\n")

        extracted_custom_q = [extract_field(custom_q_line, field) for field in extract_fields]
        extracted_custom_q = [value if value is not None else "" for value in extracted_custom_q]
        print(f"extracted_custom_q: {extracted_custom_q}")
        f.write(f"custom_q,{','.join(extracted_custom_q)}\n")

        extracted_raster = [extract_field(raster_line, field) for field in extract_fields]
        extracted_raster = [value if value is not None else "" for value in extracted_raster]
        print(f"extracted_raster: {extracted_raster}")
        f.write(f"raster,{','.join(extracted_raster)}\n")

        extracted_dct = [extract_field(dct_line, field) for field in extract_fields]
        extracted_dct = [value if value is not None else "" for value in extracted_dct]
        extracted_dct[1] = f"{direct_time:.6f}"
        print(f"extracted_dct: {extracted_dct}")
        f.write(f"direct_dct,{','.join(extracted_dct)}\n")

        extracted_dct_fast = [extract_field(dct_fast_line, field) for field in extract_fields]
        extracted_dct_fast = [value if value is not None else "" for value in extracted_dct_fast]
        extracted_dct_fast[1] = f"{direct_time_fast:.6f}"
        print(f"extracted_dct_fast: {extracted_dct_fast}")
        f.write(f"direct_dct_fast,{','.join(extracted_dct_fast)}\n")

    print(f"Ablation results CSV saved to {csvfile}")
