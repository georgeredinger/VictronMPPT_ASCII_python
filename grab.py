import serial, string
from datetime import datetime

# Read & print/write data
ser = serial.Serial('/dev/ttyUSB0',19200, 8, 'N', 1, timeout = 5)
# Open ve_direct.csv
#file_data = open('ve_data.csv', 'w')
print( "Reading data and writing to ve_data.csv")
# Listen for the input, exit if nothing received in timeout period
output = " "
while True:
  while output != "":
    output =str(ser.readline())
#    file_data.write(output)
    if output.startswith("b'V\\") :
        val = float(int((str(output).split("\\t"))[1].split("\\")[0]))/1000
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        print(current_time, output,val,"\r",end='')
  output = " "

# Close file
print( "Stopped writing to ve_data.csv")
#file_data.close()
