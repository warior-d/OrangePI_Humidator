from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QWidget, QApplication, \
    QAction, qApp, QPushButton, QDesktopWidget, QComboBox, QProgressBar, QLineEdit, \
    QSpacerItem, QVBoxLayout, QGroupBox
import os
from PyQt5 import uic, QtGui
import OPi.GPIO as GPIO
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPixmap, QPen
from BME280 import *
from datetime import datetime
import re
import requests
import json


# TODO:
# разделить http и каунтер проверки лампы



GPIO.setboard(GPIO.ZERO)  # Orange Pi Zero board
GPIO.setmode(GPIO.SOC)  # set up SOC numbering
s1 = GPIO.PA + 10#10
s2 = GPIO.PA + 20#20
key = GPIO.PA + 9#9
hum_pin = GPIO.PA + 6
light_pin = GPIO.PA + 7
GPIO.setup(s1, GPIO.IN)
GPIO.setup(s2, GPIO.IN)
GPIO.setup(key, GPIO.IN)
GPIO.setup(hum_pin, GPIO.OUT)
GPIO.setup(light_pin, GPIO.OUT)

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
    TIME_START_LAMP = 8
    TIME_FINISH_LAMP = 20
    TIME_SHIFT = 5 # минут запаса
    CPU_TEMP_FILE = "/sys/class/thermal/thermal_zone1/temp"


