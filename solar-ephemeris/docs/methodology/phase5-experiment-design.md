# Phase 5 — Thiết kế thí nghiệm khoa học (Experimental Design — chưa triển khai)

Tài liệu này là **hợp đồng thí nghiệm** cho Phase 5. Nó CHỈ chứa thiết kế:
không code thí nghiệm, không chạy sweep. Code chỉ được viết sau khi được
phê duyệt tường minh. Sửa tài liệu = sửa hợp đồng, kèm sửa test tương ứng.

Trạng thái: **APPROVED-WITH-CORRECTIONS — hợp đồng đóng băng** (2026-10-03).
Người dùng phê duyệt kèm 5 hiệu chỉnh bắt buộc: (1) E **không** có
error-acceptance threshold kiểu `100 × measured`; (2) A2 = hội tụ trước
rồi plateau (không yêu cầu `2^p` trên tổng chênh lệch); (3) T4 = 10 thân
chuẩn, Pluto là selected-body extension; (4) `de440s.bsp` chuẩn, không
tải `de440.bsp`; (5) sàn roundoff tái dùng HĐ Phase 1–2, không tạo sàn
mới. Mọi sửa đổi sau này phải kèm sửa test hợp đồng.

---

## 0. Kiểm kê năng lực hiện có (Step 1 audit)

```text
Yêu cầu thí nghiệm              | Năng lực hiện có                              | Thiếu                                    | Phần mở rộng tối thiểu              | Nguy cơ khoa học
---------------------------------|------------------------------------------------|------------------------------------------|--------------------------------------|---------------------------------------
Tích phân (Verlet / RK4)         | integrators/base+rk4+verlet, registry, chuẩn  | —                                          | —                                    | —
Bước timestep đặt được           | SimulationConfig.dt (>0, hashed)               | —                                          | —                                    | Grid dt bị chọn sau khi thấy kết quả → cấm, phải đóng băng trước
Chọn thân (body selection)       | SimulationConfig.bodies (tập con tùy ý của registry 11 thân) | —                                          | —                                    | Tier mơ hồ → **đã chốt cứng: T4 = 10 thân chuẩn MASTERPLAN, Pluto = selected-body extension (§3.1, §10.1)**
Mô phỏng tất định                | engine stateless + config_hash + test bitwise | —                                          | —                                    | Giả kết quả tất định nếu hash sai → kiểm output_hash
Chẩn đoán năng lượng            | analysis.energy.total_energy / relative_…     | —                                          | —                                    | Năng lượng nhạy dt hơn quỹ đạo (đã đo) — dùng làm metric chính
Chẩn đoán động lượng góc        | CHỈ có trong tests/numerical/test_conservation (helper) | hàm dùng lại được cho experiments  | đưa `angular_momentum_series` về `analysis/` (di trú code test, không đổi hành vi) | Chẩn đoán không tái sử dụng được → mỗi experiment tự viết → lệch định nghĩa
So sánh DE440                     | ephemeris/* pipeline Phase 4 (đã nghiệm thu)  | —                                          | KHÔNG ĐỤNG (bắt buộc theo brief)    | pipeline bị sửa → mất tính hợp lệ Phase 4
Số liệu vị trí/vận tốc           | compare_trajectory (mean/median/max/p95)      | —                                          | —                                    | —
Cấu hình thí nghiệm              | SimulationConfig (đóng băng qua config_hash)  | khái niệm experiment_id                  | record thí nghiệm bọc RunRecord      | Biến đổi ngầm giữa các run
Output record / tái lập            | runner.run_to_file + RunRecord + load_run     | output_hash của mảng; thời gian chạy     | writer record thí nghiệm (experiments/_common) | Hash npz bytes (zip timestamp) → phải hash mảng, không hash file
Khác biệt hai run cùng lưới mẫu   | analysis.compare.trajectory_difference        | —                                          | —                                    | Lệch lưới mẫu → engine chặn, không tự nội suy
IC tổng hợp (analytic)            | simulation.initial_conditions (hai-body tròn, Sun–Earth–Moon) | —                          | —                                    | Trộn IC tổng hợp với IC DE440 trong cùng một metric
IC suy từ DE440                   | ephemeris/ic.reference_state_to_model_state   | —                                          | —                                    | Gọi chênh lệch DE440 là "lỗi tích phân" → cấm diễn giải
Ước lượng bậc hội tụ              | helper trong tests/numerical/test_convergence (endpoint_error, observed_orders) | dùng lại trong experiments | đưa helper vào experiments/_common (không đổi công thức) | Ước lượng trên sai số dưới floor = vô nghĩa → kiểm floor
Đo thời gian chạy                 | không có                                        | wall-clock per run                        | time.perf_counter trong harness      | Trượt sang tối ưu hiệu năng → ngoài phạm vi
```

