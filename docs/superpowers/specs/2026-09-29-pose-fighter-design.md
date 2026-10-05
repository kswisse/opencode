# Pose Fighter — Game nhận diện tư thế (Goku vs Boss)

**Ngày:** 2026-09-29
**Trạng thái:** Approved
**Vị trí project:** `C:\Opencode\teachable machine\`

## Mục tiêu

Một game fighting 2D chạy trong trình duyệt, điều khiển bằng **pose detection** (Google Teachable Machine, Pose Project) kết hợp **phím mũi tên**. Người chơi thắng khi boss hết máu.

Deliverable đúng 3 file code + 2 ảnh đã có sẵn:

```
C:\Opencode\teachable machine\
├── index.html      — layout: canvas game, HUD, camera góc trái dưới, overlay kết quả
├── style.css       — styling toàn bộ trang, chữ CHIẾN THẮNG hoành tráng
├── stretch.js      — game loop, combat, AI, pose detection, input
├── player.png      — ảnh người chơi (đã có, 350x360)
└── boss.png        — ảnh boss (đã có, 364x364)
```

Không build step, không framework. Mở `index.html` bằng trình duyệt là chạy.

## Kỹ thuật

- **Rendering:** `<canvas>` 2D + `requestAnimationFrame`. Game world vẽ trên canvas chính (khoảng 960x540, responsive theo container).
- **Pose detection:** CDN scripts `@tensorflow/tfjs` và `@teachablemachine/pose`. Model được load từ một hằng số `MODEL_URL` trong `stretch.js` — người dùng paste URL sau khi Export (Upload → Export → Tensorflow.js) từ Teachable Machine.
- **Camera:** `<video>` 240px rộng, fixed góc trái dưới, `z-index` trên canvas. Mỗi frame chạy `posenet.detect(video)` → map class → hành động.
- **Ảnh:** `player.png` / `boss.png` load vào `Image` objects; nếu file thiếu/tải lỗi thì fallback sang hình vẽ bằng Canvas (nhân vật bo tròn đơn giản) để trang không vỡ.

## Điều khiển

### Pose → hành động của player

| Pose class | Hành động |
|---|---|
| Giơ tay trái | Skill 1 — đạn bắn thẳng |
| Giơ tay phải | Skill 2 — cầu nổ (vòng hồng tâm) |
| Dấu X (tay bắt chéo) | Def — dựng khiên |
| Đứng thẳng / idle | Idle — hồi máu |

Mapping linh hoạt: `stretch.js` chứa object `POSE_MAP` cho phép gán **tên class trong model** (hoặc index nếu tên không khớp) vào 4 hành động. Nếu model chưa load hoặc camera bị từ chối → toàn bộ pose tắt, hiện banner hướng dẫn, **game vẫn chơi được thuần phím** (phím 1/2/3 bắn skill thay pose, để test và không chết màn hình).

**Quy tắc:** phím mũi tên **chỉ có tác dụng khi pose hiện tại là idle**. Đang ở pose skill/khiên thì nhấn mũi tên không di chuyển.

### Phím mũi tên (chỉ khi idle)

| Phím | Hành động |
|---|---|
| Phải | Tiến (dịch phải trên trục ngang) |
| Trái | Lùi |
| Lên | Nhảy (parabola, có gravity) |
| Xuống | Ngồi (hitbox thấp lại, né đòn bay) |

### Phím bổ sung (không dùng pose)

- `1` / `2` / `3`: kích skill 1 / skill 2 / khiên (backup khi không có camera)
- `R`: chơi lại sau khi kết thúc

## Combat — người chơi

| Hành động | Hiệu ứng | Số liệu |
|---|---|---|
| Skill 1 | Đạn bay thẳng hàng ngang về phía boss, phát nổ khi trúng | **100 dmg**, hồi chiêu **3s** |
| Skill 2 | Vòng hồng tâm xuất hiện ngay người boss → **1s sau** nổ, áp dụng sát thương | **150 dmg**, hồi chiêu **5s** |
| Def / khiên | Khiên (PNG/CSS vẽ) dựng trước mặt player | Giảm sát thương nhận vào còn **1/4** (100 → 25). Không hồi chiêu. |
| Idle | Đứng yên, không ra chiêu | Hồi **5 máu/giây** (chỉ khi pose idle và đứng yên thực sự — không đang bấm di chuyển) |

- Máu player: **1200** (bằng boss), hiển thị thanh + số.
- Cooldown hiển thị dạng vòng quay nhỏ / thanh màu trên HUD.
- Khiên chỉ áp dụng **trong lúc đang giữ pose X** (buông pose = hết khiên).

## Combat — boss (AI tự điều khiển)

Boss đứng bên phải, đối diện player.

| Chiêu | Điều kiện | Hiệu ứng |
|---|---|---|
| Bắn | Mỗi **3s** | Đạn bay thẳng về phía player, **100 dmg** |
| Chém | Khi player ở **gần** (cách < 220px), tần suất mỗi **4s** | Vung chém, **150 dmg**, chỉ trúng khi thực sự gần |
| Khiên | Ngẫu nhiên mỗi **8–12s**, kéo dài **2s** | Giảm 1/4 sát thương nhận vào trong lúc giữ |

- Boss máu: **1200**, thanh + số phía trên boss.
- Boss phản ứng đơn giản, không phase.

## Trạng thái game

`home` → `loading` → `playing` → `won` / `lost`

- **Home (màn hình start):** hiện trước tiên khi mở trang — nền canvas (hoặc overlay phủ canvas), **tên game** lớn kiểu chữ hoành tráng (gradient vàng/cam, phát sáng), dòng phụ mô tả nhỏ, và **nút "BẮT ĐẦU"** bấm vào mới chuyển sang `loading` (load model + xin camera) rồi `playing`. Không load camera/model trước khi bấm nút (tránh trình duyệt xin quyền camera quá sớm).
- **Win:** boss ≤ 0 máu → overlay **"CHIẾN THẮNG"** hoành tráng (chữ lớn, gradient vàng, phát sáng/pulse, kim tuyến rớt), nút **Chơi lại**.
- **Lose:** player ≤ 0 máu → overlay đơn giản **"BẠN ĐÃ THUA"** + nút Chơi lại.
- Overlay chặn input trong lúc kết thúc.
- Nút Chơi lại quay về thẳng `playing` (giữ nguyên model + camera).

## Layout (index.html + style.css)

```
┌─────────────────────────────────────────────┐
│  HUD trên: [Thanh máu player ==== 1200]     │
│            [Thanh máu boss ==== 1200]       │
│ ┌─────────────────────────────────────────┐ │
│ │              GAME CANVAS                │ │
│ │   [player]  ◀── fight ──▶  [boss]       │ │
│ │                                         │ │
│ └─────────────────────────────────────────┘ │
│ ┌──────────┐  HUD dưới: cooldown skills,    │
│ │ WEBCAM   │  hướng dẫn phím, pose hiện tại│
│ └──────────┘                                │
└─────────────────────────────────────────────┘
```

- Webcam: `position: fixed`, góc trái dưới, viền bo tròn, độ mờ nhẹ, có nhãn "Camera".
- Trên webcam: dòng text nhỏ hiển thị **pose class hiện tại + confidence** (để người chơi biết model có nhận không).
- Background canvas: vẽ cảnh đơn giản (đồi cỏ / bầu trời gradient) — không phụ thuộc ảnh mạng.
- Responsive cơ bản: canvas co theo width, không bắt buộc mobile (game dùng phím).

## Xử lý lỗi

| Tình huống | Xử lý |
|---|---|
| `MODEL_URL` còn trống / load fail | Banner "Chưa có model — dán URL vào stretch.js" + game chơi được bằng phím |
| Camera bị từ chối / không có | Banner "Không có camera — chơi bằng phím 1/2/3" + pose tắt |
| `player.png` / `boss.png` load fail | Vẽ hình thay thế bằng Canvas, log console, không crash |
| Pose không nhận được class nào | Giữ nguyên hành động trước đó trong 500ms rồi về idle (tránh flicker) |

## Không làm (out of scope)

- Âm thanh / nhạc
- Mobile touch controls
- Nhiều level / phase boss
- Lưu điểm
- Tự训练 model trong trang (training làm trên web Teachable Machine)

## Testing

Chạy tay trong trình duyệt (Chrome, cần camera):

1. Mở `index.html` → thấy canvas + webcam + banner hướng dẫn (vì chưa có model URL).
2. Dán model URL → reload → webcam hiện pose class.
3. Kiểm tra từng pose: tay trái → đạn bay + cooldown 3s; tay phải → hồng tâm + nổ sau 1s; X → khiên; đứng thẳng → phím mũi tên ăn.
4. Kiểm tra phím mũi tên **không ăn** khi đang pose skill.
5. Kiểm tra khiên: boss bắn 100 → player chỉ mất 25.
6. Đánh boss hết 1200 máu → overlay CHIẾN THẮNG; để boss giết → overlay thua; `R` chơi lại.
7. Tắt camera / sai URL → banner hiện, game vẫn chơi bằng `1`/`2`/`3`.
