# Phase 4 — Đường ống tham chiếu JPL DE440 (JPL DE440 Reference Pipeline)

Tài liệu này là **hợp đồng** của Phase 4. Code và test bám vào đây; sửa tài
liệu nghĩa là sửa hợp đồng, phải kèm sửa test (test khớp tài liệu:
`tests/unit/test_phase4_doc_contract.py`). Số đo trong tài liệu lấy từ lần
chạy đo **2026-10-03** trên máy thực với kernel đã xác thực; mọi ngưỡng đều
ghi đủ *threshold / measured / reason* (checklist G).

**Cổng nghiệm thu (checklist A–B), từ `solar-ephemeris/`:**

| Cổng | Lệnh | Kết quả (2026-10-03) |
|---|---|---|
| A — bộ mặc định | `python -m pytest` | **324 passed, 26 deselected, 0 failed, 0 skipped, 0 xfailed** |
| B — kernel thật | `python -m pytest -m real_kernel` | **26 passed, 324 deselected, 0 failed, 0 skipped** |

Tổng 350 test. `deselected` ≠ `skip`: pattern do người dùng phê duyệt
(pyproject `addopts = "-m 'not real_kernel'"`), cổng B luôn chạy lại được
từng test khi có kernel.

---

## 1. Vì sao DE440 (why DE440)

