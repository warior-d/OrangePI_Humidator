from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QWidget, QApplication, \
    QAction, qApp, QPushButton, QDesktopWidget, QComboBox, QProgressBar, QLineEdit, \
    QSpacerItem, QVBoxLayout, QGroupBox
import os
from PyQt5 import uic
import OPi.GPIO as GPIO
from PyQt5.QtCore import Qt, pyqtSignal

GPIO.setboard(GPIO.ZERO)  # Orange Pi Zero board
GPIO.setmode(GPIO.SOC)  # set up SOC numbering
s1 = GPIO.PA + 10#10
s2 = GPIO.PA + 20#20
key = GPIO.PA + 9#9
GPIO.setup(s1, GPIO.IN)
GPIO.setup(s2, GPIO.IN)
GPIO.setup(key, GPIO.IN)


class MainWidget(QWidget):
    event_detected_s1 = pyqtSignal(int)
    event_detected_key = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        uic.loadUi('widj.ui', self)
        #self.label_2.setText()
        self.default_hum = 50
        self.labelNeedHum.setText(str(self.default_hum))
        self.pushButton_2.clicked.connect(self.returnOK)
        self.pushButton.clicked.connect(self.returnSOME)
        self.event_detected_key.connect(self.on_gpio_event_key)
        self.event_detected_s1.connect(self.on_gpio_event_s1)
        GPIO.add_event_detect(key, GPIO.FALLING, callback=self.event_detected_key.emit)
        GPIO.add_event_detect(s1, GPIO.RISING, callback=self.event_detected_s1.emit)

    def on_gpio_event_s1(self, s1):
        # your code here!
        state_s1 = GPIO.input(s1)
        state_s2 = GPIO.input(s2)
        self.hum_change(state_s2)


    def hum_change(self, value):

        if not value:
            if (self.default_hum > 0):
                self.default_hum = self.default_hum - 1
        else:
            if (self.default_hum < 100):
                self.default_hum = self.default_hum + 1

        self.labelNeedHum.setText(str(self.default_hum))

    def on_gpio_event_key(self, key):
        # your code here!
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
