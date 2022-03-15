#!/usr/bin/env python3
''' catch victron MPPT charge controler serial data
    measure battery temperature
    measure battery cell voltate
    control battery heater
    https://github.com/karioja/vedirect
'''
import serial, string
from datetime import datetime
import paho.mqtt.client as mqtt

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
}

def zerodta():
  dta['V'] = 0.0
  dta['I'] = 0.0
  dta['VPV'] = 0.0
  dta['PPV'] = 0.0
  dta['IL'] = 0.0


ser = serial.Serial('/dev/ttyUSB0',19200, 8, 'N', 1, timeout = 5)

output = " "
n = 60
s=0
while True:
  count = 0;
  sum_val = 0
  while output != "":
    boutput = ser.readline()
    #checksum on boutput till 'checksum
    for b in boutput:
      s =  (s + b ) % 256
    output =str(boutput)
    # b':'  whats that?
    #decode all the victron data
    l = output.split("\\t")
    if(len(l) == 2):
        key = l[0][2:]
        value = l[1][0:-5] 
        if key in dta:
          dta[key] += float(value);
        if key == "Checksum" :
            if(s != 0):
                print(key,value,s) #bad
                s=0
                continue
            else:
              s=0

#        print(l[0][2:],l[1][0:-5]) 
  #  print(pieces[1])
    
    if output.startswith("b'V\\") :
        val = float(int((str(output).split("\\t"))[1].split("\\")[0]))/1000
        sum_val = sum_val + val
        count += 1
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        if(count >=60):
            log_string = current_time + "," + str(round(sum_val/n,2)) +'\r\n'
            json = "{{\"V\": {0:.2f}}}".format(round(sum_val/n,2) )
            count=0
            # for k in dta:
            #   print(f'{k}:{dta[k]/60}')
            sum_val = 0
            json = "{{\"V\": {0:.2f},\"I\": {1:.2f},\"VPV\": {2:.2f},\"PPV\": {3:.2f},\"IL\": {4:.2f}}}".format(dta['V']/60/1000,dta['I']/60/1000,dta['VPV']/60/1000,dta['PPV']/60,dta['IL']/60/1000)
            client.publish("SolarPanel", json, qos=0, retain=False)
            zerodta()
        output = " "

