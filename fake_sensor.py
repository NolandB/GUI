# fake_sensor.py for real sensor, replace with actual sensor library
import random
import time

class FakeSEN55:
    def __init__(self):
        print("Initialized FAKE Sensirion SEN55 Sensor.")

    def read_data(self):
        time.sleep(.5)
        
        data = {
            'pm1p0': round(random.uniform(0.0, 7.0), 2), 
            'pm2p5': round(random.uniform(5.0, 25.0), 2), 
            'pm4p0': round(random.uniform(5.0, 25.0), 2),
            'pm10p0': round(random.uniform(5.0, 25.0), 2), 
            'temperature': round(random.gauss(21, 4), 2),
            'humidity': round(random.gauss(35.0, 6), 2),
            'voc_index': round(random.uniform(100.0, 300.0), 2),
            'nox_index': round(random.uniform(50.0, 150.0)),
        }
        return data