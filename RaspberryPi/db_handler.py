import configparser
import mysql.connector  # type: ignore
from PyQt5.QtCore import QThread  # type: ignore

class DatabaseHandler(QThread):
    def __init__(self):
        super().__init__()
        self.conn = None  # Dodajemy atrybut conn do klasy
        self.db_config = None
        self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        self.db_config = {
            'host': config['database']['host'],
            'user': config['database']['user'],
            'password': config['database']['password'],
            'database': config['database']['database']
        }

    def connect_to_database(self):
        if not self.conn:  # Sprawdzamy, czy połączenie już istnieje
            try:
                self.conn = mysql.connector.connect(
                    host=self.db_config['host'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['database']
                )
                print("Połączono z bazą danych")
            except mysql.connector.Error as err:
                print(f"Błąd połączenia: {err}")
                self.conn = None
        return self.conn

    def insert_data(self, temperature, humidity):
        conn = self.connect_to_database()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO SensorDateTable (Temperature, Humidity, Time) VALUES (%s, %s, NOW())"
            cursor.execute(query, (temperature, humidity))
            conn.commit()
            cursor.close()
            print("Dane zapisane do bazy!")
        else:
            print("Brak połączenia z bazą danych.")

    def clean_database(self):
        conn = self.connect_to_database()
        if conn:
            cursor = conn.cursor()
            query = "DELETE FROM SensorDateTable"
            cursor.execute(query)
            conn.commit()
            cursor.close()
            print("Dane zostały usunięte.")
        else:
            print("Błąd połączenia z bazą danych. Dane nie zostały usunięte.")
