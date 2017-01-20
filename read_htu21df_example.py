#!/usr/bin/env python

#Warning, not tested yet on real Raspberry Pi with sensor, but the HTU21DF class was tested
#Suppose no big modifications are needed

#let's pretend we are ready for Python 3
from __future__ import print_function

import HTU21DF
import math
import time

#For my Raspbery Pi B+ it is 1, read your docs
BUS_NO = 1

#For my device, the I2C address is 0x40
ADDR_HTU21 = 0x40 

#Initialize with bus_no and ADDR
htu = HTU21DF.HTU21DF(BUS_NO, ADDR_HTU21)

#Performing a soft reset (should reset the values in User register)
htu.soft_reset()

#Let's print some info about the sensor. 
#Loading into variable, so we do not have to use the I2C bus
user_reg = htu.read_user_reg()
htu.print_user_reg(user_reg)

#HTU21D-F reading temperature (a CRC check is performed, but on error, only message is printed!)
t_c = htu.read_temp_degC()  #in degree Celsius
#HTU21D-F reading humidity (a CRC is checked; on error, only message is printed!)
hum = htu.read_humidity_percent()  #in % (relative humidity)
print("Values reaad: Temp [degC]: {}, RH [%] {}".format(t_c, hum))

#We can perform compensation. Should be performed in range 0 to 80 degC
hum_c = htu.compensate_humidity_percent(hum, t_c)
#According to the sensor documentation we can compute partial Pressure (in mmHg) and Dew Point
PP_Tamb = htu.compute_partial_pressure_Pa(t_c)

 #Dew point Temperature (Td) formula
if t_c > 0 and t_c < 80:
  #use compensated humidity, if in correct range
  Td = htu.compute_dewpoint_degC(hum_c, t_c)
else:
  #use uncompensated humidity
  Td = htu.compute_dewpoint_degC(hum, t_c)

print("""HTU21D-F sensor:
        Temp [degCelsius]: {},
        Relative humidity [%]: {},
        Relative humidity compensated [%]: {},
        Partial pressure [Pa] {},
        Dew Point [degCelsius]: {},
        system timestamp: {}"""
        .format(t_c, hum, hum_c, PP_Tamb, Td, time.time()))
