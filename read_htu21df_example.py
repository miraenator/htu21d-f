#!/usr/bin/env python

from __future__ import print_function

import BMP085
import HTU21DF
import math

from time import time, sleep
import sys
from smbus import SMBus


BUS_NO = 1
ADDR_HTU21 = 0x40 
ADDR_BMP085 = 0x77

bmp_mode = BMP085.BMP085_ULTRAHIGHRES
bmp = BMP085.BMP085(busnum=1, mode=bmp_mode)

htu = HTU21DF.HTU21DF(1, ADDR_HTU21)
htu.soft_reset()
htu.print_user_reg(htu.read_user_reg())

SEP=","
ALT_M = 335  #measured by GPS for BB, Prague 6
FNAME = "{}_bmp085_m{}_htu21df.csv".format(int(time()), bmp_mode)
with open(FNAME, 'a') as f:
  f.write("timestamp,bmp_tmp_c, pressure_pa, alt_m, sealevel_pressure_pa, htu_tmp_c, htu_rh_percent, partialpressure_mmHg, dewpoint_degC\n")
  while True:
    #BMP085
    f.write("{:.2f}{}".format(time(), SEP))
    f.write("{}{}".format(bmp.read_temperature(), SEP))
    f.write("{}{}".format(bmp.read_pressure(), SEP))
#    f.write("," + sensor.read_altitude().__str__())
    f.write("{}{}".format(ALT_M, SEP))
    f.write("{}{}".format(bmp.read_sealevel_pressure(altitude_m = ALT_M), SEP))

    #HTU21D-F
    t_c = htu.read_temp_degC()
    hum = htu.read_humidity_percent()
    f.write("{}{}".format(t_c, SEP))
    f.write("{}{}".format(hum, SEP))
      #Partial Pressure formula from Ambient Temperature
    A = 8.1332
    B = 1762.39
    C = 235.66
 
    PP_Tamb = math.pow(10, A - (B / (t_c + C)))
    #Dew point Temperature (Td) formula
    Td = -( (B / (math.log10(hum * t_c / 100.0) - A) ) + C )
    f.write("{}{}{}{}".format(PP_Tamb, SEP, Td, ""))

    f.write("\n")
    f.flush()
    sleep(2.5)