class MainWidget(QWidget):

    event_detected_s1 = pyqtSignal(int)
    event_detected_key = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        uic.loadUi('tab_ui.ui', self)
        screen_width = QApplication.instance().desktop().availableGeometry().width()
        screen_height = QApplication.instance().desktop().availableGeometry().height()
        print(screen_width,'*',screen_height)
        self.setGeometry(0, 0, screen_width, screen_height)
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
        #
        self.tabWidget.currentChanged.connect(self.barClickEvent)
        # Потом сделать true!
        self.may_draw = False
        #
        self.humi_pin_status = False
        self.light_pin_status = False

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
            self.setHumidity('ON')

        if( self.humidity >= self.default_hum ):
            self.labelLed.setPixmap(QtGui.QPixmap(self.iconFiles['red']))
            self.setHumidity('OFF')

        cpu_temp_file = open(Settings.CPU_TEMP_FILE)
        cpu_temp = cpu_temp_file.read()
        cpu_temp_file.close()
        self.labelCurCPU.setText(str(round(int(cpu_temp), 1))) # такая конструкция, чтобы число вертикально было!

    def setHumidity(self, state):
        currentState = GPIO.input(hum_pin)
        if state == 'ON' and currentState == 0:
            GPIO.output(hum_pin, 1)
            print('HUM ON PIN!')

        if state == 'OFF' and currentState == 1:
            GPIO.output(hum_pin, 0)
            print('HUM OFF PIN!')

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
            self.may_draw = True

        if(Settings.NOW_DATE_UNIX):
            datetime_object = datetime.fromtimestamp(Settings.NOW_DATE_UNIX)
            start_day = datetime_object.replace(second=0, microsecond=0, minute=0, hour=0)
            start_day_UNIX = int(start_day.timestamp())
            finish_day = datetime_object.replace(second=59, microsecond=999999, minute=59, hour=23)
            finish_day_UNIX = int(finish_day.timestamp())

            time_sunrise_str = datetime.fromtimestamp(Settings.TODAY_SUNRISE_UNIX).strftime('%H:%M')
            time_sunset_str = datetime.fromtimestamp(Settings.TODAY_SUNSET_UNIX).strftime('%H:%M')
            cur_date = datetime.fromtimestamp(Settings.NOW_DATE_UNIX).strftime('%d.%m.%Y')
            self.labelSunrise.setText(str(time_sunrise_str))
            self.labelSunset.setText(str(time_sunset_str))
            self.labelDate.setText(str(cur_date))
            #print(time_sunrise_str, time_sunset_str, " -=- " , datetime_object, '-----', start_day_UNIX, finish_day_UNIX)
            self.lightUp()
            #self.drawLightTime()

    def lightUp(self):

        # определяем, нужно ли включать свет!
        light = False
        currentStateLight = GPIO.input(light_pin)

        datetime_now = datetime.fromtimestamp(Settings.NOW_DATE_UNIX)
        now_ts = int(datetime_now.timestamp())

        hour_8 = datetime_now.replace(second=0, microsecond=0, minute=0, hour=Settings.TIME_START_LAMP)
        hour_8_UNIX = int(hour_8.timestamp())
        hour_20 = datetime_now.replace(second=0, microsecond=0, minute=0, hour=Settings.TIME_FINISH_LAMP)
        hour_20_UNIX = int(hour_20.timestamp())

        if( ( (now_ts > hour_8_UNIX)  and (now_ts < hour_20_UNIX) ) \
            and ( (now_ts < (Settings.TODAY_SUNRISE_UNIX + Settings.TIME_SHIFT*60)) \
            or \
            (now_ts > (Settings.TODAY_SUNSET_UNIX - Settings.TIME_SHIFT * 60)) ) ):
            light = True

        if light == True and currentStateLight == 0:
            GPIO.output(light_pin, 1)
            print('LIGHT ON PIN!')

        if light == False and currentStateLight == 1:
            GPIO.output(light_pin, 0)
            print('LIGHT OFF PIN!')

        print( datetime_now, '-now_ts LIGHT: ', light)
        return light

    def barClickEvent(self):
        # 0 - General
        # 1 - Weather
        self.may_draw = False
        currentTab = self.tabWidget.currentIndex()

        if currentTab == 0:
            self.may_draw = True



    def paintEvent(self, e):
        if self.may_draw == True:

            pixmap = QPixmap(self.labelDraw.size())
            pixmap.fill(Qt.white)
            painter = QPainter(pixmap)
            painter.begin(self)

            hours = 24
            seconds = 86400
            ### Рисуем утренний и вечерний запрет!
            morning_end_pixels = int((Settings.TIME_START_LAMP * self.labelDraw.width()) / hours)
            evening_start_pixels = int(((hours - Settings.TIME_FINISH_LAMP) * self.labelDraw.width()) / hours)

            painter.setPen(QColor(100,102,100,150))
            brush = QBrush(QColor(100,102,100,150))
            painter.setBrush(brush)
            painter.drawRect(0, 0, morning_end_pixels, self.labelDraw.height())
            painter.drawRect(self.labelDraw.width() - evening_start_pixels, 0, self.labelDraw.width(), self.labelDraw.height())
            ###

            ### Рисуем сейчас!
            datetime_now = datetime.fromtimestamp(Settings.NOW_DATE_UNIX)
            now_ts = int(datetime_now.timestamp())
            hour_0 = datetime_now.replace(second=0, microsecond=0, minute=0, hour=0)
            hour_0_UNIX = int(hour_0.timestamp())
            delta_seconds = (now_ts  - hour_0_UNIX)
            now_pixels = (delta_seconds * self.labelDraw.width()) / seconds
            painter.setPen(QPen(QColor(0, 165, 80), 4, Qt.SolidLine))
            painter.drawLine(now_pixels, 0, now_pixels, self.labelDraw.height())
            ###

            ### Рисуем рассветы и закаты если нужны!
            hour_8 = datetime_now.replace(second=0, microsecond=0, minute=0, hour=Settings.TIME_START_LAMP)
            hour_8_UNIX = int(hour_8.timestamp())
            hour_20 = datetime_now.replace(second=0, microsecond=0, minute=0, hour=Settings.TIME_FINISH_LAMP)
            hour_20_UNIX = int(hour_20.timestamp())

            if (Settings.TODAY_SUNSET_UNIX - Settings.TIME_SHIFT * 60) < hour_20_UNIX:
                seconds_to_sunset_pixels = int(((Settings.TODAY_SUNSET_UNIX - Settings.TIME_SHIFT * 60) - hour_0_UNIX) * self.labelDraw.width() / seconds)
                fin = int((Settings.TIME_FINISH_LAMP * self.labelDraw.width()) / hours)
                painter.setPen(QColor(153, 0, 122, 90))
                brush = QBrush(QColor(153,0,122,90))
                painter.setBrush(brush)
                painter.drawRect(seconds_to_sunset_pixels, 0, fin - seconds_to_sunset_pixels, self.labelDraw.height())

            if (Settings.TODAY_SUNRISE_UNIX + Settings.TIME_SHIFT*60) > hour_8_UNIX:
                seconds_from_sunrise_pixels = int(((Settings.TODAY_SUNRISE_UNIX + Settings.TIME_SHIFT*60) - hour_0_UNIX) * self.labelDraw.width() / seconds)
                strt = int((Settings.TIME_START_LAMP * self.labelDraw.width()) / hours)
                painter.setPen(QColor(153, 0, 122, 90))
                brush = QBrush(QColor(153,0,122,90))
                painter.setBrush(brush)
                painter.drawRect(strt, 0, seconds_from_sunrise_pixels - strt, self.labelDraw.height())
            ###

            painter.end()

            self.labelDraw.setPixmap(pixmap)
            self.may_draw = False


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

    def closeEvent(self, event):
        GPIO.cleanup()

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    window = MainWidget()
    window.show()
    sys.exit(app.exec_())
