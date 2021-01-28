import time
import requests
from LCD import LCD

URL = 'http://localhost:8000'
LCD_ADDRESS = 0x27
lcd = LCD(2, LCD_ADDRESS, True)
lcd.clear()
counter = 0

while True:
    try:
        data = requests.get(URL).json()
        temp_text = '{:.1f}C'.format(data['temperature'])
        hum_text = '{:.1f}%'.format(data['humidity'])
        counter = (counter + 1) % 11
        temp_c = 0
        while temp_c < counter:
            temp_text = ' '+temp_text
            hum_text = ' '+hum_text
            temp_c += 1
        lcd.clear()
        lcd.message(temp_text, 1)
        lcd.message(hum_text, 2)
    except:
        lcd.clear()
        lcd.message("Service", 1)
        lcd.message("Unavailable", 2)
    time.sleep(3)