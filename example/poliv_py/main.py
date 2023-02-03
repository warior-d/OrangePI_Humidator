from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QWidget, QApplication, \
    QAction, qApp, QPushButton, QDesktopWidget, QComboBox, QProgressBar, QLineEdit, \
    QSpacerItem, QVBoxLayout, QGroupBox
import os
from PyQt5 import uic, QtGui
import OPi.GPIO as GPIO
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from BME280 import *
import datetime
import re
import requests
import json


GPIO.setboard(GPIO.ZERO)  # Orange Pi Zero board
GPIO.setmode(GPIO.SOC)  # set up SOC numbering
s1 = GPIO.PA + 10#10
s2 = GPIO.PA + 20#20
key = GPIO.PA + 9#9
GPIO.setup(s1, GPIO.IN)
GPIO.setup(s2, GPIO.IN)
GPIO.setup(key, GPIO.IN)

class Settings():
    URL_OPNWTHR = 'https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}'
    API_KEY = 'e5079959288766955333e44bafe83b44'
    LUB_LAT = '55.682569'
    LUB_LON = '37.879211'
    DATE_MILESTONE = '1675346579' # точка осчета - время не может быть раньше!
    NOW_DATE_UNIX = ''
    TODAY_SUNRISE_UNIX = ''
    TODAY_SUNSET_UNIX = ''
    NOW_TEMPERATURE = ''
    COUNTER_BPM_280 = 2 # Как часто будет restart
    COUNTER_HTTP = 600 # Как часто будет restart, переопрос OpenWeather - не часто...


class MainWidget(QWidget):

    event_detected_s1 = pyqtSignal(int)
    event_detected_key = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        uic.loadUi('tab_ui.ui', self)
        #self.label_2.setText()
        self.default_hum = 50
        self.labelNeedHum.setText(str(self.default_hum))
        self.pushButton_2.clicked.connect(self.returnOK)
        self.pushButton.clicked.connect(self.returnSOME)
        self.event_detected_key.connect(self.on_gpio_event_key)
        self.event_detected_s1.connect(self.on_gpio_event_s1)
        GPIO.add_event_detect(key, GPIO.FALLING, callback=self.event_detected_key.emit)
        GPIO.add_event_detect(s1, GPIO.RISING, callback=self.event_detected_s1.emit)
        ###
        self.timer_BPM280 = QTimer(self)
        self.timer_BPM280.start(1000)
        self.timer_BPM280.timeout.connect(self.showCounter)
        self.counter_BPM280 = Settings.COUNTER_BPM_280
        ###
        self.timer_http = QTimer(self)
        self.timer_http.start(1000)
        self.timer_http.timeout.connect(self.showCounter)
        self.counter_http = Settings.COUNTER_HTTP
        ###
        self.startWatch = True

        self.husterezis = 2
        self.ps = BME280()
        self.temperature = 0
        self.humidity = 0
        self.pressure = 0
        self.iconFiles = {'gray': 'icon32gray.png', 'green': 'icon32green.png', 'red': 'icon32red.png'}
        self.labelLed.setPixmap(QtGui.QPixmap(self.iconFiles['gray']))

        self.getMeasures()
        self.httpRequestOpenWeather()

    def showCounter(self):
        if self.startWatch:
            self.counter_BPM280 -= 1
            self.counter_http -= 1

        if self.counter_BPM280 < 1:
            self.restart_BPM280()

        if self.counter_http < 1:
            self.restart_http()


    def restart_BPM280(self):
        self.counter_BPM280 = Settings.COUNTER_BPM_280
        self.getMeasures()

    def restart_http(self):
        self.counter_http = Settings.COUNTER_HTTP
        self.httpRequestOpenWeather()

    def getMeasures(self):
        ps_data = self.ps.get_data()
        self.temperature = ps_data['t']
        self.humidity = ps_data['h']
        self.pressure = round(ps_data['p'] * 0.00750061683, 2)
        self.labelCurTemp.setText(str(round(self.temperature, 1)))
        self.labelCurPres.setText(str(round(self.pressure, 1)))
        self.labelCurHum.setText(str(round(self.humidity, 1)))
        if( self.humidity <= (self.default_hum - self.husterezis) ):
            self.labelLed.setPixmap(QtGui.QPixmap(self.iconFiles['green']))
            #print("on!")

        if( self.humidity >= self.default_hum ):
            self.labelLed.setPixmap(QtGui.QPixmap(self.iconFiles['red']))
            #print("off!")

        cpu_temp_file = open("/sys/class/thermal/thermal_zone1/temp")
        cpu_temp = cpu_temp_file.read()
        cpu_temp_file.close()
        self.labelCurCPU.setText(str(cpu_temp))
        #print("get values: ", self.temperature,' ', self.humidity,' ', self.pressure, ' ', cpu_temp)

    def httpRequestOpenWeather(self):
        header = {"Content-type": "text/plain",
                  "Accept": "application/json",
                  "Connection": "keep-alive"}
        url = Settings.URL_OPNWTHR.format(Settings.LUB_LAT, Settings.LUB_LON, Settings.API_KEY)
        req = requests.get(url, headers = header)
        status_http = int(req.status_code)

        if( status_http == 200 ):
            req.encoding
            jsonData = req.json()
            Settings.NOW_DATE_UNIX = jsonData['dt']
            Settings.NOW_TEMPERATURE = round(jsonData['main']['temp'] - 273.15, 2)
            Settings.TODAY_SUNRISE_UNIX = jsonData['sys']['sunrise']
            Settings.TODAY_SUNSET_UNIX = jsonData['sys']['sunset']
            self.labelCurWeatherTemp.setText(str(Settings.NOW_TEMPERATURE))

    def hum_change(self, value):

        if not value:
            if (self.default_hum > 0):
                self.default_hum = self.default_hum - 1
        else:
            if (self.default_hum < 100):
                self.default_hum = self.default_hum + 1
        self.labelNeedHum.setText(str(self.default_hum))

    def on_gpio_event_s1(self, s1):
        # ивент при вращении - вызвать функцию
        state_s1 = GPIO.input(s1)
        state_s2 = GPIO.input(s2)
        self.hum_change(state_s2)

    def on_gpio_event_key(self, key):
        # нажатие кнопки
        print("on_gpio_event_key S1 {} S2 {}".format(GPIO.input(s1), GPIO.input(s2)))

    def returnOK(self):
        print('OK!')
        GPIO.cleanup()

    def returnSOME(self):
        print(GPIO.input(s1), GPIO.input(s2))


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    window = MainWidget()
    window.show()
    sys.exit(app.exec_())
