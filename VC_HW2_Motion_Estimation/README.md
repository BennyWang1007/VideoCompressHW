# HW2 — Motion Estimation（VC）：學生使用說明

## 一、三題差在哪裡？

| 方法（CLI `--method`） | Motion block | ME cost | Mode flag | Block-size RDO |
|---|---|---|---|---|
| `full_search` | 16×16，±7 | **只有 MAD** | 固定 `1` | 沒有 |
| `three_step_search` | 16×16，TSS ±7 | **只有 MAD** | 固定 `1` | 沒有 |
| `three_step_rdo` | 16×16 或 4×8×8，TSS ±7 | **只有 MAD** | `1` 或 `0` | **`SSD + 64 × R_bits`** |

**三題的 ME 都只依 MAD 選 MV**，相同 MAD 時依 `|dy|+|dx| → dy → dx` 依序比較。MVD 仍然須用 Signed Exp-Golomb 寫入 `.bin`；Q3 額外把 MVD bits 納入 block-size RDO 的 `R_bits`。

## 二、提供的程式／教材

- `hw1_reference/`：HW1 spatial codec，供你改接 signed residual；不得更改固定 DCT/量化矩陣/VALUE-EOB 規則。
- `images/one_gray.png`／`images/two_gray.png`：Reference／Current。**Decoder 不得讀 Current**。
- `provided/predictor_mvd.py`：固定 Left/Top/Top-Right median MVP 與 MVD helper，兩端要用相同順序更新 MV field。
- **`provided/exp_golomb_demo.py`：有可直接運行的 bit-level 範例**，包含 `encode_signed()`、`pack_payload()`、`BitReader.read_signed_exp_golomb()`，示範 *寫入 MVD → header/padding → 讀回 MVD*。
- `provided/evaluator.py`：完整的學生端 **syntax check**，會解析 header、Mode、MVD、HW1 VALUE/EOB、MV 範圍、payload、padding，並計算 BPP/提交 PNG 的 PSNR。**它不是 canonical decoder**。
- `provided/check_submission.py`：檢查資料夾結構與三題 bitstream syntax。
- `src/encoder.py`／`src/decoder.py`：保持固定 CLI，內部自行完成；可增加自己的 `*.py` helper。

## 三、先跑 Signed Exp-Golomb 示例

(請注意我只允許以下兩套件，以及其他python基礎套件，不准call function。)
```bash
python -m pip install numpy pillow
python provided/exp_golomb_demo.py
```

例：`MV=[6,1]`、`MVP=[5,1]`，所以 `MVD=[+1,0]`；MVD_y 的 codeword 是 `010`（3 bits），MVD_x 是 `1`（1 bit）。這兩個直接相接，**不會寫兩個長度欄位**。Decoder 讀第一個 `010` 時，看到前導 `0` 共 1 個，遇到 `1` 後再讀 1 bit，即可知道第一個 codeword 結束；接著直接讀下一個 `1`。

當 `mode=1`、四個 8×8 residual 都只有 EOB=`111111111`，整個單一 macroblock 的 `valid_payload_bits=41`，最後的示意 bytes 為：

```text
00 00 00 29 | AF FF FF FF FF 80   (hex)
 4-byte header | 41 payload bits + 7 zero padding bits
```

**Header 只記錄整份 payload 的有效 bits 數，不是每個 MVD 的 bit 數**。中間每個 MVD、residual 後面都**不能**補 byte padding。實作完整檔案時必須逐 macroblock 寫入，最終檔案只 padding 一次。

### Q3 MVP/MVD 陷阱

- `mode=1`：一個 16×16 MV，**一組 MVD**，四個 8×8 residual；選定後把同一 MV 填到 MV field 的 2×2 格。
- `mode=0`：TL → TR → BL → BR 順序**各算 MVP、各寫 MVD、各更新 MV field**，總共四組 MVD + 四個 residual。
- 即使四個 8×8 的 MV 一模一樣，因為 MVP 依處理順序改變，MVD 也可能不同。**MVD=(0,0) 仍然要編成 `1|1`（2 bits）**，不得省略。
- 兩個候選模式試算 RDO 時，請複製同一份「前一個 macroblock 結束後」的 MV field。**只正式保留獲選模式的狀態**。

## 四、實作後如何執行及檢查？

```bash
python src/encoder.py --reference images/one_gray.png --current images/two_gray.png --method full_search --output test.bin
python src/decoder.py --reference images/one_gray.png --input test.bin --method full_search --output test_decoded.png
```

切換 `--method three_step_search` 或 `--method three_step_rdo`，各自完成一次 encoding 與 decoding。再自測：

```bash
python provided/evaluator.py images/one_gray.png images/two_gray.png test.bin test_decoded.png --method full_search
```

完成三題後，在 `student_package/` 直接整理出繳交資料：

```bash
python run_local.py --student-id 123456789 --method all
# 自行放入 HW2_123456789/report/HW2_123456789.pdf
python provided/check_submission.py HW2_123456789
```

結果位於 `HW2_123456789/results/submitted/{full_search,three_step_search,three_step_rdo}/`。最後將整份 `HW2_123456789/` 壓成 `HW2_123456789.zip`。不要只上傳 `.bin` 或只上傳 `.png`。

**Evaluator PASS 不等於完全正確**：TA 會重新跑你交的 `src/encoder.py`、`decoder.py`，獨立 decode 你實際產生的 `.bin` 並比對 PNG；成績以有效重跑結果為準。Q1/Q2 各 25 分有效執行與 10 分班平均區間，Q3 PSNR/BPP 各 8 分 Tier，Report 14 分。

**如果你的實作會 import `predictor_mvd`，請把固定的 `provided/predictor_mvd.py` 複製到提交的 `src/`，因為 TA 重跑只會複製 `src/` 內的執行相依程式。**