**Kết luận:** không component nào bị thiết kế lại; 4 phần mở rộng (momentum
di trú, record thí nghiệm, harness mỏng, timing + helper số) là tối thiểu.

---

## 1. Research questions (Câu hỏi nghiên cứu)

1. **Q1 — Timestep:** ảnh hưởng của dt tới độ chính xác quỹ đạo và tính ổn
   định số là gì? (Experiment A)
2. **Q2 — Tích phân:** Verlet và RK4 hành vi khác biệt thế nào trong điều
   kiện kiểm soát? (Experiment B)
3. **Q3 — Số thân:** tăng số thân tương tác hấp dẫn ảnh hưởng tới độ phân
   kỳ quỹ đạo ra sao? (Experiment C)
4. **Q4 — DE440:** mô hình độc lập tái tạo DE440 tốt đến đâu dưới cấu hình
   kiểm soát? (Experiment D)
5. **Q5 — Horizon:** sai số mô hình/tham chiếu tiến triển theo thời gian mô
   phỏng như thế nào? (Experiment E)

## 2. Hypotheses (Giả thuyết — chỉ những gì engine hiện có kiểm chứng được)

- **H_A1** (đo với nghiệm hai-body tròn đúng nghĩa): bậc quan sát
  `p = log2(E(dt)/E(dt/2))` ∈ [3.5, 4.5] cho RK4 và ∈ [1.5, 2.5] cho Verlet.
  *Cơ sở: lý thuyết bậc + số đo nền [4.02, 4.06] / [2.00, 2.00] đã có.*
- **H_A2** (chỉ cánh synthetic A1): sai số giảm nghiêm ngặt khi dt giảm,
  luôn ở trên sàn roundoff phân tích — **sàn tái dùng nguyên vẹn hợp đồng
  chính sách số Phase 1–2** (`tests/numerical/test_convergence.py`:
  `1.5e11 × 2⁻⁵² ≈ 3.3e-5 m` @1 AU; tính lại minh bạch: 1.496e11 ×
  2.22e-16 ≈ 3.32e-5 m). Không tạo sàn mới, không chỉnh sàn cho khớp kết
  quả thí nghiệm.
- **H_A3** (cánh DE440, Sun–Earth, 7 d) — **hai chế độ, KHÔNG yêu cầu
  `2^p` trên tổng chênh lệch**: (i) *observed numerical convergence
  regime* — chênh lệch model/reference giảm khi dt giảm trong vùng tích
  phân còn phân giải được; (ii) *plateau/floor regime* — phần bẹt ở dt
  nhỏ nhất là sàn model/tham chiếu. Báo cáo tách 3 phần: convergence
  regime / plateau-floor regime / interpretation; **plateau ≠ failed
  convergence**; sàn **không** gọi là "lỗi tích phân".
- **H_B1**: cùng dt, năng lượng Verlet dao động có biên, không trôi đại số
  (drift < 1e-12 trên một vòng quỹ đạo — ngưỡng đã nghiệm thu từ Phase 3);
  năng lượng RK4 phẳng hơn Verlet ở cùng dt.
- **H_B2**: cùng lưới dt, sai số endpoint của RK4 nhỏ hơn Verlet ở MỖI dt
  (đã đo trong Phase 3 — tái kiểm chứng, không tuyên bố "ai thắng overall").
- **H_C1**: với IC DE440 và dt đóng băng, Earth-vs-DE440 discrepancy theo
  tầng tầng thân (T1→T4) thay đổi có hướng — **hướng tăng/giảm là giả
  thuyết mở**, cả hai kết quả đều chấp nhận được và báo cáo.
- **H_C2**: tín hiệu chênh lệch giữa hai tầng thân (perturbation) lớn hơn
  nhiễu số do halving dt ≥ 10× (cơ sở: H_A1 p≥2 ⇒ mỗi halving giảm nhiễu
  ≥ 4×; hệ số 10 là dự phòng đã đăng ký).
- **H_D1**: với IC nạp từ chính DE440, `E_pos[0] == 0` exact tại mọi tầng
  (đã đo ở T1/T2 Phase 4; tái xác nhận ở T3/T4).
