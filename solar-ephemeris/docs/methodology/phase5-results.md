# Phase 5 — Kết quả thí nghiệm (phase5-results.md)

**Ngày:** 2026-10-03 · **Trạng thái:** hoàn tất 13/13 bước theo đúng thứ tự
đã phê duyệt · **Hợp đồng:** `docs/methodology/phase5-experiment-design.md`
(APPROVED-WITH-CORRECTIONS, 5 hiệu chỉnh đã áp dụng nguyên vẹn).

Số liệu lấy từ `results/` (mọi `experiment_record.json` đều mang
`configuration_hash`, `output_hash`, `gates` — tái lập bằng 2 lần chạy
bitwise `np.array_equal` + hash bằng nhau). Kernel: `de440s.bsp`
(manifest md5 `3917ee56769db332790c751e2168843d`, sha256
`c1c7fee…a49f2`, verified at load). Software `0.1.0`.

**Thứ tự chạy (§11 — không đảo, không tinh chỉnh sau khi thấy số):**
gaps → Gate A+B → A1+B synthetic → freeze baseline (`results/baseline_frozen.json`)
→ A2 → E 1 d → E 30 d → freeze gates (`results/gates_frozen.json`) → C → D
→ E 90 d → Gate → E 365 d → báo cáo này. Mọi ngưỡng dùng để judge đều nằm
trong 2 file freeze, viết **trước** thí nghiệm mà chúng judge
(`e_has_error_acceptance_threshold: false`).

---

## 1. Numerical error (chỉ A1 — analytic IC, tham chiếu đúng)

A1: Sun–Earth hai-body tròn, IC `analytic-circular`, `horizon = P/4`,
endpoint error vs nghiệm đúng. Grid `n ∈ {25,50,100,200}`.

| n | RK4 endpoint (m) | Verlet endpoint (m) | RK4 max\|dE/E₀\| | Verlet max\|dE/E₀\| |
|---:|---:|---:|---:|---:|
| 25 | 4.159e4 | 1.482e8 | 4.28e-8 | 1.95e-6 |
| 50 | 2.491e3 | 3.707e7 | 1.34e-9 | 1.22e-7 |
| 100 | 1.522e2 | 9.269e6 | 4.17e-11 | 7.61e-9 |
| 200 | 9.405 | 2.317e6 | 1.30e-12 | 4.76e-10 |

- **H_A1 ✓:** bậc quan sát RK4 = [4.061, 4.032, 4.017] ∈ [3.5, 4.5];
  Verlet = [1.999, 2.000, 2.000] ∈ [1.5, 2.5]. Lỗi giảm nghiêm ngặt mọi
  halving, mọi giá trị ≫ sàn roundoff (bản nhỏ nhất 9.405 m ≈ 2.8×10⁵ × sàn).
- Động lượng góc: Verlet ≤ 2.0e-15 (symplectic, không trôi đo được);
  RK4 2.14e-8 → 6.51e-13 theo lưới. Drift/năm quỹ đạo RK4 1.71e-7 → 5.21e-12.
- 8/8 record (2 tích phân × 4 n) qua hết gate: sàn, bậc, tái lập.

## 2. Model/reference discrepancy (A2 · D · E — không bao giờ thành claim "integrator accuracy")

### 2.1 A2 — Sun–Earth 7 d, IC DE440-derived, RK4 (báo cáo 3 phần, H_A3)

D_k = max E_pos vs DE440:

| dt | D_k (m) | tỷ số D_k/D_{k+1} | phân loại (rule 2^p<2 ⇒ floor) |
|---|---:|---:|---|
| P/500 | 5.588e6 | — | — |
| P/1000 | 5.073e6 | 1.101 | floor-dominated |
| P/2000 | 5.073e6 | 1.000 | floor-dominated |
| P/4000 | 5.200e6 | 0.976 | floor-dominated |

