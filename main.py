# main.py
import pandas as pd
import os
from datetime import datetime
import matplotlib.dates as mdates
from nicegui import ui, app
#change to real sensor
from fake_sensor import FakeSEN55

dataFile = 'sen55Log.csv'
LOGGING_INTERVAL_SECONDS = 1  #change to 300
logging = False
TICK_LIMIT = 288
tick_count = 0

app_timer = None

# change to real sensor
sensor = FakeSEN55()

data_points = pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'pm1p0', 'pm2p5', 'pm4p0', 'pm10p0', 'voc_index', 'nox_index'])

# --- GUI Elements ---
#Title
ui.label('SEN55 Environmental Monitor').classes('text-2xl font-bold')

# Buttons
start_button = ui.button('Start Logging', on_click=lambda: start_logging())
stop_button = ui.button('Stop Logging', on_click=lambda: stop_logging())

stop_button.set_visibility(False)
# Plot
plot = ui.line_plot(n=3, figsize=(10, 5), update_every=1)
plot.props['options'] = {
    'title': {'text': 'Live Sensor Data'}
}
plot.with_legend(['Temperature', 'Humidity', 'PM1.0'])

# Current values
current_row = ui.row()
with current_row:
    base_card_classes = 'px-2 transition-colors duration-500 ease-in-out'
    with ui.card().classes(base_card_classes) as temp_card:
        temp_label = ui.label('Temperature: --')
    with ui.card().classes(base_card_classes) as hum_card:
        hum_label = ui.label('Humidity: --')
    with ui.card().classes(base_card_classes) as pm1_card:
        pm1_label = ui.label('PM1.0: --')
def apply_color_label(container, value, thresholds):
    cls = 'bg-red-500 text-white'  
    for (mn, mx, name) in thresholds:
        if mn is None and value <= mx:
            cls = name
            break
        if mx is None and value >= mn:
            cls = name
            break
        if mn is not None and mx is not None and mn <= value <= mx:
            cls = name
            break
    try:
        mapping = {
            'bg-green-500 text-white': ('#16a34a', '#ffffff'),
            'bg-yellow-400 text-black': ("#f1f50b", "#292929"),
            'bg-red-500 text-white': ('#ef4444', '#ffffff'),
        }
        if cls in mapping:
            bg_color, text_color = mapping[cls]
            try:
                container.style(f'background-color: {bg_color}; color: {text_color};')
                try:
                    base = globals().get('base_card_classes', '')
                    if base:
                        container.classes(base)
                except Exception:
                    pass
            except Exception:
                try:
                    container.classes((globals().get('base_card_classes', '') + ' ' + cls).strip())
                except Exception:
                    pass
        else:
            try:
                container.classes((globals().get('base_card_classes', '') + ' ' + cls).strip())
            except Exception:
                try:
                    container.classes(cls)
                except Exception:
                    pass
    except Exception:
        try:
            container.classes(cls)
        except Exception:
            pass

# --- Functions ---
def start_logging():
    global logging
    global data_points
    logging = True
    start_button.set_visibility(False)
    stop_button.set_visibility(True)
    ui.notify('Started data logging.')
    try:
        df = pd.read_csv(dataFile)
        if data_points.empty:
            data_points = df.copy()
        else:
            data_points = pd.concat([data_points, df], ignore_index=True)
    except FileNotFoundError:
        pd.DataFrame(columns=data_points.columns).to_csv(dataFile, index=False)

def stop_logging():
    global logging
    logging = False
    start_button.set_visibility(True)
    stop_button.set_visibility(False)
    ui.notify('Stopped data logging.')

def log_data():
    global tick_count, app_timer, logging
    tick_count += 1
    if TICK_LIMIT is not None and tick_count >= TICK_LIMIT:
        try:
            if app_timer is not None:
                app_timer.stop()
        except Exception:
            pass
        logging = False
        ui.notify(f'Reached {TICK_LIMIT} ticks — stopping timer.')
        return

    if not logging:
        return
    reading = sensor.read_data()  # change to real sensor
    # Data Inputs
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
    # Add Data To csv
    global data_points
    if data_points.empty:
        data_points = new_data.copy()
    else:
        data_points = pd.concat([data_points, new_data], ignore_index=True)

    if not os.path.exists(dataFile):
        new_data.to_csv(dataFile, mode='w', header=True, index=False)
    else:
        new_data.to_csv(dataFile, mode='a', header=False, index=False)
    data_points['timestamp'] = pd.to_datetime(data_points['timestamp'], errors='coerce')
    valid = data_points.dropna(subset=['timestamp'])
    if valid.empty:
        return
    valid = valid.sort_values('timestamp')
    last_50 = valid.tail(50).copy()
    for col in ['temperature', 'humidity', 'pm1p0', 'pm2p5', 'pm4p0', 'pm10p0']:
        if col in last_50.columns:
            last_50.loc[:, col] = pd.to_numeric(last_50[col], errors='coerce')
    # Update Plot and Current Values
    try:
        newest = last_50.iloc[-1]
        x_num = float(mdates.date2num(newest['timestamp']))
        temp_val = float(pd.to_numeric(newest['temperature'], errors='coerce') or 0.0)
        hum_val = float(pd.to_numeric(newest['humidity'], errors='coerce') or 0.0)
        pm1p0_val = float(pd.to_numeric(newest['pm1p0'], errors='coerce') or 0.0)
        visible = last_50[['temperature', 'humidity', 'pm1p0']].apply(pd.to_numeric, errors='coerce').fillna(0)
        flat = [v for col in visible.columns for v in visible[col].tolist()]
        if not flat:
            return
        min_y = float(min(flat))
        max_y = float(max(flat))
        pad_y = 0.01 * (max_y - min_y) if max_y != min_y else 0.5
        plot.push([x_num], [[temp_val], [hum_val], [pm1p0_val]], x_limits=('auto'), y_limits=(min_y - pad_y, max_y + pad_y))
        ax = plot.fig.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plot.fig.autofmt_xdate(rotation=45)

        # Update current-value labels
        try:
            temp_label.set_text(f"Temperature: {temp_val:.2f} °C")
            hum_label.set_text(f"Humidity: {hum_val:.2f} %")
            pm1_label.set_text(f"PM1.0: {pm1p0_val:.2f} µg/m³")

            temp_thresholds = [
                (20, 23, 'bg-green-500 text-white'),
                (18, 20, 'bg-yellow-400 text-black'),
                (23, 25, 'bg-yellow-400 text-black'),
            ]
            apply_color_label(temp_card, temp_val, temp_thresholds)

            hum_thresholds = [
                (30, 40, 'bg-green-500 text-white'),
                (25, 30, 'bg-yellow-400 text-black'),
                (40, 45, 'bg-yellow-400 text-black'),
            ]
            apply_color_label(hum_card, hum_val, hum_thresholds)

            pm1_thresholds = [
                (None, 3, 'bg-green-500 text-white'),
                (3, 5, 'bg-yellow-400 text-black'),
                (5, None, 'bg-red-500 text-white'),
            ]
            apply_color_label(pm1_card, pm1p0_val, pm1_thresholds)
        except Exception:
            pass
    except Exception as e:
        import traceback
        print('Plot update error:', e)
        traceback.print_exc()

# --- Run the App ---
app_timer = ui.timer(LOGGING_INTERVAL_SECONDS, log_data, active=True)
ui.run()