- **H_D2**: ở 7 d, số liệu T1/T2 nằm trong ngưỡng stage9/stage10 **đã
  nghiệm thu** (không đụng lại ngưỡng). T3/T4: **không có ngưỡng sẵn** —
  chỉ ghi số + diễn giải (xem §6).
- **H_E1**: E_pos(t) tăng theo thời gian horizon nhưng **hình dạng tăng
  trưởng (tuyến tính / lũy thừa / exponential …) không được giả định
  trước** — chỉ chọn mô
  tả nếu dữ liệu phân biệt được các ứng viên theo tiêu chí đã đăng ký (§6).
- **H_E2**: mọi horizon đạt **structural gate** (§6b — hoàn tất, finite,
  tái lập, conservation pre-registered, provenance, không numerical
  failure; **không** có error threshold) trước khi sang horizon dài hơn
  (1 d → 30 d → 90 d → 365 d).

**Không có** giả thuyết về hiệu năng, ML, điều hướng tàu, thiên văn ngoài
lệch — xem §8.

## 3. Experiment matrix

### 3.0 Biến đóng băng toàn cục (Step 2 — Controls chung)

| Biến | Giá trị đóng băng |
|---|---|
| epoch | `epoch_jd = 2451545.0` (J2000), `time_scale = TDB` |
| frame model | `ACTIVE_BODIES_BARYCENTRIC` |
| gốc so sánh | SSB(0) tham chiếu, recenter theo mẫu qua `compare_trajectory` (không sửa pipeline) |
| units | m, m/s, s (đầu ra); km/km/s chỉ ở biên SPICE (Phase 4) |
| reference dataset | `de440s.bsp` + manifest hashes đã nghiệm thu; **de440s = chuẩn Phase 5 — không tải/đối chiếu `de440.bsp`; không hardcode filename — manifest abstraction quyết định** |
| kernel policy | spot-compare `de440.bsp` = optional future diagnostic, **ngoài Phase 5** (§10.3) |
| guard_m | 1.0 (mặc định, không phải biến thí nghiệm) |
| RNG | không có (`random_seed_if_any = None` — tất định thuần) |
| GM | `GM_BY_BODY` (DE440, không đổi) |
| sample grid | `times = step × dt` (không tích lũy); `sample_every` chốt từng experiment |
| replication | mỗi cấu hình chuẩn chạy **2 lần** → `np.array_equal` + `config_hash` + `output_hash` bằng nhau |
| runtime | `time.perf_counter` ghi metadata, **không** tham gia determinism, không tối ưu |
| thứ tự chạy | 13 bước đã phê duyệt (§11): gaps → Gate A+B → A1+B synthetic → freeze baseline → A2 → E(1 d, 30 d) → freeze operational gates → C → D → E(90 d) → gate → E(365 d) → report |

### 3.1 Ma trận

