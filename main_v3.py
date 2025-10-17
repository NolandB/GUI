# main.py with real sensor
import pandas as pd
import os
from datetime import datetime
import matplotlib.dates as mdates
from nicegui import ui, app
import csv
from collections import deque
import shutil

# Import your fake sensor
from Sensordata import SEN55

# --- Configuration ---
UI_UPDATE_INTERVAL_SECONDS = 1
DATA_COLLECTION_INTERVAL_SECONDS = 300 # 5 minutes

# --- Define save paths ---
LOCAL_SAVE_DIR = '/home/access/Desktop/data'
USB_SAVE_DIR = '/media/access/6AD2-B6E8/data'

# --- Application State ---
sensor = SEN55()
plot_data = deque(maxlen=50) # For the live plot
latest_reading = {}
session_data = [] 
app.storage.general.setdefault('operator_name', 'Default User')
app.storage.general.setdefault('base_filename', 'SensorLog')

# --- GUI Elements ---
ui.label('SEN55 Environmental Monitor').classes('text-2xl font-bold')
with ui.row().classes('w-full items-center'):
    name_input = ui.input('Operator Name').bind_value(app.storage.general, 'operator_name')
    file_input = ui.input('Base Filename').bind_value(app.storage.general, 'base_filename')
start_button = ui.button('Start Logging')
stop_button = ui.button('Stop Logging')

# Plot
plot = ui.line_plot(n=3, figsize=(10, 5)).with_legend(['Temperature', 'Humidity', 'PM1.0'])
plot.props['options'] = {'title': {'text': 'Live Sensor Data'}}

# Current value cards
with ui.row():
    temp_card = ui.card()
    hum_card = ui.card()
    pm1_card = ui.card()
with temp_card:
    temp_label = ui.label('Temperature: --')
with hum_card:
    hum_label = ui.label('Humidity: --')
with pm1_card:
    pm1_label = ui.label('PM1.0: --')

# --- Helper Functions ---
def apply_color_label(card: ui.card, value: float, thresholds: list):
    """Applies a background color to a card based on a value and thresholds."""
    color_class = 'bg-red-500' # Default color
    for lower, upper, class_name in thresholds:
        if (lower is None or value >= lower) and (upper is None or value <= upper):
            color_class = class_name
            break
    all_colors = ['bg-green-500', 'bg-yellow-400', 'bg-red-500']
    card.classes(remove=' '.join(all_colors), add=color_class)

# --- Core Logic Functions ---
def poll_sensor_and_update_ui():
    global latest_reading
    reading = sensor.read_data()
    latest_reading = {
        'timestamp': datetime.now(),
        'temperature': reading['temperature'], 'humidity': reading['humidity'],
        'pm1p0': reading['pm1p0'], 'pm2p5': reading['pm2p5'], 'pm4p0': reading['pm4p0'],
        'pm10p0': reading['pm10p0'], 'voc_index': reading['voc_index'], 'nox_index': reading['nox_index'],
    }
    plot_data.append(latest_reading)
    try:
        df = pd.DataFrame(list(plot_data))
        temp_val, hum_val, pm1_val = df['temperature'].iloc[-1], df['humidity'].iloc[-1], df['pm1p0'].iloc[-1]
        x_num = mdates.date2num(df['timestamp'].iloc[-1])
        plot.push([x_num], [[temp_val], [hum_val], [pm1_val]])
        ax = plot.fig.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plot.fig.autofmt_xdate(rotation=45)
        
        # --- THESE ARE THE CORRECTED LINES ---
        temp_label.set_text(f"Temperature: {temp_val:.2f} °C")
        hum_label.set_text(f"Humidity: {hum_val:.2f} %")
        pm1_label.set_text(f"PM1.0: {pm1_val:.2f} µg/m³")
        
        apply_color_label(temp_card, temp_val, [ (20, 23, 'bg-green-500'), (18, 20, 'bg-yellow-400'), (23, 25, 'bg-yellow-400'), (None, 18, 'bg-red-500'), (25, None, 'bg-red-500') ])
        apply_color_label(hum_card, hum_val, [ (30, 40, 'bg-green-500'), (25, 30, 'bg-yellow-400'), (40, 45, 'bg-yellow-400'), (None, 25, 'bg-red-500'), (45, None, 'bg-red-500') ])
        apply_color_label(pm1_card, pm1_val, [ (None, 3, 'bg-green-500'), (3, 5, 'bg-yellow-400'), (5, None, 'bg-red-500') ])

    except Exception as e:
        print(f'UI update error: {e}')

def collect_data_point():
    if latest_reading:
        session_data.append(latest_reading.copy())
        ui.notify(f'Data point collected. Total points: {len(session_data)}')

def save_session_to_files():
    ui_timer.deactivate()
    collection_timer.deactivate()
    try:
        if sensor:
            sensor.stop()
        ui.notify('Sensor successfully stopped.', type='positive')
    except Exception as e:
        ui.notify(f'Error stopping sensor: {e}', type='negative')
    ui.notify('Monitoring stopped. Saving data...')
    if not session_data:
        ui.notify('No data was collected to save.', type='warning')
        return
    op_name, base_file = app.storage.general.get('operator_name'), app.storage.general.get('base_filename')
    today_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{base_file}_{today_str}.csv"
    headers = list(session_data[0].keys())
    def write_log_file(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', newline='') as f:
            f.write(f"# Operator: {op_name}\n")
            f.write(f"# Date: {today_str}\n")
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(session_data)
    local_path = os.path.join(LOCAL_SAVE_DIR, filename)
    try:
        write_log_file(local_path)
        ui.notify(f'Successfully saved to {local_path}', type='positive')
    except Exception as e:
        ui.notify(f'Error saving to Desktop: {e}', type='negative')
        return
    usb_path = os.path.join(USB_SAVE_DIR, filename)
    try:
        write_log_file(usb_path)
        ui.notify(f'Successfully saved copy to USB: {usb_path}', type='positive')
    except Exception as e:
        ui.notify(f'Could not save to USB: {e}', type='warning')

def start_logging():
    session_data.clear() 
    ui_timer.activate()
    collection_timer.activate()
    ui.notify('Monitoring started.')

# --- Run the App ---
ui_timer = ui.timer(UI_UPDATE_INTERVAL_SECONDS, poll_sensor_and_update_ui, active=False)
collection_timer = ui.timer(DATA_COLLECTION_INTERVAL_SECONDS, collect_data_point, active=False)

start_button.on('click', start_logging)
stop_button.on('click', save_session_to_files)

ui.run(title="SEN55 Monitor")