- **(i) Observed numerical convergence regime: không có** — không khoảng
  nào giảm khi dt giảm (tỷ số đầu đã < 2). Không tính `2^p` trên tổng
  chênh lệch (hiệu chỉnh #2).
- **(ii) Plateau/floor regime: 3/3 interval floor-dominated** — từ chính
  dt lớn nhất đã nằm trên sàn.
- **(iii) Interpretation:** sàn ~5.07e6 m là chênh lệch **model/IC vs
  DE440**, không phải "lỗi tích phân"; plateau ≠ failed convergence;
  `E_pos[0] = 0.0` exact; max relative energy error 1.4e-12 → 1.3e-15 theo lưới.

### 2.2 D — tái xác nhận DE440 (H_D1, H_D2)

**Formal (ngưỡng Phase-4 đã nghiệm thu, không đụng lại):**

| Run | E_pos max (m) | band | E_vel max (m/s) | band | rel ≤ 3.45e-3 |
|---|---:|---|---:|---|---:|
| T1 @ 7 d | 5.07321e6 | [5e4, 5.1e8] ✓ | 16.4805 | [0.16, 1650] ✓ | 3.449e-5 ✓ |
| T2 @ 7 d | 15033.85 | [150, 1.51e6] ✓ | 0.04874 | [4.8e-4, 4.88] ✓ | 1.02e-7 ✓ |

Hai số liệu **trùng khớp từng chữ số với Phase 4** (5.07321e6 / 16.4805 /
15033.85 / 0.0487388) → tái lập hoàn toàn.

**Report-only (KHÔNG ngưỡng mới — hiệu chỉnh/theo §6):**

| Run | E_pos max (m) | E_vel max (m/s) | rel max | mẫu |
|---|---:|---:|---:|---:|
| T3 @ 7 d | 1.087e4 | 3.531e-2 | 7.39e-8 | 65 |
| T1 @ 30 d | 3.159e7 | 25.66 | 2.14e-4 | 83 |
| T2 @ 30 d (dùng lại C) | 2.031e5 | 1.594e-1 | 1.38e-6 | 11 |
| T3 @ 30 d (dùng lại C) | 1.527e5 | 1.269e-1 | 1.04e-6 | 11 |

Reuse T2/T3@30 d: `config_hash` C == D, assert lúc ghi record
(`reused_from: experiment_C/tier_T2|T3`). `E_pos[0] == 0` exact ở **mọi**
run (H_D1 ✓). Mọi record đối chiếu manifest kernel.

### 2.3 E — horizon 1 → 30 → 90 → 365 d, T2 SEM, RK4 (mô tả thuần, không error threshold)

| horizon | mẫu | structural gates | E_pos max (m) | E_vel max (m/s) | rel max | growth (§6e) |
|---|---:|---|---:|---:|---:|---|
| 1 d | 2 | 8/8 PASS | 3.249e2 | 7.42e-3 | 2.21e-9 | không đủ mẫu |
| 30 d | 30 | 8/8 PASS | 2.313e5 | 1.689e-1 | 1.57e-6 | **power** (SSE 1.73e8 ≤ 0.1× linear 1.84e10) |
| 90 d | 90 | 8/8 PASS | 2.046e6 | 5.015e-1 | 1.37e-5 | **power** (2.7e10 ≤ 0.1× linear 4.7e12) |
| 365 d | 362 | 8/8 PASS | 1.112e7 | 2.075 | 7.47e-5 | **không phân biệt được** (best linear 8.05e14 / power 1.14e15 = 0.71 > 0.1) → không chọn mô hình |

- **H_E1 ✓ (mức mô tả):** E_pos tăng theo horizon (325 m → 1.11e7 m).
  Hình dạng: 30/90 d phân biệt được power theo đúng rule đã đăng ký;
  **365 d không phân biệt → không claim growth law** (hiệu chỉnh #1:
  phân loại mô tả, không phải tiêu chuẩn chấp nhận).
- **H_E2 ✓ 4/4 horizon**, tổng 32/32 gate §6b: finite · tái lập bitwise +
  output_hash · hoàn tất đúng lưới (`n_samples = 2/30/90/362`) ·
  conservation · provenance (§6d đủ + kernel hashes == manifest) ·
  không numerical failure. Conservation đo được (worst qua 4 horizon):
  `max|dE/E₀| = 1.93e-14 ≤ 1e-6`, `max|P_rel| = 2.15e-15 ≤ 1e-10`,
  `max|ΔL|/|L0| = 9.51e-15 ≤ 1e-8` — ngưỡng đóng băng, không suy ra từ lỗi.
- **Không tồn tại error-acceptance threshold nào cho E**
  (`e_has_error_acceptance_threshold: false` trong `gates_frozen.json`).
- Cánh ref của B (lưới P_SE/{500…4000}, 8 số RK4/Verlet): tất cả nằm cùng
  sàn 5.07e6 m (xem phụ lục B) → **không phân biệt tích phân ở cánh ref**.

## 3. Physical perturbation signal (Experiment C — 4 tầng, 30 d)

Criterion đóng băng: `signal ≥ 10 × control` (control = điều khiển halving
T2/T3@dt/2 pre-registered; **T3↔T4 mượn control T3** — ghi trong record
trước khi judge). Mọi cặp **RESOLVED** (tệ nhất vẫn 2.63×10⁶ × ngưỡng):

| cặp | metric | signal (m) | control (m) | ratio |
|---|---|---:|---:|---:|
| T1↔T2 | ΔEarth | 3.044e7 | 1.285e-3 | 2.37e10 |
| T1↔T2 | Δbary(Sun,Earth) | 5.451e3 | 3.69e-9 | 1.48e12 |
| T2↔T3 | ΔEarth | 2.473e5 | 1.119e-3 | 2.21e8 |
| T2↔T3 | ΔMoon | 2.473e5 | 9.39e-2 | 2.63e6 |
| T2↔T3 | Δbary(S,E,M) | 2.068e5 | 2.25e-9 | 9.18e13 |
| T3↔T4 | ΔEarth | 1.147e9 | 1.119e-3 | 1.02e12 |
| T3↔T4 | ΔMoon | 1.147e9 | 9.39e-2 | 1.22e10 |
| T3↔T4 | Δbary(6 thân) | 1.147e9 | 2.44e-9 | 4.69e17 |

**H_C2 ✓** — tín hiệu tầng luôn ≫ nhiễu halving (≥ 2.63e6 ×, ngưỡng là 10×).
Không câu nào rơi vào "signal not numerically resolved".

**H_C1 (hướng là giả thuyết mở — số đo được):** E_pos max vs DE440 theo
tầng, cùng dt/mẫu: T1 3.061e7 → T2 2.031e5 → T3 1.527e5 → **T4 543.7 m**
(E_vel: 25.41 → 0.159 → 0.127 → 4.51e-4 m/s; Moon T4 = 1.204e3 m).
Quan sát: **giảm dần** khi thêm tầng thân (T1 thiếu Moon+planets nên lệch
lớn nhất). Báo cáo như số đo, không suy diễn nguyên nhân beyond data.
Điều khiển dt/2 cho kết quả E_pos giống main tới chữ số hiển thị
(T2: 203096 == 203096) → nhiễu halving nằm dưới sàn chênh lệch tầng.

## 4. Roundoff / precision limits

- Sân roundoff **tái dùng nguyên vẹn** Phase 1–2: `1.5e11 × 2⁻⁵² =
  3.3307e-5 m` @1 AU — không tính lại để khớp kết quả (hiệu chỉnh #5;
  contract test assert `3.2e-5 < floor < 3.4e-5`).
- **Không thí nghiệm nào bị giới hạn bởi roundoff:** numerical error nhỏ
  nhất (A1 n=200) = 9.405 m ≈ 2.8×10⁵ × sàn; toàn bộ chênh lệch
  model/reference (3.2e2 … 1.1e7 m) đều ≫ sàn; conservation nằm ở chế độ
  máy-định (1e-14…1e-17, informational).
- (Thông tin: Verlet giữ động lượng góc ≤ 2e-15 qua lưới A1 — symplectic,
  không phải claim chấp nhận.)

## 5. Stability limitations

**Không có.** Không gate §6b nào bị vượt ở bất kỳ horizon/experiment nào;
không numerical failure; 32/32 gate E PASS; A1 8/8, A2 4/4, C 6/6 record
(repro), D formal 2/2. Runtime (informational, không tham gia determinism):
A1 n=200 ≈ 0.03 s · C T4 30 d ≈ 0.19 s/chạy · E 365 d ≈ 1.9–2.0 s/chạy.

---

## Phụ lục B — Experiment B (kiểm chứng tích phân, không xếp hạng tổng thể)

§12 gán nhãn "numerical error" cho A1; B trình bày tách riêng, mỗi cánh
gắn đúng lớp tham chiếu của nó.

**Cánh synthetic (IC analytic, tham chiếu = nghiệm đúng — cùng lớp A1):**

- **H_B1 ✓:** drift/năm quỹ đạo RK4 < Verlet ở MỌI dt
  (1.71e-7 < 8.09e-6 … 5.21e-12 < 1.98e-9); Verlet 1 vòng quỹ đạo:
  drift = 1.22e-16 ≤ 1e-12 (ngưỡng Phase-3) — dao động có biên, không
  trôi đại số; RK4 phẳng hơn.
- **H_B2 ✓:** endpoint RK4 < Verlet ở mọi n (bảng mục 1: 4.16e4 ≪ 1.48e8 …
  9.4 ≪ 2.32e6).

**Cánh ref (IC DE440, 7 d, lưới P_SE/{500,1000,2000,4000}):**

| divisor | RK4 max E_pos (m) | Verlet max E_pos (m) | RK4 < Verlet? |
|---:|---:|---:|---|
| 500 | 5.588e6 | 5.345e6 | no |
| 1000 | 5.073e6 | 5.009e6 | no |
| 2000 | 5.073e6 | 5.057e6 | no |
| 4000 | 5.200e6 | 5.196e6 | no |

Cả 8 số nằm trong cùng sàn ~5.07e6 m (A2: tỷ số halving ≈ 1.0) → chênh
lệch 0.1…5.6% giữa hai tích phân **nằm trong nhiễu sàn**, không đủ sức
phân biệt. Kết luận B: **tích phân phân biệt được ở cánh synthetic
(H_B1/H_B2 ✓), không phân biệt được ở cánh ref (floor-dominated) — không
tuyên bố ai thắng overall** đúng như hợp đồng. "Verlet nhỏ hơn RK4" ở
bảng trên **không** phải kết luận (không significant so với sàn).

---

## Nhật ký thực thi & defect

1. Gaps §7 hoàn tất: `src/solar_ephemeris/analysis/momentum.py`
   (thúc helper momentum; `tests/numerical/test_conservation.py` import
   lại), `experiments/{__init__,_common,run_phase5}.py`,
   `tests/unit/test_experiment_contract.py`.
2. Gate A: 324 → **340 passed** (+16 test hợp đồng), Gate B: **26 passed**;
   chạy lại ở bước 11 và bước 13 đều xanh.
3. Defect duy nhất trong lúc chạy: `cmd_c` ban đầu tra
   `controls["T4"]` (KeyError) — sửa về đúng quy tắc **pre-registered**
   "T3↔T4 mượn control T3" TRƯỚC khi bất kỳ số C nào được judge; không
   ngưỡng nào bị sửa; quy tắc nằm nguyên văn trong `experiment_C/analysis.json`.
4. Mọi stdout dùng UTF-8 (bảng chỉ đọc, record JSON UTF-8).

## Câu hỏi nghiên cứu — trả lời ngắn

- **Q1 (dt):** bậc 4/2 xác nhận chính xác (A1); trên cánh DE440 7 d, dt
  đã dưới sàn model/reference từ P/500 → giảm dt thêm không cải thiện
  E_pos (A2 floor-dominated).
- **Q2 (tích phân):** synthetic phân biệt sạch theo cả 2 hướng (RK4 phẳng
  hơn, endpoint nhỏ hơn); ref không phân biệt được vì cùng sàn — không
  xếp hạng tổng thể.
- **Q3 (số thân):** tín hiệu tầng luôn ≫ nhiễu halving (≥ 2.6e6 ×); E_pos
  vs DE440 giảm dần T1→T4 (số đo, hướng quan sát được).
- **Q4 (DE440):** tái lập đúng từng chữ số ngưỡng Phase-4 (T1/T2 @ 7 d);
  `E_pos[0]==0` exact mọi tầng; T4 30 d đạt 543.7 m (report-only).
- **Q5 (horizon):** E_pos tăng 325 m (1 d) → 1.11e7 m (365 d); growth
  phân biệt "power" ở 30/90 d, **không** phân biệt ở 365 d → không claim
  hình dạng tăng trưởng cho mốc cuối; mọi horizon qua structural gate.

---

## Final Phase 5 gate — checklist §13

```text
[x] A1 completed                        (results/experiment_A1, 8 record + 2 orders)
[x] A2 completed                        (results/experiment_A2, 4 record + analysis.json)
[x] B completed                         (synthetic + one_period + ref_lattice + ref_summary.json)
[x] C completed                         (4 tier + 2 control + analysis.json, all resolved)
[x] D completed                         (6 record: 2 formal PASS, 4 report-only)
[x] E completed through the allowed horizon   (1 d → 30 d → 90 d → 365 d, 32/32 gates)
[x] all results are reproducible         (mọi record: 2 chạy bitwise + config_hash + output_hash)
[x] all experiment metadata are recorded (§6d fields — contract test + gate 5 provenance/E)
[x] thresholds were frozen before judging results
                                          (baseline_frozen.json trước A2/E; gates_frozen.json trước C/D/E90)
[x] no post-hoc acceptance threshold was introduced
                                          (e_has_error_acceptance_threshold=false; D@30d report-only; growth không ngưỡng)
[x] numerical error is separated from model/reference discrepancy   (5 mục §12 tách riêng ở trên)
[x] scientific conclusions are supported by measured results        (Q1–Q5 ở trên, mỗi claim kèm số)
[x] phase5-results.md exists             (file này)
[x] all existing tests remain green      (Gate A 340 passed, Gate B 26 passed — chạy tại bước 13)
```

**Phase 5: PASS. STOP** — không tự động bắt đầu feature mới (§13 cuối).