| Exp | Biến độc lập | Kiểm soát | Cấu hình | Duration | Metrics | Quan sát kỳ vọng |
|---|---|---|---|---|---|---|
| **A1** | dt: n ∈ {25, 50, 100, 200}, `dt = (P/4)/n` | IC hai-body tròn **analytic** (Sun–Earth @1 AU), 2 tích phân, epoch J2000, cùng `horizon = P/4` | Sun, Earth; `endpoint_error` vs nghiệm đúng `exact_at` | P/4 (~91.3 d) | sai số endpoint (m); bậc quan sát p; sàn roundoff | lỗi giảm nghiêm ngặt; RK4 p∈[3.5,4.5], Verlet p∈[1.5,2.5]; ≫ 3.3e-5 m |
| **A2** | dt ∈ {P_SE/500, P_SE/1000, P_SE/2000, P_SE/4000} | IC **DE440-derived** (`ic.py`), Sun–Earth, `sample_every=1`, cùng epoch/duration, RK4 | Sun, Earth (T1) | 7 d (đã nghiệm thu môi trường) | E_pos/E_vel/E_rel vs DE440 (mean/median/p95/max); `relative_energy_error` | báo cáo 3 phần: observed numerical convergence regime (tỷ số D_k/D_{k+1} từng halving) / plateau-floor regime / interpretation; sàn ≠ lỗi tích phân; `E_pos[0]==0` |
| **B** | tích phân ∈ {verlet, rk4} trên **cùng lưới dt** (dùng chung dataset A1 + lưới P_SE/{500..4000} cánh RK4/Verlet) | y hệt A: cùng IC, epoch, duration, dt, sample grid, reference | như A1 (synthetic) + A2 (ref) | như A1/A2 | E_pos/E_vel vs nghiệm đúng & vs DE440; năng lượng (max osc, drift slope); động lượng góc (biên, drift); runtime (informational); bậc hội tụ | Verlet: dao động có biên, không trôi; RK4: phẳng hơn; cùng dt RK4 chính xác hơn mỗi điểm; **không xếp hạng tổng thể** |
| **C** | tầng thân: **T1** Sun–Earth · **T2** Sun–Earth–Moon · **T3** Sun–Mercury–Venus–Earth–Moon–Mars · **T4** = **10 thân chuẩn MASTERPLAN** (Sun, Mercury, Venus, Earth, Moon, Mars, Jupiter, Saturn, Uranus, Neptune — Pluto **không** thuộc T4, chỉ là selected-body extension §10.1) | **một dt duy nhất cho mọi tầng** = `P_EM/1000 ≈ 2360.5915 s` (chốt theo động lực nhanh nhất = Mặt Trăng); IC DE440-derived cùng epoch; `sample_every` chốt (100) — điều khiển dt/2 dùng `sample_every = 200` cho lưới mẫu trùng khớp; cùng reference; + **2 điều khiển halving pre-registered, LUÔN chạy** (T2 & T3 ở dt/2) | 4 tier + 2 điều khiển | 30 d | Δ Earth position giữa các tầng (`trajectory_difference`, lưới giống hệt); Δ Moon (T2+); Δ barycentre tập con; E_pos/E_vel vs DE440 mỗi tầng; biên năng lượng/động lượng góc | criterion đóng băng: `signal ≥ 10 × control`, không sửa sau khi thấy số; control = tín hiệu halving từ điều khiển đã đăng ký (signal T4↔T3 mượn control T3 — pre-registered, ghi chú trong record); nếu vẫn < 10× → báo **"signal not numerically resolved"**, không ép diễn giải vật lý |
| **D** | cấu hình: T1, T2, T3 | **không sửa pipeline Phase 4**; IC `ic.py`; tích phân RK4; dt = P_SE/1000 (T1) / P_EM/1000 (T2, T3); epoch J2000; record đủ field §6d | T1@7 d, T2@7 d (ngưỡng stage9/10 cũ), T3@7 d (report-only); thêm T1–T3 @30 d **report-only** | 7 d (+30 d report-only) | pos: mean/median/p95/max; vel: mean/median/p95/max; provenance đầy đủ | T1@7 d + T2@7 d **formal** vào ngưỡng Phase-4 đã nghiệm thu; T3@7 d + mọi run @30 d **report-only**: chỉ ghi số + diễn giải, **không bịa ngưỡng mới** (không hậu-học); mọi record đối chiếu manifest kernel |
| **E** | horizon H ∈ {1 d, 30 d, 90 d, 365 d} | cấu hình T2 (SEM), IC DE440-derived, RK4, dt = P_EM/1000, `sample_every = round(86400/dt) = 37` (≈1 mẫu/ngày, lưới step×dt), epoch J2000 | Sun, Earth, Moon | 1 d → 30 d → 90 d → 365 d gated, **mỗi bước chỉ qua structural gate** | E_pos(t), E_vel(t) từng mẫu vs DE440 (**mô tả thuần**); `relative_energy_error` series; động lượng góc; (nếu dữ liệu phân biệt ứng viên) mô tả tăng trưởng §6e | **KHÔNG có error-acceptance threshold** — gate = 6 hạng mục §6b (completion, finite/không failure, tái lập, conservation pre-registered, provenance); gate_FAIL ⇒ dừng chuỗi, điều tra trước khi tiếp; growth-law chỉ classify nếu dữ liệu phân biệt được ứng viên |

## 4. Initial-condition policy (Chính sách IC — Step 2, bắt buộc)

- **Nhóm A (phương pháp số: A1, phần synthetic của B):** IC **analytic**
  (`make_circular_two_body_ic`, nghiệm đúng `exact_at`). Ở đây sai số =
  **lỗi tích phân thuần** — không đụng DE440.
- **Nhóm B (tham chiếu: A2, C, D, E, cánh ref của B):** IC **DE440-derived**
  (`reference_state_to_model_state`, `ic_source` bắt buộc trong record).
  Ở đây chênh lệch phản ánh tổng của model + IC + tham chiếu — **không
  bao giờ** gọi thuần "integrator error".
