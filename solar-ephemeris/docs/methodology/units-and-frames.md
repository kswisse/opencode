# Đơn vị & Khung toạ độ (Units & Frames)

Tài liệu này là **hợp đồng** của Phase 1–2. Code và test đều bám vào đây; sửa tài
liệu này nghĩa là sửa hợp đồng, phải kèm sửa test.

## 1. Quy ước đơn vị

| Đại lượng | Đơn vị nội bộ | Ghi chú |
|---|---|---|
| Độ dài | metre (m) | `AU` **chỉ** xuất hiện ở ranh giới I/O |
| Thời gian | giây (SI s) | thời gian nội bộ là số giây kể từ `epoch_jd` |
| Khối lượng | kg | chỉ cần để biết — động lực học dùng GM, không dùng m |
| Vận tốc | m/s | |
| GM | m³/s² | hằng số hấp dẫn năng động duy nhất |

**Bắt buộc:**

- Động lực học chỉ dùng **GM** (`GM_BY_BODY`), không bao giờ dùng `G × m`.
  Lý do: hằng số G của CODATA và GM của DE440 không tự nhất quán với nhau
  (sai số tương đối ~1e-10 trở lên); trộn hai nguồn tạo ra sai số không kiểm
  soát được. `G` chỉ được xuất hiện trong test (đổi đơn vị / so sánh), không
  nằm trong đường tính chính.
- `AU` quy đổi **một lần duy nhất** ở biên nhập/xuất (I/O boundary). Toàn bộ
  tính toán bên trong làm việc với số mét.
- Nguồn GM: DE440 (Park et al. 2021, Table 2), đơn vị gốc km³/s² ×1e9 → m³/s².
  Bảng ánh xạ đầy đủ nằm trong `physics/constants.py::GM_SOURCES`.
- **Cạm bẫy đã ghi nhận:** `GM_EMB = 4.03503235502e14` là GM của hệ
  Trái Tim–Trăng, **không** phải GM của Trái Đất. GM Trái Đất đúng là
  `3.98600435507e14`. Test `test_constants.py` khoá cả hai giá trị.

## 2. Khung toạ độ

### `ACTIVE_BODIES_BARYCENTRIC` (đang hoạt động)

- Gốc: tâm quán tính (barycentre) của **chính xác tập thân đang xét**
  (`config.bodies`).
- Trục: ICRS/J2000 quay quán tính — trục X về J2000 equinox, Z về cực J2000.
- Ghi chú trục (`axis_note`) lưu trong `StateMeta`, ép bởi constructor.
- Bắt buộc nội tại: động lượng tuyến tính của hệ = 0 trong khung này
  (test N4 kiểm tra đến 1e-12).

### `SSB_ICRS` (kích hoạt từ Phase 4)

- **Cập nhật Phase 4 (2026-10-03):** `frames/transforms.py` giờ tồn tại;
  `ephemeris/spice_backend.py` kết xuất `ReferenceState` ở gốc
  `ssb(0)` (SPICE `J2000`, geometric, không aberration). Phép biến đổi duy
  nhất giữa hai khung là dịch thuần theo barycentre của `config.bodies`
  (`recenter_ssb_to_model` — không xoay), luôn đi qua
  `assert_compatible` trước khi trừ. Hợp đồng đầy đủ: xem
  [`phase4-jpl-validation.md`](phase4-jpl-validation.md) §6–§10
  (kể cả bias J2000/ICRF ~0.02″ không hiệu chỉnh).
- Thời kỳ Phase 1–2 (bản ghi lịch sử): sổ đăng ký đã có giá trị này nhưng
  chưa phép biến đổi nào, `transforms.py` chưa tồn tại — cố ý theo phạm
  vi pass.

### Trộn khung bị cấm

`SimulationEngine._align` từ chối thẳng (raise) khi gặp mismatch:

- tập thân khác (`body_set`)
- khung khác (`frame`)
- thang thời gian khác (`time_scale`)
- epoch khác (`epoch_jd`)

Không có "silently reproject". Sai thì hỏng có kiểm soát, không sai im lặng.

## 3. Thang thời gian

- `TimeScale`: `TDB | TT | UTC | SI` (StrEnum).
- Nội bộ Phase 1–2: **TDB** — mọi tích phân trên trục TDB.
- Chuyển đổi TDB↔TT↔UTC **không** được implement — Phase 4 đã quyết định
  LSK-free, chỉ nhận epoch số trên TDB; `TT/UTC/SI` bị từ chối
  (`TimeScaleMismatchError`) thay vì lặng đổi. Test và config chỉ khai báo
  TDB (chi tiết: `phase4-jpl-validation.md` §8).
- `epoch_jd` là số JD trên thang khai báo; thời gian nội bộ
  `t = (jd − epoch_jd) × 86400` giây.

## 4. Trạng thái & năng lượng

- `State` luôn **định danh thân theo tên** (`body_names`), không theo chỉ số —
  thứ tự mảng và thứ tự tên phải khớp mọi lúc (constructor validate).
- `Trajectory.velocities` **luôn cùng thời điểm** với
  `Trajectory.positions/ times`. Không lưu `v_half` (velocity Verlet rơi vào
  nửa bước) trong kết quả tích phân — trung gian nội bộ được căn lại trước khi
  ghi.
- Năng lượng kiểm chứng (test N1–N6):
  `E = Σᵢ ½ mᵢ‖vᵢ‖² − Σ_{i<j} G mᵢ mⱼ / r_{ij}` với
  `mᵢ = GMᵢ / G` (G chỉ để đổi đơn vị cho mục tiêu kiểm thử).

## 5. Tính tất định (determinism)

- Stepper **stateless**: không cache gia tốc giữa các bước —
  cùng state + cùng config ⇒ cùng bit kết quả.
- `config_hash` = SHA-256 của **chỉ** các trường vật lý/số học
  (bodies, integrator, dt, duration, epoch, frame, time_scale).
  Thời điểm chạy (`run_timestamp_utc`) **không** nằm trong hash.
- `run_to_file` ghi `trajectory.npz` + `run_record.json`; tái lập được bằng
  `load_run`. Lưu ý: bytes của npz **không** được dùng để so sánh (zip nhúng
  timestamp) — so sánh phải trên mảng sau khi load (`np.array_equal`).
