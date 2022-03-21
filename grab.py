#!/usr/bin/env python3
''' catch victron MPPT charge controler serial data
    measure battery temperature
    measure battery cell voltate
    control battery heater
    https://github.com/karioja/vedirect
'''
import logging
from re import A
import serial, string
from datetime import datetime
import paho.mqtt.client as paho
import time
import board
import adafruit_mcp9808
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from vedirect import Vedirect

publishMinute = set([0,5,10,15,20,25,30,35,40,45,50,55])
#publishMinute = set([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59])
average_count = 0
last_minute = 0

logging.basicConfig(filename='victron.log', encoding='utf-8', level=logging.DEBUG)


i2c = board.I2C()  # uses board.SCL and board.SDA

# To initialise using the default address:
mcp = adafruit_mcp9808.MCP9808(i2c)

#i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)
ads.gain = 0.6666666666666666

v0Last = 0.0
v1Last = 0.0
v2Last = 0.0
v3Last = 0.0 
tLast = 0.0

def analogIn():
  global v0Last, v1Last, v2Last, v3Last
  scale0 = (1/0.18)*1.065
  scale1 = (1/0.18)*1.0579
  scale2 = (1/0.18)*1.0507
  scale3 = 1/0.18
  
  try:
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    chan2 = AnalogIn(ads, ADS.P2)
    chan3 = AnalogIn(ads, ADS.P3)
  except Exception as e:
    logging.debug(e)
    return(v0Last,v1Last,v2Last,v3Last)
  else:
    v0=round(chan0.voltage * scale0,2)
    v1=round(chan1.voltage * scale1,2)
    v2=round(chan2.voltage * scale2,2)
    v3=round(chan3.voltage * scale3,2)
    v0Last = v0
    v1Last = v1
    v2Last = v2
    v3Last = v3  
    return [v0,v1,v2,v3]


def getTemperature():
  global tLast
  try:
    temp = mcp.temperature
    temp = temp * 9 / 5 + 32
    tLast = temp
    return temp
  except Exception as e:
    logging.debug(e)
  else:
    return tLast

def on_publish(client, userdata, result):
    logging.debug("data published {}".format(result))

broker_address="192.168.1.113" 
port=1883

client = paho.Client("SolarPanel",protocol=paho.MQTTv311)
client.on_publish = on_publish
client.connect(broker_address,port)


#average
dta = {
'V': 0.0,
'I': 0.0,
'VPV': 0.0,
'PPV': 0.0,
'IL': 0.0,
'T': 0.0,
'C0': 0.0,#Cell0
'C1': 0.0,#Cell1
'C2': 0.0,#Cell2
}

def zerodta():
  dta['V'] = 0.0
  dta['I'] = 0.0
  dta['VPV'] = 0.0
  dta['PPV'] = 0.0
  dta['IL'] = 0.0
  dta['T'] = 0.0
  dta['C0'] = 0.0
  dta['C1'] = 0.0
  dta['C2'] = 0.0



def crunch_data_callback(packet):
    global average_count
    global last_minute
    global client
    dta['V'] += float(packet['V']);
    dta['I'] += float(packet['I']);
    dta['VPV'] += float(packet['VPV']);
    dta['PPV'] += float(packet['PPV']);
    dta['IL'] += float(packet['IL']);
    dta['T'] += getTemperature()
    c = analogIn()
    dta['C0'] += float(c[0]);
    dta['C1'] += float(c[1]);
    dta['C2'] += float(c[2]);
    average_count +=1
    minute = datetime.now().minute
    if((minute in publishMinute) and (minute != last_minute ) ):

      last_minute = minute #ensure we don't publish twice in a minute
      c1 = dta['C1']/average_count - dta['C0']/average_count
      c2 = dta['C2']/average_count - dta['C1']/average_count
    
      json = "{{\"V\": {0:.2f},\"I\": {1:.2f},\"VPV\": {2:.2f},\"PPV\": {3:.2f},\"IL\": {4:.2f},\"T\": {5:.2f},\"C0\": {6:.2f},\"C1\": {7:.2f},\"C2\": {8:.2f}}}"\
      .format(dta['V']/average_count/1000,dta['I']/average_count/1000,dta['VPV']/average_count/1000,dta['PPV']/average_count,dta['IL']/average_count/1000,dta['T']/average_count,dta['C0']/average_count,c1,c2)
      countStash = average_count
      average_count = 0
      now = datetime.now().isoformat()
      print("{},{},{}".format(now,countStash,json))
      logging.debug("{},{},{}".format(now,countStash,json))

      client.publish("SolarPanel", json, qos=1, retain=True)
     
      zerodta()


    
ve = Vedirect('/dev/ttyUSB0',60)
ve.read_data_callback(crunch_data_callback)