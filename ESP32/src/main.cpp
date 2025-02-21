#include <WiFi.h>
#include <PubSubClient.h>

#define WIFI_SSID "goscinne"
#define WIFI_PASSWORD "k5eddxhfjeVr"
#define BROKER_IP "192.168.0.40"  
#define MQTT_PORT 1883
#define MQTT_TOPIC_TEMP "sensor/temp"
#define MQTT_TOPIC_HUM "sensor/humidity"

WiFiClient espClient;
PubSubClient client(espClient);

void connectToWiFi() {
    Serial.print("Łączenie z WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" Połączono!");
}

void connectToMQTT() {
    while (!client.connected()) {
        Serial.print("Łączenie z MQTT...");
        if (client.connect("ESP32_Client")) {  // Nazwa klienta
            Serial.println(" Połączono!");
        } else {
            Serial.print(" Błąd: ");
            Serial.print(client.state());
            delay(2000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    connectToWiFi();
    client.setServer(BROKER_IP, MQTT_PORT);
    connectToMQTT();
}

void loop() {
    if (!client.connected()) {
        connectToMQTT();
    }
    client.loop();

    float temperature = 20.0 + (rand() % 100) / 10.0;  // Zakres 20.0 - 30.0°C
    float humidity = 40.0 + (rand() % 600) / 10.0;     // Zakres 40.0 - 100.0%

    String tempStr = String(temperature, 1);
    String humStr = String(humidity, 1);

    client.publish(MQTT_TOPIC_TEMP, tempStr.c_str());
    client.publish(MQTT_TOPIC_HUM, humStr.c_str());

    Serial.print("Wysłano temperaturę: ");
    Serial.println(tempStr);
    
    Serial.print("Wysłano wilgotność: ");
    Serial.println(humStr);

    delay(2000);
}
