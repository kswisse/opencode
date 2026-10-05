# Hệ Trái Đất–Mặt Trăng (Phase 3)

Tài liệu này là **hợp đồng** của Phase 3 — mở rộng của `units-and-frames.md`
(Phase 1–2), không thay thế nó. Code và test bám vào đây; sửa tài liệu nghĩa
là sửa hợp đồng, phải kèm sửa test.

Phase 4 (chuẩn hoá khung/thời gian, so sánh DE440, I/O tham chiếu) **chưa
bắt đầu** — không có phép biến đổi khung nào, không có I/O ephemeris nào,
không có validation nào trong phạm vi này.

## 1. Điều kiện đầu vào (IC)

### 1.1 `make_sun_earth_moon_ic()` — Mô hình B (3 thân)

Công thức, theo đúng thứ tự tính (`simulation/initial_conditions.py`):

```
ω_EMB = sqrt((GM_S + GM_EM) / R³)          # quỹ đạo tròn của EMB quanh Mặt Trời
r_EMB = (+R, 0, 0),  v_EMB = (0, ω_EMB·R, 0)
d₀    = (a, 0, 0)                          # a = EARTH_MOON_DISTANCE_M = 3.844e8 (tham số mô hình)
f_E   = GM_E / GM_EM,  f_M = GM_M / GM_EM
r_E   = r_EMB − f_M·d₀,   v_E = v_EMB − f_M·ω_EM·d₀
r_M   = r_EMB + f_E·d₀,   v_M = v_EMB + f_E·ω_EM·d₀
ω_EM  = sqrt(GM_EM / a³)                   # quỹ đạo tròn của Mặt Trăng quanh Trái Đất
r_S   = −(GM_EM/GM_S)·r_EMB,  v_S = −(GM_EM/GM_S)·v_EMB   # ép COM = 0 đúng theo số
```

Bắt buộc nội tại (test `test_initial_conditions.py` khoá):

- COM của hệ = 0 tới mức dấu (residual ~3.5e-18 chuẩn hoá).
- Khoảng cách |r_M − r_E| = `a` chính xác; vận tốc tương đối
  |v_M − v_E| = `sqrt(GM_EM/a)` = **1024.546847 m/s**, vuông góc với vector
  vị trí (quỹ đạo tròn).
- Hàng Sun/EMB của mô hình B **trùng với** IC hai thân của mô hình A
  (lumped) tới mức dấu — đây là cơ sở so sánh "cùng điểm xuất phát".
- Chiều quay khớp công thức của `make_circular_orbit` (thân 1 ở +x, vận
  tốc +y) để mọi IC trong dự án cùng một hệ quy ước.

Giá trị đặc trưng (đo 2026-10-01):

| Đại lượng | Giá trị |
|---|---|
| P_EM (chu kỳ mô hình Trái Đất–Mặt Trăng) | 27.2846058 ngày |
| P_EMB (chu kỳ EMB quanh Mặt Trời) | 365.2563431 ngày |
| \|v_EM\| tại IC | 1024.546847 m/s |
| Độ lệch Trái Đất so với EMB (amplitude) | (GM_M/GM_EM)·a = 4.671e6 m |
| Lực hấp dẫn giữa cặp so với thủy triều Mặt Trời | Mặt Trời làm yếu đi 1.12 % |

### 1.2 `make_circular_two_body_ic()` — Mô hình A

Dùng cho A_naive (`Sun + Earth`, GM Trái Đất) và A_lumped (`Sun + EMB`,
GM_E + GM_M). Đây là quỹ đạo hai thân chính xác của **GM đã gộp**, nên:

- **Hệ quyển hệ số 5.5 km (đã đo, đã ghi):** tại epoch, "Trái Đất" của
  A_naive nằm ở vị trí quỹ đạo GM_E, còn EMB của Mô hình B nằm ở vị trí
  quỹ đạo GM_EM — khác nhau `R·(GM_EM − GM_E)/GM_S` ≈ **5526.6 m** (số đo:
  hàng Sun của hai mô hình lệch đúng từng này mét, COM=0 nên hàng Trái Đất
  lệch ngược lại). Đây là khác biệt **định nghĩa khối lượng**, không phải
  tín hiệu động lực. Vì vậy A_lumped được chạy song song: so sánh
  EMB-vs-EMB bắt đầu **đúng bằng 0**.
- Tại epoch, độ lệch Trái Đất thật (Mô hình B) so với "Trái Đất" của
  A_naive = độ lệch Trái Đất so với EMB (4.671e6 m) − hệ số khung (5.5e3 m)
  ≈ **4.665e6 m** — test `test_naive_frame_systematic_at_epoch` khoá cả ba
  con số này.

## 2. Thí nghiệm quấy nhiễu của Mặt Trăng

