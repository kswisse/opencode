# Sensor Guide — từ demo synthetic sang data đo thật

Phần duy nhất cần bạn làm bằng tay: mua LK, đấu dây, đặt máy ở trường,
copy serial log về. Còn lại code đã viết sẵn.

## Mua gì (mỗi node ~250k)
- 1× ESP32 DevKit, 1× DHT22 (AM2302), dây Dupont, sạc dự phòng
- 3 node: `san_truong`, `lop_12a1`, `phong_may`

## Đấu dây
DHT22 VCC→3V3, GND→GND, DATA→GPIO15 (+điện trở 4.7k nối DATA lên 3V3).

## Nạp + log
1. Arduino IDE → Library Manager → cài `DHTesp` → mở `firmware/dht22_logger.ino` → Upload
2. Mở Serial Monitor 115200, copy output vào `data/sensor_log.csv`
   (giữ đúng header `timestamp,node_id,temp_c,humidity`)
3. Đặt node ở 3 điểm, chạy 2 tuần. Chụp ảnh lắp đặt (dùng cho đơn EV).

## Đổ vào dashboard
```bash
python scripts/sensor_to_campus.py data/sensor_log.csv data/campus_measured.csv
```
Mở `src/heat_intelligence/dashboard/app.py`, đổi `demo_campus.csv`
thành `campus_measured.csv`. Badge dashboard sẽ chuyển 🟢 measured.

Lưu ý trung thực: cột wind/canopy/shade/surface là hằng số theo điểm đặt
(xem `ZONES` trong script), chỉ nhiệt + ẩm là đo thật — ghi đúng vậy trong đơn.
