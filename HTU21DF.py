#Class for reading I2C sensor HTU21D-F (Humidity, Temperature). Created for Raspbery Pi B+

from smbus import SMBus
import logging
import time
import math

# Default HTU21D-F sensor I2C address
HTU21DF_I2CADDR = 0x40

#=== User register info ===
#Measurement resolution
#From bit 7 and bit 0 from the User register; default: 00
#b7  b0     RH     Temp
# 0   0    12 bit  14 bit
# 0   1     8 bit  12 bit
# 1   0    10 bit  13 bit
# 1   1    11 bit  11 bit

#Disable OTP reload (if active, i.e. 0, loads default settings after each time a measurement cmd is issued)
#bit 1 of User register; default 1

#Batery status (end of batt)
#bit 6 of the User register; default 0; '1' means VDD < 2.25 V, '0' VDD > 2.25 (may vary by +- 0.1 V)

#Reserved
#bits 3, 4, 5: Do not change; Must be preserved on registry write. I.e. read first, change bits and write back

#On-chip heater
#bit 2 of the User reg.: For functional diagnosis: relative hum drops upon rising remp; Consumes bout 5.5 mW, provdes tmp increase of about 0.5 to 1.5 deg Celsius

#Commands
HTU21DF_READTEMPCMD    = 0xE3
HTU21DF_READHUMCMD     = 0xE5
HTU21DF_READUSERREGCMD = 0xE7
HTU21DF_SOFTRESETCMD   = 0xFE

#HTU21DF_WRITEUSERREGCMD = 0xE6
#No_hold master versions of the measurement cmds: can be used for polling. First, trigger measurement, than poll i2c bus for results
#HTU21DF_READTEMPCMD_NO_HOLD = 0xF3
#HTU21DF_READHUMCMD_NO_HOLD = 0xF5

#Constants for computation Partial pressure and dewpoint
A = 8.1332
B = 1762.39
C = 235.66

