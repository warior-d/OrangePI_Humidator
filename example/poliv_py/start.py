from BME280 import *
import datetime
import re
import os

temperature_unit = 'C' # 'C' | 'F'
pressure_unit = 'mm Hg' # 'Pa' | 'mm Hg'
humidity_unit = '%'
#========================================
database_name = 'weather.db'
temperature_field = 'temperature'
pressure_field = 'pressure'
humidity_field = 'humidity'

units = {temperature_field: temperature_unit, pressure_field: pressure_unit, humidity_field: humidity_unit}


def convert(value, unit):
    if unit == 'F':
        # Convert from Celsius to Fahrenheit
        return round(1.8 * value + 32.0, 2)
    if unit == 'mm Hg':
         #Convert from Pa to mm Hg
        return round(value * 0.00750061683, 2)
    return value

ps = BME280()
ps_data = ps.get_data()

print(ps_data)

print("Temperature:", convert(ps_data['t'], units[temperature_field]), "_"+units[temperature_field], "Pressure:", convert(ps_data['p'], units[pressure_field]), units[pressure_field], "Humidity:", ps_data['h'], units[humidity_field])