Ba mô hình, **một lưới mẫu duy nhất** (`dt` giống hệt, `duration` giống
hệt, `sample_every` giống hệt — `np.array_equal` trên `times`, yêu cầu
cứng của `trajectory_difference`):

| Mô hình | Thân | Vai trò |
|---|---|---|
| B | Sun + Earth + Moon | đối tượng đo |
| A_naive | Sun + Earth (GM_E) | đường cơ sở "không có Mặt Trăng" |
| A_lumped | Sun + EMB (GM_E+GM_M) | so sánh công bằng về mặt hệ số |

Định nghĩa sai số (đoạn 60 ngày, RK4, `dt = P_EM/1000`, mẫu mỗi 10 bước):

```
Δ_earth(t) = r_Earth^B − r_Earth^A_naive
Δ_emb(t)   = r_EMB^B     − r_EMB^A_lumped      (r_EMB^B tính bằng barycenter Trái Đất+Mặt Trăng)
```

Kết quả đo (khoảng chặn của test là 10–100× số đo, không nới lỏng):

| Đại ölçü | Số đo | Ngưỡng test |
|---|---|---|
| max \|Δ_earth\| | 4.7025e6 m = 3.143e-5 AU | 4.6–4.8e6 m; /AU 2.9–3.3e-5 |
| max \|Δ_emb\| | 4584.1 m (và cũng là giá trị cuối; trung bình 1579 m) | < 1e4 m |
| tỉ lệ Δ_emb/Δ_earth | 9.75e-4 | < 2e-3 |
| Δ_emb tại t=0 | đúng 0.0 | array_equal 0 |
| thành phần z của Δ_earth | đúng 0 (mặt phẳng giữ nguyên) | == 0 |
| tín hiệu có tiến triển? | ptp(\|Δ_earth\|) ≈ 6.8e4 m | > 1e3 m |

Diễn giải: Mặt Trăng kéo Trái Đất lệch vài nghìn km trong 60 ngày
(≈3e-5 AU), trong khi quỹ đạo của EMB (tức hệ Trái Đất–Mặt Trăng gộp)
chỉ xê dịch ~4.6 km — đúng bản chất: quấy nhiễu nội bộ làm Trái Đất
"lắc" quanh EMB, không đẩy cả hệ đi đâu.

## 3. Ước lượng chu kỳ

Hai ước lượng, hai câu hỏi khác nhau (`analysis/orbit.py`):

- **`angular_period` (chính):** quấn góc của vector vị trí tương đối,
 slope tối thiểu bình phương → **chu kỳ quỹ đạo**. Không nhạy với "thở"
  khoảng cách.
- **`radial_period` (phụ):** khoảng cách giữa các cực tiểu khoảng cách
  (đã nội suy đỉnh-parabol). Trên mô hình này Mặt Trăng tạo **hai cực tiểu
  mỗi quỹ đạo** (khoảng cách giãn nở do thủy triều Mặt Trời), nên nó trả
  về **14.36 ngày** trong khi chu kỳ quỹ đạo là 27.03 ngày — test
  `test_lunar_orbit_diagnostics_60d` khoá tỉ lệ 0.45–0.60 để diễn giải
  này luôn kiểm tra được.

Số đo 60 ngày: angular period **27.0255 d** (cửa sổ test 26.5–27.6 d, mô
hình 27.2846 d — lệch 0.9 %, nằm trong ảnh hưởng của thủy triều lẫn nhau
và chỉnh động của hệ ba thân), amplitude khoảng cách **0.0354**.

## 4. Quy tắc timestep & an toàn

**Quy tắc Phase 3:** `dt ≤ P_EM/1000 ≈ 2357 s` (≥1000 mẫu/quỹ đạo Mặt
Trăng). Động lực chậm nhất phải được phân giải là quỹ đạo Mặt Trăng, không
phải quỹ đạo Trái Đất–Mặt Trời.

Mượn `dt = P_SE/1000 ≈ 31558 s` (quy tắc Phase 2) chỉ cho **74.7 mẫu /
quỹ đạo Mặt Trăng**. Đo trên 2×P_EM, cùng endpoint:

| | dt = P_EM/1000 | dt = P_SE/1000 | tỉ lệ |
|---|---|---|---|
| max \|dE/E0\| RK4 | 2.58e-15 | 2.24e-11 | **8.7e3** |
| max \|dE/E0\| Verlet | 8.02e-12 | 1.25e-9 | **1.6e2** |
| angular period | 27.0255 d | 27.0038 d | lệch 0.08 % |

**Bài học đo được, ghi vào test:** chu kỳ gần như "mù" với bước sai
(0.08 % vẫn có vẻ ổn), còn **năng lượng nhạy gấp ~10³ lần** — ngưỡng
tính adequacy phải đặt ở năng lượng
(`test_period_is_blind_where_energy_sees`).

Nội suy bậc 4 hội tụ đúng bậc: tỉ lệ sai số endpoint khi halve dt đo được
16.0–17.9 (asymptotic = 16), test khoá [8, 32].

