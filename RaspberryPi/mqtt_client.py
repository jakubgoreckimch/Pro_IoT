import paho.mqtt.client as mqtt  # type: ignore
from PyQt5.QtCore import QThread, pyqtSignal  # type: ignore
import time 

class MQTTClient(QThread):
    temp_received = pyqtSignal(str)
    hum_received = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, broker_ip):
        super().__init__()
        self.broker_ip = broker_ip
        self.client = mqtt.Client()
        self.last_received_time = None
        self.timeout_limit = 10


    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:  # Połączono pomyślnie
            print("Połączenie pomyślne, subskrypcja na tematy.")
            client.subscribe("sensor/temp")
            client.subscribe("sensor/humidity")
        else:
            print(f"Problem z połączeniem, kod rozłączenia: {rc}")
            self.error_signal.emit("Problem z połączeniem do brokera.")


    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()

        if msg.topic == "sensor/temp":
            print(f"Otrzymano temperaturę: {payload} °C")
            self.temp_received.emit(payload)
        elif msg.topic == "sensor/humidity":
            print(f"Otrzymano wilgotność: {payload} %")
            self.hum_received.emit(payload)

        # Aktualizujemy czas, gdy otrzymaliśmy dane
        self.last_received_time = time.time()


    def on_disconnect(self, client, userdata, rc):
        """Obsługuje rozłączenie z brokerem"""
        print(f"Rozłączono z brokerem. Kod rozłączenia: {rc}")
        if rc != 0:  # Jeśli kod rozłączenia nie jest 0, oznacza to błąd
            self.error_signal.emit("Brak połączenia z brokerem!")


    def check_connection(self):
        """Sprawdzamy, czy połączenie jest aktywne (czy są nowe dane)"""
        if self.last_received_time is None:
            return False
        current_time = time.time()
        if current_time - self.last_received_time > self.timeout_limit:
            return False
        return True

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.connect(self.broker_ip, 1883, 10)  # Oczekuj 10 sekund na połączenie
        self.client.loop_start()  # Używamy loop_start(), aby działało równolegle

        while True:
            if not self.check_connection():
                print("Brak danych z ESP32, próba ponownego połączenia...")
                self.error_signal.emit("Brak danych z ESP32.")
                self.client.reconnect()  # Próba ponownego połączenia z brokerem
            time.sleep(5)  # Czekaj 5 sekund przed kolejną próbą