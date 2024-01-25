#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import requests
from datetime import datetime

from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.virtual import viewport, sevensegment

from bmp280 import BMP280

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

import RPi.GPIO as GPIO
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)


def displayTemperature(sevenSeg, temperature, delay):
    for _ in range(8):
        sevenSeg.text = '{:05.2f}\u00b0C'.format(temperature)
        time.sleep(delay)

def authenticateToServer(session, url, certFile):
   try:
      loginData = {'username':'Sensor1', 'password':'DomekBezpieczny'}
      r = session.post(url, data=loginData, verify=certFile)
      return 0
   except requests.exceptions.RequestException:
      print("Authentication/Connection Error")
      return -1

def sendData(session, url, certFile, temperature, battery, panel):
   try:
      r = session.post(url,
          json = {'temperature':temperature, 'battery':battery, 'panel':panel},
          #cert=(clientCertFile, clientKeyFile),
          verify=certFile)
   except requests.exceptions.RequestException:
      print("Connection Error")
      return -1
   return r.status_code

def getHeatingMode(session, url, certFile, oldHeatingMode):
   try:
      r = session.get(url, verify=certFile)
      return r.json()['systemMode']
   except requests.exceptions.RequestException:
      print("Connection Error")
      return oldHeatingMode

def setHeatingMode(heatingMode):
   if heatingMode == 'On':
      GPIO.output(17, 1)
   elif heatingMode == 'Off':
      GPIO.output(17, 0)

def main():
    address = 'https://192.168.165.99:8000'
    serverCertFile = './certs/server_cert.pem'
    clientCertFile = './certs/client_cert.pem'
    clientKeyFile = './certs/client_key.pem'

    bus = SMBus(1)
    bmp280 = BMP280(i2c_dev=bus)

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    #ratio = (R1 + R2)/R2
    ratio = 2
    batteryReader = AnalogIn(ads, ADS.P2)
    panelReader = AnalogIn(ads, ADS.P3)

    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, cascaded=1)
    seg = sevensegment(device)

    heatingMode = 'Off'

    session = requests.Session()
    sessionEstablished = -1
    while True:
        temperature = bmp280.get_temperature()
        displayTemperature(seg, temperature, 1)
        battery = int(batteryReader.voltage * ratio * 1000)
        print(panelReader.voltage)
        panel = int((panelReader.voltage * 1000))
        if sessionEstablished != 0:
           sessionEstablished = authenticateToServer(session, address + '/login/', serverCertFile)
        else:
           sendData(session, address + '/update-data', serverCertFile, temperature, battery, panel)
           heatingMode = getHeatingMode(session, address + '/system-mode', serverCertFile, heatingMode)
           setHeatingMode(heatingMode)

if __name__ == '__main__':
    main()