**An toàn:** `CloseEncounterError` / `guard_m` giữ nguyên từ Phase 1–2
(không nới lỏng). Test `test_close_encounter_guard_active_for_moon_config`
chứng minh guard nhạy với cấu hình có Mặt Trăng (guard 4e8 m > khoảng cách
3.844e8 m trips ngay lần tính lực đầu). Một defect nhỏ được sửa trong pass
này: thông báo lỗi guard từng chọn sai cặp thân (`r[i,i]=0` thắng
`argwhere`) — hành vi raise luôn đúng, chỉ message sai; giờ mask đường chéo
trước khi chọn chỉ số.

## 5. Bất biến & năng lượng

- **COM = 0:** tổng quán tính của hệ giữ ở gốc (residual chuẩn hoá
  < 1e-15 — số đo ~1e-17 trên 60 ngày).
- **Nhận diện EMB:** `r_EMB = −(GM_S/GM_EM)·r_S` đúng — sai số đo
  **6.1e-4 m** trên 60 ngày.
- **Bán kính EMB lệch quỹ đạo tròn ~3.06e-6 (≈450 m):** đây là **vật lý
  thật**, không phải lỗi tích phân — hấp dẫn Mặt Trăng phân kỳ trên trục
  Trái Đất–Mặt Trăng làm EMB không phải quỹ đạo Kepler chính xác, bậc
  (a/R)² ≈ 6.6e-6. Ngưỡng test 1e-5.
- **Năng lượng:** `analysis/energy.py::total_energy` đổi GM→kg **chỉ để
  ghi sổ** (chia cho G), không bao giờ quay lại đường tính lực — số đo
  tương đối với định nghĩa sách giáo khoa. RK4 60 ngày: 2.8e-15
  (ngưỡng 1e-12).

## 6. Determinism

- Cùng config + cùng IC → mảng `times/positions/velocities` **bitwise**
  giống hệt, cả trong bộ nhớ lẫn qua `run_to_file` → `load_run`
  (test 7 của requirement).
- `config_hash` khớp giữa config, `TrajectoryMeta` và `RunRecord`.
- So sánh liên-mô hình chỉ hợp lệ trên lưới bitwise giống nhau
  (`trajectory_difference` từ chối nếu khác — không bao giờ nội suy ngầm).

## 7. Bản đồ test (requirement → test)

| # | Yêu cầu | Test |
|---|---|---|
| 1 | cấu hình Sun-Earth-Moon VÀ Sun-Earth | `integration/test_sun_earth_moon.py::test_config_builds_for_both_required_body_sets` |
| 2 | từ chối thân lạ | `physics/test_moon_interaction.py::test_engine_rejects_unknown_body` |
| 3 | thứ tự thân theo config, vật lý bất biến thứ tự | `test_sun_earth_moon.py::test_body_order_follows_config` |
| 4 | GM Mặt Trăng đi qua registry→engine→traj đúng | `test_moon_interaction.py::test_engine_resolves_gm_in_config_order` + `test_sun_earth_moon.py::test_engine_and_trajectory_carry_exact_moon_gm` |
| 5 | trạng thái tương đối Trái Đất–Mặt Trăng | `test_sun_earth_moon.py::test_relative_state_at_epoch` |
| 6 | quán tính tâm điểm / EMB | `test_sun_earth_moon.py::test_barycentre_invariants` |
| 7 | determinism (nhớ + file) | `test_sun_earth_moon.py::test_determinism_*` |
| 8 | timestep an toàn | `numerical/test_moon_timestep.py` (7 test) |
| 9 | (prompt bị cắt — bao phủ bằng) quấy nhiễu + ổn định | `integration/test_moon_perturbation.py` (6 test) + `test_moon_timestep.py` |

Tương tác hấp dẫn có Mặt Trăng (golden từ vòng lặp Python độc lập,
không qua `einsum`):
`physics/test_moon_interaction.py` — 9 test, gồm Newton thứ 3 đúng dạng
**lực**: `GM_M·a_M(E) = −GM_E·a_E(M)` (so gia tốc trực tiếp là sai vật lý —
hệ số GM lệch ~81 lần; test ghi chú bẫy này).

## 8. Giới hạn

- IC là quỹ đạo tròn lý tưởng ở epoch J2000 giả tưởng — **không** phải
  trạng thái ephemeris thật; Phase 4 sẽ thay bằng trạng thái DE440.
- Mặt phẳng Trái Đất–Mặt Trăng đồng phẳng với quỹ đạo EMB (thành phần z
  của mọi khác biệt = 0) — mô hình hoá tối giản, có chủ đích.
- Chưa có hiệu ứng tương đối (relativity), áp suất bức xạ mặt trời,
  nhiễu hành tinh khác.
- Chưa có so sánh với quan sát/ephemeris tham chiếu (Phase 4).