- **Cấm trộn:** không so IC tổng hợp với DE440 rồi gán sai số vào tích
  phân; không so IC DE440 với nghiệm tròn analytic. Mỗi record ghi rõ
  `initial_condition_source ∈ {analytic-circular, reference-ingested}`.

## 5. Timestep policy (Chính sách timestep — Step 2, giải thích khác biệt theo hệ)

- **Sun–Earth (T1):** động lực chậm (P_SE ≈ 3.156e7 s). Nhánh chuẩn:
  `dt = P_SE/1000 ≈ 31558 s` (đã đo Phase 4); lưới A2 chia đôi quanh chuẩn
  (500/1000/2000/4000). Nhánh synthetic A1: `dt = (P/4)/n` để ước lượng bậc
  chính xác.
- **Sun–Earth–Moon (T2):** động lực nhanh nhất quyết định dt:
  `dt = P_EM/1000 ≈ 2360.5915 s`. **Đã chứng minh Phase 3:** mượn dt
  P_SE/1000 làm năng lượng xấu đi có kiểm chứng được (test moon_timestep).
- **Hệ lớn (T3/T4):** dt theo **động lực nhanh nhất còn lại trong cấu
  hình** (T3/T4 vẫn có Moon → P_EM/1000). Nếu sau này bỏ Moon khỏi tier,
  dt theo thân nhanh nhất (Mercury, P ≈ 7.6e6 s) — công thức chung:
  `dt = min_i P_i / 1000`, nơi `P_i` là chu kỳ của thân có P nhỏ nhất.
  **Một dt cho mọi tầng trong Experiment C** để tín hiệu khác tầng không bị
  lẫn sai số.dt.

## 6. Acceptance criteria (Tiêu chí chấp nhận)

**(a) Hội tụ số thành công (numerical convergence):**
1. sai số giảm nghiêm ngặt dọc lưới dt đã đóng băng (A1);
2. bậc quan sát `p` trong cửa sổ [3.5, 4.5] (RK4) / [1.5, 2.5] (Verlet) —
   *cơ sở: lý thuyết bậc phương pháp*;
3. sai số cuối cùng > 1000 × sàn roundoff phân tích (`3.3e-5 m` @1 AU —
   sàn **tái dùng nguyên vẹn** HĐ Phase 1–2: `tests/numerical/test_convergence.py`
   với `1.5e11 × 2⁻⁵²`; tính lại minh bạch, không tạo sàn mới, không sửa
   sàn cho khớp kết quả);
4. nhánh DE440 (A2): **KHÔNG có ngưỡng `2^p` trên tổng chênh lệch** —
   nhiệm vụ = báo cáo 3 phần: *observed numerical convergence regime*
   (tỷ số D_k/D_{k+1} từng halving, trong vùng tích phân còn phân giải),
   *plateau/floor regime* (vùng bẹt), *interpretation* (sàn
   model/tham chiếu; plateau **không** phải failed convergence; sàn
   không gọi là lỗi tích phân). Nhận diện floor — quy ước mô tả đóng băng
   trước khi chạy: một interval là floor-dominated khi D_k/D_{k+1} < 2
   (halving không phân giải nổi thành phần bậc ≥ 1).

**(b) Tích phân ổn định (stable integration) — structural gates:**
- mọi mảng **finite** (không NaN/inf); không chạm guard close-encounter
  ngoài các case đã biết (Moon); run **hoàn tất đúng `n_steps`** đã cấu
  hình; không có numerical failure;
- Verlet (cánh B / A1-synthetic): `drift` năng lượng trên một P < 1e-12
  (ngưỡng Phase 3 đã nghiệm thu), dao động biên theo ngưỡng N1 đã đo;
