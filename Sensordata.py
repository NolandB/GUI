import time
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sensorbridge import SensorBridgePort, SensorBridgeShdlcDevice, SensorBridgeI2cProxy
from sensirion_i2c_sen5x import Sen5xI2cDevice
from sensirion_i2c_driver import I2cConnection

class SEN55:
    def __init__(self):
        print("Initializing REAL Sensirion SEN55 Sensor...")
        SERIAL_PORT = "/dev/ttyUSB0" 
        
        try:
            self.port = ShdlcSerialPort(port=SERIAL_PORT, baudrate=460800)
            self.port.open()
            
            bridge = SensorBridgeShdlcDevice(ShdlcConnection(self.port), slave_address=0)
            bridge_port = SensorBridgePort.ONE 

            bridge.set_supply_voltage(bridge_port, voltage=5.0)
            bridge.switch_supply_on(bridge_port)
            bridge.set_i2c_frequency(bridge_port, frequency=100000)

            i2c_proxy = SensorBridgeI2cProxy(bridge, port=bridge_port)
            i2c_connection = I2cConnection(i2c_proxy)
            self.sen5x = Sen5xI2cDevice(i2c_connection)

            # Start the measurement
            self.sen5x.start_measurement()
            
            print("Successfully initialized REAL sensor.")
        
        except Exception as e:
            print(f"Failed to initialize REAL sensor: {e}")
            print("Please check connection and port permissions.")
            raise

    def read_data(self):
        try:
            values = self.sen5x.read_measured_values()
            data = {
                'pm1p0': round(values.mass_concentration_1p0.physical, 2) if values.mass_concentration_1p0 else 0.0,
                'pm2p5': round(values.mass_concentration_2p5.physical, 2) if values.mass_concentration_2p5 else 0.0,
                'pm4p0': round(values.mass_concentration_4p0.physical, 2) if values.mass_concentration_4p0 else 0.0,
                'pm10p0': round(values.mass_concentration_10p0.physical, 2) if values.mass_concentration_10p0 else 0.0,
                'temperature': round(values.ambient_temperature.degrees_celsius, 2) if values.ambient_temperature else 0.0,
                'humidity': round(values.ambient_humidity.percent_rh, 2) if values.ambient_humidity else 0.0,
                'voc_index': round(values.voc_index.scaled, 2) if values.voc_index else 0.0,
                'nox_index': round(values.nox_index.scaled, 0) if values.nox_index else 0.0, # Match fake sensor's int rounding
            }
            return data
            
        except Exception as e:
            print(f"Error reading sensor data: {e}")
            return {
                'pm1p0': 0.0, 'pm2p5': 0.0, 'pm4p0': 0.0, 'pm10p0': 0.0,
                'temperature': 0.0, 'humidity': 0.0, 'voc_index': 0.0, 'nox_index': 0.0
            }

    def stop(self):
        print("Stopping sensor measurement and closing port...")
        try:
            self.sen5x.stop_measurement()
            self.port.close()
            print("Sensor stopped and port closed.")
        except Exception as e:
            print(f"Error during sensor stop: {e}")