class HTU21DF(object):

  def __init__(self, bus_no, address=HTU21DF_I2CADDR, **kwargs):
    """ Constructor(I2C_bus_number [, i2c_address]
      Creates a I2C bus object (smbus.SMBus)"""
    self._log = logging.getLogger('HTU21D-F i2c sensor')
    self._bus = SMBus(bus_no)
    self._address = address

  def soft_reset(self):
    """ Performs a soft reset of the device.
      Resets the user register to default values."""
    self._bus.write_byte(self._address, HTU21DF_SOFTRESETCMD)
    time.sleep(0.015)

  def read_user_reg(self):
    """ Returns (reads) the user register. 
    In case of writing back, make sure you preserved the reserved bits"""
    self._bus.write_byte(self._address, HTU21DF_READUSERREGCMD)
    return self._bus.read_byte(self._address)

  def print_user_reg(self, reg):
    """ Prints out debug info about the user register.
        Argument (byte): user register value"""
    resolution         = reg & 0b10000001
    otp_reload_disable = reg & 0b00000010
    heater_enable      = reg & 0b00000100
    reserved_bits      = reg & 0b00111000
    end_of_batt_status = reg & 0b01000000
    
    if resolution == 0x00:
      (rh, rt) = (12, 14)
    elif resolution == 0x01:
      (rh, rt) = (8, 12)
    elif resolution == 0x80:
      (rh, rt) = (10, 13)
    elif resolution == 0x81:
      (rh, rt) = (11, 11)
    else:
      self._log.error("Incorrect resolution value: {}, userReg: {}".format(hex(resolution), hex(reg)))
    
    if otp_reload_disable == 0x00:
      otp_d = False
    elif otp_reload_disable == 0x02:
      otp_d = True
    else:
      self._log.error("Incorrect otp_reload_value: {}, userReg: {}".format(hex(otp_reload_disable), hex(reg)))

    if end_of_batt_status == 0x00:
      end_batt = False
    elif end_of_batt_status == 0x40:
      end_batt = True
    else:
      self._log.error("Incorrect end_of_batt_status_value: {}, userReg: {}".format(hex(end_of_batt_status), hex(reg)))

    if heater_enable == 0x00:
      heat_en = False
    elif heater_enable == 0x04:
      heat_en = True
    else:
      self._log.error("Incorrect heater_enable_value: {}, userReg: {}".format(hex(heater_enable), hex(reg)))
    
    print("User_reg: {}, User_reg: {}, Resolution_temp: {}, Resolution_humidity: {}, otp_disable: {}, heater_enable: {}, reserved_bits: {}, end_of_batt_status: {}".format(hex(reg), bin(reg), rh, rt, otp_d, heat_en, bin(reserved_bits >>3), end_batt))

  def read_temp_degC(self, **kwargs):
    """Perform a temperature read. MSB, LSB and a CRC is read via I2C bus.
     A CRC is checked, but even in case of error, the valu is returned. Only 
     an error message is printed.
     Returns: temperature in degree Celsius"""
   
    tr = self._bus.read_i2c_block_data(self._address, HTU21DF_READTEMPCMD, 3)
    #reads MSB, LSB, CRC8 bytes (3x8 bit)
    #warning: LSB  last two bits are status bits: b0: not assigned, b1: 0=temperature meas, 1 = hum meas
    #    before converting to physical values, these must be set to '00'
    self._log.debug("Temp measurement bytes (raw): {}".format(tr))
    tv = tr[0] * 256 + (tr[1] & 0xFC)
    crc8 = tr[2]
    verify_crc = self.computeCRC((tr[0], tr[1]))
    if (crc8 != verify_crc):
      self._log.error("Temperature CRC error: got: {}, computed: {}, data: {}"
                      .format(hex(crc8), hex(verify_crc), tr))
    return float(tv) * 175.72 / 65536.0 - 46.85

  def read_humidity_percent(self):
    """ Performs a (relative) humidity value read. MSB, LSB and a CRC is read via I2C bus.
      A CRC is checked, but in case of error only error message is printed, but the (incorrect)
      value is returned.
      "Warning: The value is not compensated.
      Returns: relative humidity in percent"""
    hr = self._bus.read_i2c_block_data(self._address, HTU21DF_READHUMCMD, 3)
    #reads MSB, LSB, CRC8 bytes (3x8 bit)
    #warning: LSB  last two bits are status bits: b0: not assigned, b1: 0=tempaerature meas, 1 = hum meas
    #    before converting to physical values, these must be set to '00'
    self._log.debug("Humidity measurement bytes (raw): {}".format(hr))
    hv = hr[0] * 256 + (hr[1] & 0xFC)
    crc8 = hr[2]
    verify_crc = self.computeCRC((hr[0], hr[1]))
    if (crc8 != verify_crc):
      self._log.error("Humidity CRC error: got: {}, computed: {}, data: {}"
                      .format(hex(crc8), hex(verify_crc), hr))
    return float(hv) * 125.00 / 65536.0 - 6.0

  def compensate_humidity_percent(self, hum, temp):
    """Performs relative humidity compensation computation according to the datasheet.
     Warning: The compensation temperature range is 0 to 80 degrees Celsius
     Args: measured_humidity (percent), temperature (degrees Celsius)
     Returns: compensated_relative_humidity (percent)"""
    if temp < 0 or temp > 80:
      self._log.error("Temperature out of range 0 to 80 degC for compensation: {}".format(temp))
    return hum + (25.0 - temp) * (-0.15)

  def compute_partial_pressure_mmHg(self, temp):
    """Computes partial pressure in mmHg.
       Args: temperature (deg Celsius)
       Returns: partial_pressure (mmHg)"""
    return math.pow(10, A - (B / (temp + C)))

  def compute_partial_pressure_Pa(self, temp):
    """Computes partial pressure in Pascals.
       Args: temperature (deg Celsius)
       Returns: partial_pressure (Pascal)"""
    return 133.32239 * self.compute_partial_pressure_mmHg(temp)

  def compute_dewpoint_degC(self, hum, temp):
    """Computes dew point in degrees Celsius.
       Args: relative_humidity (percent), (temperature (deg Celsius)
       Returns: dewpoint (degrees Celsius)"""
    pp = self.compute_partial_pressure_mmHg(temp)
    return - ((B / (math.log10(hum * pp / 100.0) - A)) + C)

  def computeCRC(self, data, CRClen=8, D=int('0b100110001', 2)):
    """Computes CRC. Tested only for CRClen=8, D=0x131.
     Args: (MSB, LSB)
     Returns: Computed CRC"""
   
    DLen = D.bit_length()

    if isinstance(data, int):
      if data == 0:
        return D & 0xFF
      else:
        b = data
    else:
      b = data[0]
      for l in range(1, len(data)):
        b = b << 8
        b = b + data[l]
        # make space for the resulting CRC(8)
    b = b << CRClen

    # shift the divider to the left
    dtmp = D << (b.bit_length() - D.bit_length())
    if dtmp.bit_length() != b.bit_length():
      self._log.error("Error: lengths differ: divlen {}, veclen{}".format(dtmp.bit_length(), b.bit_length()))

    c = b.bit_length()
    i = b
    while True:
      # compute XOR
      i = i ^ dtmp

      # remove leftmost bit of the vector i: not needed, as the XOR operation with key did it for us
      # we have to shift:
      delta = c - i.bit_length()
      self._log.debug("Shifting right by: {}".format(delta))

      c -= delta
      if c <= CRClen:
        return i
      dtmp >>= delta
