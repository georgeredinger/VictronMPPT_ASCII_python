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
import paho.mqtt.client as mqtt
import time
import board
import adafruit_mcp9808
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from vedirect import Vedirect


average_count = 0


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


broker_address="192.168.1.113" 
client = mqtt.Client("SolarPanel")
client.connect(broker_address)

#string capture
dts = {
'V': 'na',
'I': 'na',
'VPV': 'na',
'PPV': 'na',
'CS': 'na',
'MPPT': 'na',
'ERR': 'na',
'LOAD' : 'na',
'IL': 'na',
'H19' : 'na',
'H20': 'na',
'H21': 'na',
'H22': 'na',
'H23': 'na',
'HSDS': 'na',
'Checksum': 'na',
'PID': 'na',
'FW': 'na',
'SER': 'na',
}

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

chaw = ""

# ser = serial.Serial('/dev/ttyUSB0',19200, 8, 'N', 1, timeout = 5)

# output = " "
# n = 60
# s=0
# while True:
#   count = 0;
#   sum_val = 0
#   while output != "":
#     boutput = ser.readline()
#     #checksum on boutput till 'checksum
#     for b in boutput:
#       s =  (s + b ) % 256
#     output =str(boutput)

#     # b':'  whats that?
#     #decode all the victron data
#     l = output.split("\\t")
#     if(len(l) == 2):
#         key = l[0][2:]
#         value = l[1][0:-5] 
#         chaw += key + '\t' + value  + '\r\n'
#         if key in dta:
#           dta[key] += float(value);
#         if key == "Checksum" :
#             if(s != 0):
#                 print((chaw))
#                 print("Bad",key,value,s) #bad
#                 chaw = ""
#                 s=0
#                 continue
#             else:
#          #     print((chaw))
#               chaw = ""
#               tempF = getTemperature()
#               dta['T'] += tempF  #temperature
#               voltage = analogIn()
#               dta['C0'] += voltage[0]  #cell 0
#               dta['C1'] += voltage[1]  #cell 1
#               dta['C2'] += voltage[2]  #cell 2
#               s=0

#     if output.startswith("b'V\\") :
#         val = float(int((str(output).split("\\t"))[1].split("\\")[0]))/1000
#         sum_val = sum_val + val
#         count += 1
#         now = datetime.now()
#         current_time = now.strftime("%H:%M:%S")

#         if(count >=60):
#             log_string = current_time + "," + str(round(sum_val/n,2)) +'\r\n'
#             json = "{{\"V\": {0:.2f}}}".format(round(sum_val/n,2) )
#             count=0
#             # for k in dta:
#             #   print(f'{k}:{dta[k]/60}')
#             sum_val = 0
#             c1 = dta['C1']/60 - dta['C0']/60
#             c2 = dta['C2']/60 - dta['C1']/60
#             json = "{{\"V\": {0:.2f},\"I\": {1:.2f},\"VPV\": {2:.2f},\"PPV\": {3:.2f},\"IL\": {4:.2f},\"T\": {5:.2f},\"C0\": {6:.2f},\"C1\": {7:.2f},\"C2\": {8:.2f}}}"\
#             .format(dta['V']/60/1000,dta['I']/60/1000,dta['VPV']/60/1000,dta['PPV']/60,dta['IL']/60/1000,dta['T']/60,dta['C0']/60,c1,c2)
#             client.publish("SolarPanel", json, qos=0, retain=False)
#             print(json)
#             zerodta()
#         output = " "



def crunch_data_callback(packet):
    global average_count
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
    if(average_count >=60):
      average_count = 0
      c1 = dta['C1']/60 - dta['C0']/60
      c2 = dta['C2']/60 - dta['C1']/60
    
      json = "{{\"V\": {0:.2f},\"I\": {1:.2f},\"VPV\": {2:.2f},\"PPV\": {3:.2f},\"IL\": {4:.2f},\"T\": {5:.2f},\"C0\": {6:.2f},\"C1\": {7:.2f},\"C2\": {8:.2f}}}"\
      .format(dta['V']/60/1000,dta['I']/60/1000,dta['VPV']/60/1000,dta['PPV']/60,dta['IL']/60/1000,dta['T']/60,dta['C0']/60,c1,c2)
      client.publish("SolarPanel", json, qos=0, retain=False)
      print(json)
      zerodta()


    
ve = Vedirect('/dev/ttyUSB0',60)
ve.read_data_callback(crunch_data_callback)