- **chuỗi horizon E — KHÔNG có error-acceptance threshold** (hiệu chỉnh
  người dùng #1). Gate mỗi horizon = 6 hạng mục **pre-registered, suy ra
  từ HĐ Phase 1–3 + tích lũy phân tích, KHÔNG derive từ lỗi quan sát của
  chính E**:
  1. *numerical stability*: mọi mảng finite;
  2. *deterministic reproducibility*: 2 lần chạy → `np.array_equal` +
     `config_hash` + `output_hash` bằng nhau;
  3. *successful completion*: đủ `n_steps`, lưới mẫu đúng `step×dt`;
  4. *conservation diagnostics* (stability gate, không phải accuracy):
     `max|dE/E0| ≤ 1e-6` (cơ sở: Phase-3 đo 2.58e-15 @ 2·P_EM RK4
     rule-dt; quy chiếu tuyến tính tới 365 d ≈ 1.7e-14 → dự phòng ~6×10⁷,
     gate chỉ bắt bùng nổ — accuracy E_pos/E_vel báo cáo mô tả thuần);
     `max|P_rel| ≤ 1e-10` (≥ 3 cấp trên cận tích lũy √N·eps ≈ 2.6e-14);
     `max|ΔL|/|L0| ≤ 1e-8` (≥ 10⁴ trên mức đo Phase 3 RK4 8.5e-13/quỹ đạo);
  5. *valid metadata/provenance*: đủ field §6d + kernel hashes == manifest;
  6. *absence of numerical failure* (xem mục 1).
  Mọi bound **đóng băng tại tài liệu này, trước bất kỳ run E nào** —
  không bao giờ sửa sau khi thấy số; vượt bound = báo *stability
  limitation* + điều tra, không nới ngưỡng. E_pos/E_vel(t) **không bao
  giờ** bị judged bằng ngưỡng derived từ chính nó. Dừng tiến trình
  1→30→90→365 d nếu fail, điều tra nguyên nhân trước khi tiếp.

**(c) So sánh hợp lệ (valid comparison):**
- `assert_compatible` pass (7 lớp); `ic_source` đúng nhóm chính sách §4;
- `E_pos[0] == 0` chính xác với IC DE440-derived;
- record đủ provenance: kernel hashes/coverage == manifest (test Phase 4
  đã có); frame/center/time/units đúng hợp đồng;
- **không** diễn giải tách riêng "model error / IC error / integration
  error / reference difference" trừ khi biến đó được thí nghiệm kiểm soát
  tường minh (A1 kiểm soát IC+tham chiếu → được gọi là integration error;
  A2/C/D/E **không được**).

**(d) Kết quả tái lập được (reproducible):**
- 2 lần chạy cùng config → `np.array_equal` trên mọi mảng, `config_hash`
  bằng nhau, `output_hash` bằng nhau;
- `output_hash` = SHA-256 của **bytes mảng** (times/positions/velocities
  float64, thứ tự cố định) — **không** hash bytes npz (zip timestamp);
- record máy-đọc-được với đủ các field quy định (§ reproducibility của
  brief): experiment_id, epoch, bodies, initial_condition_source,
  integrator, timestep, duration, reference_dataset, reference_frame,
  reference_origin, time_scale, units, software/version, configuration_hash,
  output_hash.

**(e) Phân loại mô tả tăng trưởng (E) — mô tả, KHÔNG phải acceptance):**
- Ứng viên: tuyến tính `c·t`, lũy thừa `c·t^α`, exponential `c·e^{λt}`
  (fit trên mẫu `t > 0`);
- phân biệt được ⇔ SSE của ứng viên tốt nhất ≤ 0.1 × SSE của ứng viên
  kế; ngược lại ghi "không phân biệt được — chỉ báo cáo series";