- Yêu cầuMASTERPLAN Phase 4: **DE440 là canonical, không thay thế ngầm**
  (không DE441/DE442/Horizons/„nâng cấp giúp" — R6). Mọi kết quả phải
  trỏ về đúng **một file nhị phân** bằng sha256.
- File chuẩn: **`de440s.bsp`** (ADR-401): cùng bộ fit DE440 với `de440.bsp`,
  độ phủ 1849–2150 đủ cho so sánh Phase 4, gọn ~31 MB thay vì ~114 MB.
  JPL không phát biểu độ chính xác nào phân biệt hai file; NAIF khuyến nghị
  „ngắn nhất phủ đủ ngày tháng".
- Nguồn khoa học: Park et al. (2021), AJ 161:105, DOI
  10.3847/1538-3881/abd414. GM của bảng `physics/constants.py` cũng lấy từ
  DE440 — model và tham chiếu dùng **một nguồn khối lượng duy nhất**.
- DE440 là **tham chiếu/viện dẫn**, KHÔNG thay engine Newtonian của dự án:
  tích phân vẫn do `SimulationEngine` tự làm; SPICE chỉ dùng để nạp IC và
  tra cứu trạng thái so sánh.

## 2. Nguồn (source) & trích dẫn (provenance)

- URL: `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp`
- Ngày tải: `retrieval_date = 2026-10-03`.
- Trích dẫn đầy đủ nằm trong `kernel_manifest.py::DE440S_MANIFEST.source_citation`
  (NAIF generic SPK + Park et al. 2021) và được sao chép vào
  `ReferenceMetadata.source` của **mọi** kết quả.
- **Provenance 17 field** (`ReferenceMetadata.to_dict`): `reference_name`,
  `reference_version`, `source`, `kernel_filename`, `kernel_md5`,
  `kernel_sha256`, `size_bytes`, `retrieval_date`, `kernel_coverage`,
  `body_ids`, `reference_frame`, `reference_center`, `time_standard`,
  `native_position_unit`, `native_velocity_unit`, `spice_version`,
  `software_version`. Không API nào trả về „sáu con số trần": mọi trạng thái
  là `ReferenceState` (frozen dataclass) kèm `provenance`.
- Bản ghi so sánh: `ComparisonResult.to_dict()` → `comparison_record.json`
  gồm cả phía model (`config_hash`, `ic_source`, tích phân, dt…) và chuỗi
  `transform`. Bản ghi của lần nghiệm thu:
  `docs/methodology/phase4_comparison_record.json` (Sun–Earth–Moon, 9252 B).

## 3. Danh tính kernel & checksum (kernel identity & checksum)

Bảng ghim trong repo: `src/solar_ephemeris/ephemeris/kernel_manifest.py`:

| Field | Giá trị |
|---|---|
| `filename` | `de440s.bsp` |
| `size_bytes` | `32726016` |
| `md5` | `3917ee56769db332790c751e2168843d` (đối chiếu NAIF `aa_checksums.txt`) |
| `sha256` | `c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2` |

Kiểm tra **tại lúc nạp** (`verify_kernel` → `KernelIntegrityError`, luôn kèm
„download from https://naif.jpl.nasa.gov…"):

1. file tồn tại → 2. size khớp → 3. MD5 khớp → 4. SHA-256 khớp;
5. `spkobj` == danh sách `body_ids` của manifest;
6. hợp nhất `spkcov` == `coverage_et` của manifest. Sai lệch nào cũng hủy nạp
   (`unload` nếu đã `furnsh`) — không bao giờ „tải được là dùng".

Test từ chối đã đo: file thiếu (lỗi kèm hướng dẫn tải), cắt cụt 4096 B
(`size mismatch`), đổi 1 byte cùng kích thước (`MD5 mismatch`),
tên `de441.bsp` bị manifest từ chối (`not a DE440 kernel`, R6).

## 4. Coverage (phạm vi thời gian)

- `spkcov` đo được (union 14 target, **cùng giá trị từng target**):
  ET `[-4734072000.0, 4735368000.0]` s TDB ↔ JD `[2396752.5, 2506352.5]`
  ↔ **1849-12-26 → 2150-01-22**. Khớp tuyệt đối với manifest
  (so đúng `==` trên float, không dùng xấp xỉ).
- `Coverage` là khoảng đóng; 5 biên được test: inside / exact-lower /
  exact-upper / outside-lower / outside-upper → ngoài là `CoverageError`
  „refusing to extrapolate" (không bao giờ nội suy ngoài).
- Fixture ghi sẵn: 12 mẫu **hàng ngày** × 12 body, cửa sổ ET
  `[-86400.0, 864000.0]` (−1 d … +10 d quanh J2000), 35504 B, schema v1.
- `spkcov(path, 0)` rỗng (segment gốc không có ở ID 0) — truy vấn luôn theo
  target thật.

## 5. Body IDs (bảng ánh xạ)

`ephemeris/mapping.py` — bảng đóng, không đoán theo chỉ số, sai là raise
(`UnknownBodyMappingError`):

| Body | NAIF | Body | NAIF |
|---|---|---|---|
| Sun | 10 | Mars | 4 |
| Mercury | 199 | Jupiter | 5 |
| Venus | 299 | Saturn | 6 |
| Earth | **399** | Uranus | 7 |
| Moon | **301** | Neptune | 8 |
| EMB | 3 | Pluto | 9 |

- `Earth → 399` (Trái Đất rắn + khí quyển), **không** phải 3 (EMB) — so sánh
  GM Trái Đất với GM hệ Trái Đất–Mặt Trăng chính là hệ số 5,5 km / 4,665e6 m
  mà Phase 3 đã định lượng.
- `Mars..Pluto → 4..9` (barycentre của hệ): kernel **không có** segment
  499/599/699/799/899/999. Bẫy đã đo: `spkezr("Jupiter")` theo *tên* SPICE
  resolve về 599 → `SpiceSPKINSUFFDATA`. Mọi truy vấn dùng
  `str(naif_id(name))` — test `test_jupiter_uses_barycentre_id_not_absent_planetcentre`
  đo `|r|=741701935982.2852 m` (et=0) với ID 5.
- Mọi body trong `GM_BY_BODY` đều mappable (import-time contract + test).
- Golden canary (đo et=0): |Earth–SSB| ∈ [1.46e11, 1.52e11] m
  (đo 1.4688894e11), |v_Earth| ∈ [29000, 31000] m/s (đo 30285.26),
  |Moon–Earth| ∈ [3.56e8, 4.07e8] m (đo 4.02449e8). Đảo ID sai là golden
  fail ngay.

## 6. Khung toạ độ (frame)

- **Tham chiếu**: `spkezr(..., "J2000", "NONE", "SOLAR SYSTEM BARYCENTER")`
  → trục J2000, tâm SSB, hiệu chuẩn **geometric** (không light-time/aberration
  — R7; `"NONE"` hard-code trong `spice_backend.py` duy nhất).
- **Model**: `ACTIVE_BODIES_BARYCENTRIC` — trục „ICRS/J2000", xuất phát điểm
  = barycentre của **đúng** `config.bodies` (GM của dự án).
- Sai lệch hệ thống **R8: J2000 vs ICRF ~0.02″ ≈ 1.45e4 m tại 1 AU — hằng
  số, KHÔNG hiệu chỉnh**. Ghi trong `ReferenceMetadata.reference_frame`
  (`"J2000"`); coi là sàn dưới độ chính xác có thể đạt. Nếu hiệu chỉnh về
  sau, chỗ duy nhất là `frames/transforms.py` kèm test riêng.
- `axis_note = "ICRF-aligned (derived from DE440 reference states)"` trong
  `State` do `ic.py` sinh ra — **claim về hướng** chỉ đúng khi IC đến từ
  `ic.py`. IC tổng hợp (convention „thần 1 trục +x") **không hợp lệ để so
  hướng** với tham chiếu; vì thế `ic_source` là tham số bắt buộc của
  `compare_trajectory` và được assert là reference-derived, không suy luận.

## 7. Tâm & xuất phát điểm (center / origin)

- Tham chiếu: tâm gốc `ssb(0)` — tâm mặc định của kernel.
- Model: `origin = "barycenter(Sun, Earth[, Moon])"`, COM = 0 và **giữ = 0**
  (động lượng đầu bằng 0, bảo toàn — đo: COM model ≤ 5.63e-8 m (Sun–Earth)
  và ≤ 2.81e-8 m (Sun–Earth–Moon) trong 7 ngày).
- **Độ lệch hai tâm, đã đo** (R1): tại et=0, `|SunEarthBary − SSB|` =
  1147044492.23 m (et=1 d: 1146706427.99 m) — cửa sổ [5e8, 2e9] m; delta
  xuất phát điểm Sun–Earth vs Sun–Earth–Moon = 5426.387689 m (cửa sổ
  [4000, 7000]). Gọi chung là O(10⁸–10⁹ m), **thời biến** (nhấp nhô do
  Sao Mộc + Thổ ≈ 7.4e8 + 4.1e8 m).
- Trước bất kỳ phép trừ nào, `assert_compatible` chặn 7 lớp sai lệch
  (body → frame hai chiều → center/cần `transform` → `epoch_jd` so `==` →
  time_scale → length_unit → velocity_unit), mỗi lớp một exception
  `MetadataMismatchError(field, model_value, reference_value)`.

## 8. Thang thời gian (time scale)

- **TDB duy nhất.** `et = (epoch_jd − 2451545.0) × 86400.0` — đổi *đại
  diện* hai đầu đều TDB, không có quy đổi IT/leap-second/TT.
- J2000 = 2451545.0 = 2000-01-01 **12:00** TDB; `et(2451545.0) == 0.0` exact.
- ULP float64 tại 2451545.0 ≈ 4.03e-5 s — áp **một lần** ở epoch, cả hai
  phía dùng cùng `config.epoch_jd` → common-mode, không lọt vào E_pos/E_vel.
- **Không bao giờ** round-trip JD theo mẫu (R9): mẫu là `et0 + t_s`
  (`test_sample_epochs_uses_one_conversion_not_per_sample_jd`).
- **LSK-free**: không nạp leapseconds kernel, không `str2et`, không lịch;
  epoch truyền cho SPICE là số `float`. Kiểm chứng: `sp.ktotal("leapseconds") == 0`
  trước **và sau** khi truy vấn (`test_lsk_free_time_operation`).
  `UTC/TT/SI` → `TimeScaleMismatchError` (từ chối, không lặng đổi).
- Ghi `time_standard = "TDB — SPICE ephemeris time, s past J2000 TDB"`.

## 9. Đơn vị (units)

- SPICE SPK xuất **km, km/s** (chuẩn NAIF, ghi trong metadata — không đoán).
  Dự án làm việc bằng **m, m/s**. Quy đổi qua
  `units.from_native(..., native_unit=...)`, hằng `KM_TO_M = 1000.0` exact;
  phép nhân hiện diện trong **một file**: `ephemeris/spice_backend.py`.
- Goldens **tách riêng** vị trí và vận tốc (R2 — golden vị trí không bắt
  bug vận tốc): `test_position_golden_earth_ssb_j2000` (1.496e11 m) +
  `test_velocity_golden_earth_ssb_j2000` (29 780 m/s).
- Live: `test_stage5_units_live` so **exact** output provider với
  `spkezr` × 1000 (vị trí và vận tốc hai assertion riêng).
- **Spot-verify checklist F (đã làm 2026-10-03):** xóa ×1000 ở vận tốc →
  AssertionError tại dòng 168 test stage5; xóa ở vị trí → AssertionError
  dòng 167; khôi phục → pass. `git diff` sạch sau khôi phục.

## 10. Biến đổi (transformations)

- Một hàm duy nhất: `frames/transforms.py::recenter_ssb_to_model` —
  **dịch thuần** theo barycentre GM-weighted (GM dự án, cùng trọng số model),
  **không xoay, không tham số xoay** (`test_api_exposes_no_rotation`,
  `test_relative_vectors_preserved_no_rotation`).
- Trong `compare_trajectory`, tham chiếu được recenter **theo từng mẫu**:
  `ref'(t) = ref(t) − r_B(t)` với `r_B(t)` là barycentre tập con **tại chính
  thời điểm t` — đúng định nghĩa „relatif to barycentre của `config.bodies`"
  mà frame model dùng (COM model = 0 mọi t). Nếu recenter **một lần** ở
  t0, độ lệch quỹ đạo barycentre tham chiếu sẽ lọt vào E_pos như lỗi giả:
  **đo được 9477584.13 m (Sun–Earth) và 9551718.12 m (Sun–Earth–Moon) sau
  7 ngày** — bằng ~630× sai số SEM thật (15033.85 m). Chính R1
  („partially-corrected residuals mistaken for model error").
- Số đo backing: sau recenter, COM model-vs-tham chiếu ≈ 0; hồi quy
  quét: `test_com_zero_invariant_after_recenter`,
  `test_sun_earth_model_origin_offset_from_ssb`,
  `test_se_vs_sem_origin_delta_quantified`.
- Chuỗi transform in `ComparisonResult.transform` (chứa „no rotation" +
  offset tại et0) — có trong record.

## 11. Nội suy (interpolation)

- **Đường so sánh chính: KHÔNG nội suy phía dự án.** SPK là Type-2
  Chebyshev; `spkezr` đánh giá **đúng epoch yêu cầu** (vị trí đa thức +
  đạo hàm vận tốc). Cùng `et` → cùng bit (không RNG, không tích lũy).
- `interpolation.py` (cubic Hermite, C¹, dùng cả vị trí lẫn vận tốc,
  O(h⁴)) chỉ dùng cho **dữ liệu mẫu** (fixture, batch): domain đóng
  `[-86400, 864000]`, đúng mẫu trả về **bit-exact**, ngoài domain →
  `InterpolationError` (zero extrapolation), lưới không đơn điệu/trùng →
  reject, gọi lặp lại bit-identical (toàn bộ ma trận test trong
  `test_interpolation.py`, 11 test).
- **Sai số nội suy đã đo** (fixture hàng ngày vs `spkezr` native, quanh
  J2000, Trái Đất): 26 probe nội bộ → max **62.578 m** (vị trí),
  **0.002216 m/s** (vận tốc); 3 probe stage-8 → 62.5777 m / 0.0022923 m/s.
  Ngưỡng stage-8 = 100× các số đo này (6258 m / 0.23 m/s) với lý do ghi
  trong docstring. Điểm mẫu: nội suy == native **bit-equal** (đo True).

## 12. Số đo & ComparisonResult (metrics)

- Thứ tự tính (plan §9): map body → `et0 + t` (R9) → truy vấn tham chiếu
  (mỗi mẫu, coverage kiểm mỗi mẫu) → recenter (lớp transform) →
  `assert_compatible` (**trước** mọi trừ) → E_pos/E_vel/E_rel → thống kê.
- `E_pos(t) = ‖r_model − r_ref'‖`, `E_vel(t) = ‖v_model − v_ref'‖` (m, m/s);
  `E_rel = E_pos / ‖r_ref'‖` với guard mẫu số 0 (raise, không chia lặng).
- Thống kê: mean / median / max + percentiles cấu hình (mặc định p95,
  `np.percentile(method="linear")`), tính trên **cả hai** mảng.
- **Không** fitting, không làm mượt, không „alignment search" — số liệu là
  đúng những gì mẫu nói (kỷ luật Phase 3 kế thừa).
- Test tổng hợp (chạy trước, kernel-free): model==tham chiếu → sai số 0
  bit-exact; +Δr 5000 m → tái lập chính xác; +Δv 5 m/s → tái lập; p95 tay =
  3.85; 7 lớp mismatch; guard mẫu số 0; `to_dict()` round-trip;
  `write_comparison_record` với `allow_nan=False`.
- `ic_source` **bắt buộc** (R4): không có nó thì không có kết quả so sánh.

## 13. Kết quả đo có kiểm soát (staged results — số đo 2026-10-03)

Thứ tự giai đoạn bắt buộc (brief §14), mỗi bước một test
(`tests/real_kernel/test_staged_validation.py::stage1..stage10`):
load → metadata → 1 body/1 epoch → nhiều epoch → units → frame/center →
body IDs → nội suy-vs-native → **Sun–Earth** → **Sun–Earth–Moon**.

| Cấu hình | dt (s) | mẫu | E_pos max (m) | E_vel max (m/s) | E_rel max | Ngưỡng (floor–ceiling) |
|---|---|---|---|---|---|---|
| Sun–Earth, RK4, ≤ 7 d, IC `ic.py` | 31558.1498 (= P_SE/1000) | 20 | **5073209.53** | **16.4805** | 3.4486e-5 | pos 5.0e4–5.1e8; vel 0.16–1650; rel ≤ 3.45e-3 |
| Sun–Earth–Moon, RK4, ≤ 7 d, IC `ic.py` | 2360.5915 (= P_EM/1000) | 65 | **15033.85** | **0.0487388** | — | pos 150.0–1.51e6; vel 4.8e-4–4.88 |
| Khoảng cách Đất–Mặt Trăng (metric riêng) | — | 65 | **121.80** (max sai số khoảng cách) | — | — | 1.2–1.22e4 m |

- `E_pos[0] == 0` **exact** ở cả hai cấu hình (IC nạp từ chính tham chiếu).
- Khoảng cách Đất–Mặt Trắng t=0: `d_model[0] == d_ref[0] == 402448639.8873211`
  (bit-equal); `d_ref` luôn trong cửa sổ vật lý [3.56e8, 4.07e8] m.
- Ceiling = 100× số đo (bắt hồi quy đơn vị/khung/body sai → vệt O(1e9));
  floor = số đo/100 (bắt so sánh „hỏng im lặng", ví dụ body tự so với
  mình). Lý do đầy đủ trong docstring từng test (checklist G).
- Ghi nhận kiểm soát trong record: epoch, bodies, `ic_source`, tích phân,
  dt, duration, kernel (sha256), frame, center, time scale, đơn vị,
  `config_hash` — assert tại `test_stage9_sun_earth_controlled` /
  `test_stage10_sun_earth_moon_controlled`.

## 14. Nguồn không chắc chắn (uncertainty sources)

Danh sách thành phần sai số **đã cách ly được** (không khẳng định nhân quả
vượt quá phần đo được):

1. **Thiếu thân trong cấu hình** (so sánh với DE440 đầy đủ): cấu hình
   Sun–Earth thiếu Mặt Trăng (thuật số thủy triều ngoài ~… — chênh lệch
   5.07e6 m sau 7 d so với 1.50e4 khi thêm Mặt Trăng vào — số đo ở §13);
   cấu hình ≤3 thân thiếu hành tinh (thuật số thủy triềm còn lại).
2. **Lỗi tích phân RK4** (O(dt⁵)/mẫu): dt lớn (P/1000) ở Sun–Earth.
3. **Hệ số IC/định nghĩa** (kế thừa Phase 3, `phase3-earth-moon.md`):
   5,5 km mass-definition, 4.665e6 m Earth-vs-EMB — IC reference-ingested
   (`ic.py`) đã giảm phần này xuống mức dùng chung định nghĩa GM.
4. **Bias trục J2000 vs ICRF** (R8): ~0.02″ ≈ 1.45e4 m tại 1 AU, hằng
   số — không hiệu chỉnh, ghi nhận là sàn.
5. **Đại diện SPK** (Type-2 Chebyshev): đặc trưng của tham chiếu, không
   định lượng lại được ở đây.
6. **Nội suy fixture** (khi dùng fixture thay kernel): ≤ 62.578 m đã đo
   (§11).
7. **Lỗi float64/ULP**: 4.03e-5 s epoch (common-mode), không phát hiện
   được trên E_pos hiện tại.

## 15. Hạn chế (limitations)

- Coverage **1849–2150** (de440s). Chuyển sang `de440.bsp` (1550–2650) là
  **thay manifest, không thay code** (R12). Mục mở (non-blocking, chưa làm):
  nếu có `de440.bsp` trong tay, spot-compare `spkezr` tại 3 epoch rồi ghi
  khác biệt vào tài liệu này — hiện **không có** file de440.bsp để so.
- Kernel không có segment tâm hành tinh (499/599/…) — ánh xạ dùng
  barycentre; truy vấn theo tên hành tinh sẽ fail (đúng ý muốn).
- So sánh với IC tổng hợp **vô hiệu về hướng** (§6) — bị cấm, không
  „sửa" bằng máy dò hướng.
- Model cách ly (≤3 thân) **không đại diện được** dịch chuyển COM do lực
  ngoài — đó là định nghĩa cấu hình, không phải bug; so sánh đo cấu trúc
  tương đối (§10).
- Không LSK → không nhận epoch chuỗi (chỉ số TDB float) — chủ đích.
- Ngưỡng ghi theo máy đo 2026-10-03; bit-đúng giữa các nền tảng không
  được đảm bảo (chỉ đảm bảo đơn đặt hàng).
- `spiceypy` khoá `>=8,<9` (extra `[spice]`); core không phụ thuộc SPICE
  (test import-boundary + `test_core_import_does_not_load_spiceypy`).

## 16. Quy trình tái lập (reproducibility procedure)

```powershell
# 1) cài đặt (một lần)
pip install -e ".[spice]"                       # spiceypy >=8,<9

# 2) nạp kernel (một lần) + đối chiếu checksum
Invoke-WebRequest -Uri "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp" -OutFile kernels\de440s.bsp
python -c "import hashlib,pathlib; p=pathlib.Path('kernels/de440s.bsp'); print(p.stat().st_size, hashlib.md5(p.read_bytes()).hexdigest(), hashlib.sha256(p.read_bytes()).hexdigest())"
# kỳ vọng: 32726016  3917ee56769db332790c751e2168843d  c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2

# 3) hai cổng (bắt buộc cả hai, 0 failed / 0 skipped)
python -m pytest                                  # Gate A
python -m pytest -m real_kernel                   # Gate B

# 4) ghi lại fixture tham chiếu (nếu muốn fixture mới)
python tools\record_reference_fixture.py

# 5) tái lập bản ghi so sánh nghiệm thu (Sun–Earth–Moon, §13)
python -c "import sys; sys.path.insert(0, 'src'); from pathlib import Path; from solar_ephemeris.ephemeris.spice_backend import SpiceReference; from solar_ephemeris.ephemeris.ic import reference_state_to_model_state; from solar_ephemeris.ephemeris.comparison import compare_trajectory, write_comparison_record; from solar_ephemeris.simulation.configuration import SimulationConfig; from solar_ephemeris.simulation.engine import SimulationEngine; from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale; cfg = SimulationConfig(bodies=('Sun','Earth','Moon'), integrator='rk4', dt=27.321661*86400/1000, duration=604800.0, epoch_jd=2451545.0, time_scale=TimeScale.TDB, frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC, reference_dataset='JPL DE440 (de440s.bsp live)'); sp = SpiceReference('kernels/de440s.bsp'); ic = reference_state_to_model_state(sp, bodies=('Sun','Earth','Moon'), epoch_jd=2451545.0); traj = SimulationEngine(cfg).run(ic, sample_every=4); res = compare_trajectory(traj, sp, body='Earth', ic_source='reference-ingested via ephemeris/ic.py (live de440s.bsp)'); write_comparison_record(res, Path('docs/methodology/phase4_comparison_record.json')); print(res.position_stats.max, res.velocity_stats.max)"
# kỳ vọng: 15033.85078170456 0.04873877478110312
```

Bản ghi cam kết là của **lần chạy nghiệm thu 2026-10-03**; chạy lại cùng
kernel + cùng phiên bản phải cho đúng các field tham chiếu (req 2) —
`test_phase4_doc_contract.py` đối chiếu record với manifest, không cần
kernel.

## 17. Bản đồ yêu cầu → test (requirement → test map)

| # | Yêu cầu | Test chính |
|---|---|---|
| 1 | DE440 canonical, không thay thế ngầm | `test_kernel_manifest.py` (hash/size/URL); `test_ephemeris_types.py::test_metadata_rejects_reference_substitution`; `test_spice_backend.py::test_wrong_solution_filename_refused_by_manifest` |
| 2 | Provenance 17 field + record | `test_ephemeris_types.py::test_metadata_round_trip_preserves_all_fields`; `test_comparison.py::test_comparison_result_carries_full_provenance`; `test_staged_validation.py::test_stage9_record_provenance_audit` |
| 3 | `ReferenceState` không „sáu số trần" | `test_reference_facade.py` (10); `test_ephemeris_types.py::test_state_carries_provenance` |
| 4 | Cách ly SPICE (chỉ `spice_backend.py`) | `test_import_boundaries.py` (5, gồm subprocess-import) |
| 5 | Ánh xạ body-ID tường minh | `test_ephemeris_mapping.py` (9, gồm wrong-ID canary) |
| 6 | Cổng tương thích 7 lớp trước khi trừ | `test_comparison.py::test_mismatch_*` (7) + `test_compatible_pair_passes` |
| 7 | Biến đổi dịch thuần, không xoay | `test_transforms.py` (10) |
| 8 | Hợp đồng thời gian TDB, LSK-free | `test_ephemeris_time.py` (7); `test_spice_backend.py::test_lsk_free_time_operation` |
| 9 | Đơn vị, ×1000 tách vị trí/vận tốc | `test_ephemeris_units.py` (7); `test_staged_validation.py::test_stage5_units_live`; spot-verify §9 |
| 10 | Coverage đo từ kernel, 5 biên | `test_ephemeris_types.py::test_coverage_*` (5+); `test_spice_backend.py::test_state_at_rejects_outside_coverage`; `test_staged_validation.py::test_stage1_load`/`stage2` |
| 11 | Nội suy: ma trận + sai số đo | `test_interpolation.py` (11); `test_spice_backend.py::test_interior_interpolation_vs_native_within_measured_bound`; `test_staged_validation.py::test_stage8_interpolation_vs_native` |
| 12 | Metrics + thống kê + guard | `test_comparison.py` (zero/offsets/stats/percentile/mẫu số 0) |
| 13 | `ComparisonResult` + record auditable | `test_comparison.py::test_result_to_dict_round_trip`/`test_write_comparison_record`; `test_synthetic_end_to_end.py::test_comparison_record_written_from_chain` |
| 14 | Thứ tự giai đoạn bắt buộc | `test_staged_validation.py::test_stage1..stage10` (12) |
| 15 | Synthetic trước, kernel-free | `test_synthetic_end_to_end.py` (4); toàn bộ Gate A xanh không cần kernel |
| 16 | Diễn giải lỗi, 11 kiểm soát | `test_ic.py::test_axis_note_is_the_icrf_claim`; `test_staged_validation.py::test_stage9_sun_earth_controlled` (`ic_source` ref-derived) + `_assert_controls` |
| 17 | Kỷ luật ngưỡng (measured-first) | Docstring `threshold/measured/reason` ở stage8/9/10 + interpolation; audit checklist G |
| 18 | 0 failed / 0 skipped, không làm suy yếu test cũ | Cổng A + B (§0); checklist J |
| 19 | Tài liệu + khớp doc↔manifest | Tài liệu này; `tests/unit/test_phase4_doc_contract.py` |
| 20 | Cổng nghiệm thu + STOP | Checklist A–J; không mở Phase 5 khi chưa được phép |

**Phạm vi file Phase 4 (checklist I):** `src/solar_ephemeris/ephemeris/*`
(13 file), `src/solar_ephemeris/frames/transforms.py`,
`tools/record_reference_fixture.py`, `tests/fixtures/reference/*`,
`tests/real_kernel/*` + test Phase-4 trong `tests/unit/`, `pyproject.toml`
(extra + marker + addopts — đã được phê duyệt), tài liệu này + record JSON
+ sửa điểm chỉ `units-and-frames.md` §2. Không sweep, không vẽ đồ thị,
không ML, không tối ưu hóa.
