# main.py
import pandas as pd
from datetime import datetime
from nicegui import ui, app
#change to real sensor
from fake_sensor import FakeSEN55

dataFile = 'sen55Log.csv'
LOGGING_INTERVAL_SECONDS = 5  #change to 300
logging = False

# change to real sensor
sensor = FakeSEN55()

dataLabel = pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'pm1','pm25', 'pm4', 'pm10', 'voc_index', 'nox_index'])

# --- GUI Elements ---
ui.label('SEN55 Environmental Monitor').classes('text-2xl font-bold')
start_button = ui.button('Start Logging', on_click=lambda: start_logging())
stop_button = ui.button('Stop Logging', on_click=lambda: stop_logging()).set_visibility(False)

# Chart for plotting data
plot = ui.line_plot(n=1, figsize=(10, 5), update_every=1).with_props({
    'options': {
        'title': {'text': 'Live Sensor Data'},
        'xAxis': {'type': 'category'},
        'yAxis': {'title': {'text': 'Values'}},
    }
})

# --- Functions ---
def start_logging():
    global logging
    logging = True
    start_button.set_visibility(False)
    stop_button.set_visibility(True)
    ui.notify('Started data logging.')
    try:
        pd.read_csv(dataFile)
    except FileNotFoundError:
        data_points.to_csv(dataFile, index=False)


def stop_logging():
    global logging
    logging = False
    start_button.set_visibility(True)
    stop_button.set_visibility(False)
    ui.notify('Stopped data logging.')

def log_data():
    if not logging:
        return

    reading = sensor.read_data()#change to real sensor
    timestamp = datetime.now()

   
    new_data = pd.DataFrame([{
        'timestamp': timestamp,
        'pm1p0': reading['pm1p0'],
        'pm2p5': reading['pm2p5'],
        'pm4p0': reading['pm4p0'],
        'pm10p0': reading['pm10p0'],
        'temperature': reading['temperature'],
        'humidity': reading['humidity'],
        'voc_index': reading['voc_index'],
        'nox_index': reading['nox_index'],
    }])
    
    # Append to the main DataFrame and save to CSV
    global data_points
    data_points = pd.concat([data_points, new_data], ignore_index=True)
    new_data.to_csv(dataFile, mode='a', header=False, index=False)

    # Update the plot
    # Keep only the last 50 points for a clean plot
    last_50 = data_points.tail(50)
    time_str = [dt.strftime('%H:%M:%S') for dt in last_50['timestamp']]
    
    plot.push(time_str, [
        {'name': 'Temperature', 'data': last_50['temperature'].tolist()},
        {'name': 'Humidity', 'data': last_50['humidity'].tolist()},
        {'name': 'PM2.5', 'data': last_50['pm25'].tolist()},
    ])

# --- Run the App ---
# Use a timer to call the log_data function periodically
app_timer = ui.timer(LOGGING_INTERVAL_SECONDS, log_data, active=True)
ui.run()