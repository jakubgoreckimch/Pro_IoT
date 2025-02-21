import sys
import random
import mysql.connector # type: ignore
import pyqtgraph as pg # type: ignore
import paho.mqtt.client as mqtt # type: ignore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton # type: ignore
from PyQt5.QtCore import QTimer, QThread, pyqtSignal # type: ignore

class DatabaseHandler(QThread):
    def __init__(self):
        super().__init__()

    def connect_to_database(self):
        try:
            conn = mysql.connector.connect(
                host='s108.cyber-folks.pl',
                user='iothost_jakub',
                password='Paluch10/29',  
                database='iothost_raspberry_db'
            )
            return conn
        
        except mysql.connector.Error as err:
            print(f"Błąd połączenia: {err}")
            return None

    def insert_data(self, temperature, humidity):
        conn = self.connect_to_database()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO SensorDateTable (Temperature, Humidity, Time) VALUES (%s, %s, NOW())"
            cursor.execute(query, (temperature, humidity))
            conn.commit()
            cursor.close()
            conn.close()
            print("Dane zapisane do bazy!")
        else:
            print("Brak połączenia z baza danych.")

    def clean_data_base(self):
        conn = self.connect_to_database()
        if conn:
            cursor = conn.cursor()
            query = "DELETE FROM SensorDateTable"
            cursor.execute(query)
            conn.commit()
            cursor.close()
            conn.close()
            print("Dane zostały usunięte.")
        else:
            print("Błąd połączenia z bazą danych. Dane nie zostały usunięte.")


class MQTTClient(QThread):
    temp_received = pyqtSignal(str)
    hum_received = pyqtSignal(str)

    def __init__(self, broker_ip):
        super().__init__()
        self.broker_ip = broker_ip
        self.client = mqtt.Client()

    def on_connect(self, client, userdata, flags, rc):
        print("Połączono z brokerem MQTT!")
        client.subscribe("sensor/temp")
        client.subscribe("sensor/humidity")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()

        if msg.topic == "sensor/temp":
            print(f"Otrzymano temperaturę: {payload} °C")
            self.temp_received.emit(payload)
        elif msg.topic == "sensor/humidity":
            print(f"Otrzymano wilgotność: {payload} %")
            self.hum_received.emit(payload)

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_ip, 1883, 60)
        self.client.loop_forever()  # Pętla nasłuchująca


class TempHumidityApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Monitoring Temperatury i Wilgotności")
        self.setGeometry(100, 100, 800, 400)

        self.layout = QVBoxLayout()

        self.temp_label = QLabel("Temperatura: -- °C")
        self.humidity_label = QLabel("Wilgotność: -- %")
        
        self.layout.addWidget(self.temp_label)
        self.layout.addWidget(self.humidity_label)

        # Tworzenie wykresu
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.plot_widget.setLabel("left", "Wartość", units="°C / %")
        self.plot_widget.setLabel("bottom", "Czas", units="s")
        self.temp_curve = self.plot_widget.plot(pen="r", name="Temperatura")  # Czerwona linia
        self.humidity_curve = self.plot_widget.plot(pen="b", name="Wilgotność")  # Niebieska linia

        # Dane początkowe
        self.x_data = list(range(100))  
        self.temp_data = [0 for _ in range(100)]
        self.humidity_data = [0 for _ in range(100)]

        # Timer do aktualizacji wykresu
        self.timer = QTimer()
        self.timer.setInterval(1000)  # Odświeżanie co 1s
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


        self.quit_button = QPushButton("Wyczyść dane z bazy")
        self.quit_button.clicked.connect(self.clean_data_base_db)
        self.layout.addWidget(self.quit_button)

        # Przycisk do zakończenia aplikacji
        self.quit_button = QPushButton("Zakończ")
        self.quit_button.clicked.connect(self.close)
        self.layout.addWidget(self.quit_button)

        # Ustawienie layoutu
        self.setLayout(self.layout)

        # Timer do aktualizacji danych
        self.mqtt_client = MQTTClient("192.168.0.40")
        self.mqtt_client.temp_received.connect(self.update_temp)
        self.mqtt_client.hum_received.connect(self.update_humidity)
        self.mqtt_client.start()  # Start wątku MQTT

        self.db_handler = DatabaseHandler()

        self.latest_temp = None
        self.latest_humidity = None


    def update_temp(self, temperature):
        self.latest_temp = float(temperature)
        self.temp_label.setText(f"Temperatura: {temperature} °C")
        self.save_to_db()

    def update_humidity(self, humidity):
        self.latest_humidity = float(humidity)
        self.humidity_label.setText(f"Wilgotność: {humidity} %")
        self.save_to_db()

    def save_to_db(self):
        if self.latest_temp is not None and self.latest_humidity is not None:
            self.db_handler.insert_data(self.latest_temp, self.latest_humidity)

    def clean_data_base_db(self):
        self.db_handler.clean_data_base()

    def update_plot(self):
        """ Aktualizacja danych na wykresie """
        self.temp_data.append(float(self.latest_temp))
        self.humidity_data.append(float(self.latest_humidity))

        self.temp_data.pop(0)  # Usunięcie starego punktu
        self.humidity_data.pop(0)

        self.temp_curve.setData(self.x_data, self.temp_data)
        self.humidity_curve.setData(self.x_data, self.humidity_data)

        

if __name__ == "__main__":
    print("Aplikacja uruchomiona!")  # Dodaj ten print dla debugowania
    app = QApplication(sys.argv)
    window = TempHumidityApp()
    window.show()
    sys.exit(app.exec_())