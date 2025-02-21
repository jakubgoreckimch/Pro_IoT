import sys
import pyqtgraph as pg  # type: ignore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton  # type: ignore
from PyQt5.QtCore import QTimer  # type: ignore
from db_handler import DatabaseHandler 
from mqtt_client import MQTTClient

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
        self.x_data = list(range(500))  
        self.temp_data = [0 for _ in range(500)]
        self.humidity_data = [0 for _ in range(500)]

        # Timer do aktualizacji wykresu
        self.timer = QTimer()
        self.timer.setInterval(200)  # Odświeżanie co 0.2s
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


        self.clean_button = QPushButton("Wyczyść dane z bazy")
        self.clean_button.clicked.connect(self.clean_database)
        self.layout.addWidget(self.clean_button)

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

    def clean_database(self):
        self.db_handler.clean_database()

    def update_plot(self):
        """ Aktualizacja danych na wykresie """
        self.temp_data.append(float(self.latest_temp) if self.latest_temp else 0)
        self.humidity_data.append(float(self.latest_humidity) if self.latest_temp else 0)

        self.temp_data.pop(0)  # Usunięcie starego punktu
        self.humidity_data.pop(0)

        self.temp_curve.setData(self.x_data, self.temp_data)
        self.humidity_curve.setData(self.x_data, self.humidity_data)
