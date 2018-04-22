import sys, time, thread, threading, json, Adafruit_DHT, Adafruit_SSD1306, thingspeak
from time import strftime, localtime
import RPi.GPIO as GPIO
from PIL import Image, ImageFont, ImageDraw

"""
    Read settings
"""
settings_file = open('settings.json','r')
settings = json.loads(settings_file.read())
settings_file.close()

"""
    Setup screen
"""
oled = Adafruit_SSD1306.SSD1306_128_64(rst=24)
oled.begin()

"""
    Setup GPIO
"""
relay_pin = settings['Relay']['pin']

GPIO.setup(relay_pin, GPIO.OUT)
dht_obj = None
dht_pin = settings['DHT']['pin']
dht_type = settings['DHT']['type']
if dht_type == '11':
    dht_obj = Adafruit_DHT.DHT11
elif dht_type == '22':
    dht_obj = Adafruit_DHT.DHT22
elif dht_type == '2302':
    dht_obj = Adafruit_DHT.AM2302

"""
    Setup misc
"""
thingspeak_obj = thingspeak.Channel(id = settings['ThingSpeak']['channel-id'],
                                    write_key = settings['ThingSpeak']['write-key'],
                                    timeout = settings['ThingSpeak']['timeout'])
font_style = settings['Display']['font']
"""
    Data
"""
temperature = 0.0
humidity = 0.0
relay = 0
countdown = 0
is_relay_on = False

def read_dht(dht_obj, dht_pin):
    global temperature, humidity
    last_update_time = time.time()
    while True:
        curr_hum, curr_temp = Adafruit_DHT.read_retry(dht_obj, dht_pin, delay_seconds=0.5)
        with threading.Lock():
            humidity = curr_hum
            temperature = curr_temp
        if time.time() - last_update_time < 5:
           time.sleep(5)
           last_update_time = time.time()

def update_thingspeak():
    global temperature, humidity, relay
    while True:
        if temperature > 0.0 and humidity > 0.0:
            try:
                thingspeak_obj.update({1: temperature, 2: humidity, 3: relay})
            except:
                pass
            time.sleep(15)
        else:
            time.sleep(1)

def update_oled(oled):
    global temperature, humidity, countdown
    x = 0
    while True:
        x = (x+1)%300
        try:
            oled.clear()
            buffer = Image.new('1',(128,64))
            buffer_draw=ImageDraw.Draw(buffer)
            font_big=ImageFont.truetype(font_style,size=25)
            buffer_draw.text((x%15,0), strftime('%d %h %-I:%M:%S%p',localtime()), font=font_big, fill=255)
            buffer_draw.text((x%20,26), '{:.2f}C | {:.2f}%'.format(temperature,humidity), font=font_big, fill=255)
            font_small=ImageFont.load_default()
            buffer_draw.text((x%100,54), '{:d}'.format(countdown), font=font_small, fill=255)
            oled.image(buffer)
            oled.display()
        except:
            pass
        time.sleep(1)

def relay_control():
    global countdown
    set_relay_pin(True)
    while True:
        control_file = open('control.json', 'r')
        control = json.loads(control_file.read())
        control_file.close()

        target_temp = control['target-temperature']
        relaxation = control['relaxation']
        duration = control['duration']

        min_temp = target_temp - relaxation
        max_temp = target_temp + relaxation
        
        if temperature >= max_temp:
            set_relay_pin(True)
        elif temperature <= min_temp:
            set_relay_pin(False)
        elif is_relay_on:
            if temperature < target_temp:
                countdown = countdown + 1
            if countdown >= duration:
                set_relay_pin(False)
        else:
            if temperature > target_temp:
                countdown = countdown + 1
            if countdown >= duration:
                set_relay_pin(True)

        time.sleep(1)


def set_relay_pin(flag):
    global countdown, is_relay_on
    if flag:
        with threading.Lock():
            countdown = 0
            is_relay_on = True
            relay = 1
        GPIO.output(relay_pin, GPIO.HIGH)
    else:
        with threading.Lock():
            countdown = 0
            is_relay_on = False
            relay = 0
        GPIO.output(relay_pin, GPIO.LOW)


thread.start_new_thread(read_dht,(dht_obj, dht_pin, ))
thread.start_new_thread(update_thingspeak,())
thread.start_new_thread(update_oled,(oled, ))
thread.start_new_thread(relay_control,())

while 1:
    time.sleep(60)
