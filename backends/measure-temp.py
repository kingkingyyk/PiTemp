from gevent import monkey
monkey.patch_all()

import Adafruit_DHT
import json
import time
from threading import Thread
from flask import Flask
from subprocess import check_output

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 17
CURRENT_TEMPERATURE = None
CURRENT_HUMIDITY = None
CURRENT_PI_TEMP = None

def update_temp():
    global CURRENT_TEMPERATURE
    global CURRENT_HUMIDITY
    global CURRENT_PI_TEMP
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            CURRENT_TEMPERATURE = temperature
            CURRENT_HUMIDITY = humidity
            CURRENT_PI_TEMP = float(check_output(['vcgencmd', 'measure_temp']).decode('UTF-8')[5:-3])
        time.sleep(5.0)

app = Flask(__name__)
@app.route('/')
def show_values():
    global CURRENT_TEMPERATURE
    global CURRENT_HUMIDITY
    value = {
        'temperature': CURRENT_TEMPERATURE,
        'humidity': CURRENT_HUMIDITY,
        'pi-temp': CURRENT_PI_TEMP,
    }
    return json.dumps(value)

if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer

    Thread(target=update_temp).start()
    server = WSGIServer(('0.0.0.0', 8000), app)
    server.serve_forever()