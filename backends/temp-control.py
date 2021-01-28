from gevent import monkey
monkey.patch_all()

import RPi.GPIO as GPIO
import json
import requests
import time
from flask import Flask
from threading import Thread

RELAY_PIN = 27
URL = 'http://localhost:8000'
RELAY_ON_TEMP = 42.0
RELAY_OFF_TEMP = 40.0
RELAY_STATUS = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

def event_loop():
    global RELAY_PIN
    global URL
    global RELAY_ON_TEMP
    global RELAY_OFF_TEMP
    global RELAY_STATUS
    while True:
        try:
            data = requests.get(URL).json()
            temperature = data['temperature']
            humidity = data['humidity']
            if temperature > RELAY_ON_TEMP:
                RELAY_STATUS = 1
                GPIO.output(RELAY_PIN, RELAY_STATUS)
            elif temperature < RELAY_OFF_TEMP:
                RELAY_STATUS = 0
                GPIO.output(RELAY_PIN, RELAY_STATUS)
        except:
            print('error reading values')
        time.sleep(5.0)

app = Flask(__name__)
@app.route('/')
def show_values():
    global RELAY_STATUS
    value = {
        'relay': RELAY_STATUS
    }
    return json.dumps(value)


if __name__ == "__main__":
    Thread(target=event_loop).start()

    from gevent.pywsgi import WSGIServer
    server = WSGIServer(('0.0.0.0', 8001), app)
    server.serve_forever()