#!/usr/bin/env bash

# Create results folder if it doesn't exist
mkdir -p results

evaluate_image() {
  local image_name="$1"
  local image_path="$2"
  local ref_output="$3"

  mkdir -p "results/${image_name}"

  local bin_file="results/${image_name}/${image_name}.bin"
  local recon_img="results/${image_name}/${image_name}_reconstructed.png"
  local enc_trace="results/${image_name}/${image_name}_encoder_trace.txt"
  local dec_trace="results/${image_name}/${image_name}_decoder_trace.txt"
  local enc_out="results/${image_name}/${image_name}_encoder_output.txt"
  local dec_out="results/${image_name}/${image_name}_decoder_output.txt"
  local eval_out="results/${image_name}/${image_name}_evaluation.txt"
  local final_out="results/${image_name}/${image_name}_output.txt"
  local step_err="results/${image_name}/${image_name}_step_error.log"

  # Helper function to halt execution on failure
  fail_and_exit() {
    local step_name="$1"
    echo "[FAIL] Test for image '${image_name}' FAILED at step: ${step_name}"
    echo "--- ERROR LOG ---"
    if [ -f "$step_err" ] && [ -s "$step_err" ]; then
      cat "$step_err"
    fi
    echo "-----------------"
    exit 1
  }

  # 1. Encode
  if ! python encoder.py \
    "$image_path" \
    "$bin_file" \
    --trace "$enc_trace" \
    --block-index 0 > "$enc_out" 2> "$step_err"
  then
    fail_and_exit "encoder.py"
  fi

  # 2. Decode
  if ! python decoder.py \
    "$bin_file" \
    "$recon_img" \
    --trace "$dec_trace" \
    --block-index 0 > "$dec_out" 2> "$step_err"
  then
    fail_and_exit "decoder.py"
  fi

  # 3. Evaluate
  {
    echo "===== FINAL EVALUATION ====="
    if ! python evaluate.py \
      "$image_path" \
      "$recon_img" \
      "$bin_file" 2> "$step_err"
    then
      fail_and_exit "evaluate.py"
    fi
  } > "$eval_out"

  # 4. Concatenate with blank line spacers
  cat "$enc_out" \
      <(printf '\n\n') \
      "$dec_out" \
      <(printf '\n\n') \
      "$eval_out" \
      > "$final_out"

  # 5. Normalize line endings and strip trailing newline
  dos2unix -q "$final_out"
#   truncate -s -1 "$final_out"

  # 6. Compare with reference output
  local diff_err="results/${image_name}_diff.log"
  if ! diff -u --strip-trailing-cr -wB "$final_out" "$ref_output" > "$diff_err" 2>&1; then
    echo "[FAIL] Test for image '${image_name}' FAILED (diff mismatch)"
    echo "--- DIFF ERROR LOG ---"
    cat "$diff_err"
    echo "----------------------"
    exit 1
  fi

  echo "[PASS] Test for image '${image_name}' PASSED"
  rm -f "$step_err" "$diff_err"
}

run_ablations() {
  if ! python ablation_experiments.py; then
    echo "[FAIL] Ablation experiments failed"
    exit 1
  fi
  echo "[PASS] Ablation experiments completed"
}

# Example Usage:
# evaluate_image "<image_name>" "<image_path>" "<reference_output_file>"
evaluate_image "lena" "lena_gray.png" "lena_reference_output.txt"
evaluate_image "mandril" "mandril_gray.png" "mandril_reference_output.txt"

run_ablations