- quy ước này **mô tả**, không gate, không quyết định pass/fail horizon;
  không giả định hình dạng tăng trưởng trước dữ liệu (hiệu chỉnh #1).

## 7. Required implementation gaps (Chỉ những thay đổi code tối thiểu)

| # | Thay đổi | File | Lý do (chỉ cần khi được duyệt) |
|---|---|---|---|
| 1 | Di trú `angular_momentum_series` từ `tests/numerical/test_conservation.py` về `src/solar_ephemeris/analysis/` (cùng công thức, không đổi hành vi; test cũ import lại hàm mới) | `src/…/analysis/momentum.py` (mới) + sửa 1 test import | A/B/E cần chẩn đoán động lượng góc dùng lại được |
| 2 | Record thí nghiệm: writer JSON bọc `RunRecord.to_dict()` + `ComparisonResult.to_dict()` + `experiment_id`, `output_hash`, `initial_condition_source`, `threshold/measured/interpretation` | `experiments/_common.py` (mới) | brief đòi record chuẩn hóa; KHÔNG sửa RunRecord Phase 1–3 |
| 3 | Harness thí nghiệm: `run_a.py` … `run_e.py` (hoặc 1 driver có subcommand), mỗi file chạy đúng grid đã đóng băng, ghi `results/experiment_<X>/*.json`; kèm helper: `observed_orders`, `endpoint_error` (công thức nguyên vẹn từ tests), runtime `perf_counter`, chọn ứng viên mô tả tăng trưởng (E) | `experiments/` (mới) | không có cách nào chạy grid hàng loạt + record nhất quán |
| 4 | Test hợp đồng cho record schema + output_hash tất định + grid đóng băng khớp tài liệu này | `tests/unit/test_experiment_contract.py` (mới) | chống trôi grid/ngưỡng (R10) |

**KHÔNG sửa:** `engine`, `integrators`, `ephemeris/*` (toàn bộ pipeline
DE440), `comparison`, `ic`, mapping/manifest, test Phase 1–4 hiện hữu
(trừ 1 chỗ import hàm di trú ở mục 1).

## 8. Scope-risk audit

| Rủi ro bị cấm | Trạng thái | Bằng chứng |
|---|---|---|
| AI / ML / AI prediction | **Không có** | không fit "mô hình học máy", không "AI prediction" dưới mọi tên; hồi quy nhỏ trong E chỉ là mô tả tăng trưởng có quy ước §6e, không huấn luyện |
| Điều hướng tàu (spacecraft navigation) | **Không có** | không có quỹ đạo tên lửa/định hướng/điều khiển |
| Web application | **Không có** | output = JSON/CSV số liệu + markdown |
| Thiên văn không liên quan | **Không có** | mọi số liệu quanh 5 câu hỏi Q1–Q5, hệ Mặt Trời |
| Visualization-first | **Không có** | output = JSON/CSV số liệu; **không** plot pipeline; viz chỉ được thêm nếu **trực tiếp phục vụ một kết quả khoa học đã hoàn thành** — không có trong Phase 5 này |
| Tối ưu hiệu năng non suy | **Không có** | runtime chỉ ghi nhận (informational); **chỉ optimize sau khi có profiling** — không có trong Phase 5 này; không cache acceleration, không đổi stepper |
| Sweep/ML/optimization Phase-4 bị cấm hồi Phase 4 | nay **hợp pháp trong Phase 5** vì brief yêu cầu thí nghiệm; phạm vi = `experiments/` mới + 4 gaps ở §7, không hơn |

## 9. Nguy cơ khoa học (Scientific risks)

- **R-S1 — Trộn diễn giải IC:** nhóm analytic vs DE440 bị gộp thành một
  "sai số" → kiểm soát bằng §4 + trường record bắt buộc.
- **R-S2 — Nhịu số ẩn trong tín hiệu tầng thân (C):** dt khác nhau giữa
  tầng sẽ giả lập "perturbation" → dt đồng nhất mọi tầng + điều khiển
  halving + ngưỡng ≥10× đã đăng ký; không đạt → kết luận lẫn lộn, chạy lại
  dt/2 (không được sửa ngưỡng).
- **R-S3 — Ngưỡng hậu-học (after-the-fact):** → mọi acceptance number
  chỉ đến từ (i) ngưỡng Phase 1–3 đã nghiệm thu, (ii) suy diễn/lý thuyết
  bậc đã đăng ký, (iii) hằng số đóng băng trong tài liệu này **TRƯỚC**
  khi chạy; E không có error threshold (§6b); không bao giờ derive ngưỡng
  từ kết quả mà chính ngưỡng đó judging; mọi ngưỡng ghi
  threshold/measured/reason.
- **R-S4 — Dũng sai số DE440 thành "lỗi tích phân"** ở A2/C/D/E → cấm
  trong §6c; chỉ A1 được quyền gọi sai số là integration error.
- **R-S5 — Horizon dài vượt stability thật:** gate nối tiếp 1→30→90→365 d;
  fail = dừng, không "chạy thử xem sao".
- **R-S6 — Floor roundoff:** mọi ước lượng bậc phải chứng minh sai số
  > 1000×3.3e-5 m (đã có test sẵn patterns).
- **R-S7 — Cost tính toán:** mọi grid ước lượng vài nghìn–vài chục nghìn
  bước × ≤11 thân → không có nhu cầu song song/optimization (củng cố §8).
- **R-S8 — Mục mở Phase 4** (so `de440.bsp` vs `de440s.bsp`): **đã chốt
  (hiệu chỉnh #4) — ngoài phạm vi Phase 5**, chỉ là optional future
  diagnostic; không tải, không benchmark, không phụ thuộc filename
  (manifest abstraction quyết định); xem §10.3.

## 10. Điểm mơ hồ của MASTERPLAN — trạng thái giải quyết khi phê duyệt

1. **Tier T3/T4:** Moon **giữ trong T3** (Earth cần hệ Trái Đất hoàn
   chỉnh để so DE440). **T4 = CHỐT 10 thân** chuẩn MASTERPLAN (Sun,
   Mercury, Venus, Earth, Moon, Mars, Jupiter, Saturn, Uranus, Neptune) —
   **hiệu chỉnh #3**. **Pluto = selected-body extension**, không phải core
   body: registry vẫn giữ 11 thân (mapping Pluto đã exercise Phase 2),
   Phase 5 **không** chạy Pluto; muốn chạy sau phải sửa thiết kế + test
   hợp đồng (không âm thầm thêm thân).
2. **E dùng tích phân nào:** giữ **RK4 duy nhất** (B đã so Verlet/RK4;
   E hỏi horizon, không hỏi tích phân) — không thay đổi.
3. **Mục mở Phase 4 (de440 vs de440s):** ✅ **CHỐT — ngoài Phase 5**
   (hiệu chỉnh #4): chỉ optional future diagnostic, không tải
   `de440.bsp`, không benchmark; manifest abstraction quyết định.
4. **30 d report-only ở D:** ✅ **CHỐT — giữ nguyên**: không pass/fail,
   chỉ ghi số + diễn giải; không bịa ngưỡng hậu-học cho 30 d.
5. **phase5-results.md:** ✅ **CHỐT — BẮT BUỘC** theo yêu cầu phê duyệt
   (§12, §11 bước 13).

---

## 11. Thứ tự triển khai (đã phê duyệt — 13 bước, không đảo)

```text
1.  Minimal infrastructure gaps (§7, 4 mục, gồm test hợp đồng)
2.  Gate A + Gate B
3.  A1 + B synthetic
4.  Freeze numerical baseline
5.  A2
6.  E: 1 day → 30 day
7.  Freeze/calibrate chỉ các operational gate được phép tường minh
    (structural gates §6b — đã đóng băng sẵn, không derive ngưỡng mới
    từ lỗi quan sát)
8.  C
9.  D
10. E: 90 days
11. Gate
12. E: 365 days
13. Final analysis/report → phase5-results.md (§12)
```

- **Không đảo thứ tự** chỉ vì kết quả sớm bất ngờ.
- **Không tinh chỉnh thiết kế sau khi thấy kết quả**, trừ khi phát hiện
  **defect số thật** — khi đó phải ghi rõ trong record + test.
- Cánh ref-lattice của B (Verlet trên lưới `P_SE/{500,1000,2000,4000}`)
  chạy trong bước 3 (lattice xác định trước, không phụ thuộc A2); record
  B hoàn tất sau bước 5 khi đã có số A2.
- Bước 11 "Gate" = đối chiếu §13 (các mục hợp lệ tại thời điểm đó);
  bước 13 chạy checklist đầy đủ.

---

## 12. Yêu cầu báo cáo cuối (phase5-results.md — BẮT BUỘC)

`docs/methodology/phase5-results.md` viết **sau khi thí nghiệm hoàn
tất**, tách **5 loại kết quả thành 5 mục riêng**:

1. **numerical error** — chỉ A1 (analytic IC, tham chiếu đúng) được dùng
   thuật ngữ này;
2. **model/reference discrepancy** — A2/C/D/E: **không bao giờ** chuyển
   thành claim "integrator accuracy";
3. **physical perturbation signal** — Experiment C (tier signals);
4. **roundoff/precision limits** — sàn Phase 1–2 (`3.3e-5 m` @1 AU);
5. **stability limitations** — nếu có gate §6b vượt / failure nào.

---

## 13. Final Phase 5 gate (checklist — chỉ báo cáo PASS khi đủ hết)

```text
[ ] A1 completed
[ ] A2 completed
[ ] B completed
[ ] C completed
[ ] D completed
[ ] E completed through the allowed horizon
[ ] all results are reproducible
[ ] all experiment metadata are recorded
[ ] thresholds were frozen before judging results
[ ] no post-hoc acceptance threshold was introduced
[ ] numerical error is separated from model/reference discrepancy
[ ] scientific conclusions are supported by measured results
[ ] phase5-results.md exists
[ ] all existing tests remain green
```

Sau báo cáo chấp nhận Phase 5 → **STOP**. Không tự động bắt đầu feature
mới.
