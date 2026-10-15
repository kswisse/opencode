// dht22_logger.ino — ESP32 sensor node for School Heat Intelligence.
// Logs DHT22 readings as CSV to Serial every 10 minutes.
// Wiring: DHT22 VCC->3V3, GND->GND, DATA->GPIO15 (+4.7k pull-up to 3V3).
// Needs Arduino library: "DHTesp" (install via Library Manager).
// Flash with Arduino IDE / PlatformIO, then capture Serial output to a file.
#include <DHTesp.h>

#define DHT_PIN 15
#define INTERVAL_MS 600000UL  // 10 minutes

DHTesp dht;
char nodeId[24];

void setup() {
  Serial.begin(115200);
  dht.setup(DHT_PIN, DHTesp::DHT22);
  // ponytail: chip MAC as node id, set NODE_ID below for fixed names (e.g. "san_truong")
  snprintf(nodeId, sizeof(nodeId), "esp32_%06X", (unsigned)(ESP.getEfuseMac() & 0xFFFFFF));
  Serial.println("timestamp,node_id,temp_c,humidity");
}

void loop() {
  static unsigned long last = 0;
  unsigned long now = millis();
  if (now - last < INTERVAL_MS && last != 0) { delay(1000); return; }
  last = now;
  TempAndHumidity th = dht.getTempAndHumidity();
  if (dht.getStatus() != 0) return;  // skip failed reads, try next cycle
  // ISO-8601 needs real time: replace millis() with NTP once WiFi is configured.
  Serial.print(now / 1000); Serial.print(",");
  Serial.print(nodeId); Serial.print(",");
  Serial.print(th.temperature, 1); Serial.print(",");
  Serial.println(th.humidity, 1);
}
