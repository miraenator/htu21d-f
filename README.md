# htu21d-f
Python library for reading HTU21D-F humidity and temperature sensor via i2c.

**Warning**: The code is not really tested yet. Use on your own responsibility.

This is a pet project as I could not find a working Python library for my RPi easily. 
The code is inspired by the Arduino library: https://github.com/adafruit/Adafruit_HTU21DF_Library

Check also the datasheet: https://cdn-shop.adafruit.com/datasheets/1899_HTU21D.pdf

The relative humidity (RH) compensation is not applied automatically. However, the function is available. The compensation should be performed in the temp range (0 to 80 deg C):

`RH_compensated = RHmeasured + (25 - Tmeasured) * CoeffTemp`

Where `CoeffTemp = -0.15 [%RH/degC]`

## API outline
### Constructor
| Name | Description |
| --- | --- |
| `HTU21DF(bus_no, addr)` | constructor. Needs i2c bus address and i2c address of the sensor | 

### Basic functions
| Name | Description |
| --- | --- |
| `.soft_reset()` | performs soft reset (resets user register to default values) |
| `.read_user_reg()` | reads user register (returns 1 byte) |
| `.print_user_reg(register)` | prints debug info about the user register |
| `.read_temp_degC()` | performs temperature read, returns value in degrees Celsius |
| `.read_humidity_percent()` | performs relative humidity read, returns value in percent |

### Additional computations
| Name | Description |
| --- | --- |
| `.compensate_humidity_percent(humidity, temperature)` | performs humidity compensation computation based on humidity mesaured and temperature measured. Returns value in percent |
| `.compute_partial_pressure_mmHg(temp)` | computes partial pressure from ambient temperature. Returns value in mmHg |
| `.compute_partial_pressure_Pa(temp)` | computes partial pressure from ambient temperature. Returns value in Pascasl |
| `.compute_dewpoint_degC(humidity, temperature)` | computes dewpoint from humidity and temperature. Returns value in degrees Celsius |
| `.computeCRC(data)` | computes CRC. Used for verification of the measurements |

## Example code
```python
import HT21DF

#Bus 1, i2c addr: 0x40. Works for me.
htu = HTU21DF.HTU21DF(1, 0x40)

htu.soft_reset()

print("Temp [degC]: {}".format(htu.read_temp_degC()))
print("Rel. humidity [%]: {}".format(htu.read_humidity_percent()))
```
## Installation (Raspbian (Debian Jessie, maybe Ubuntu))
```bash
#Under root
sudo apt-get install python python-smbus
sudo apt-get install git

#clone the repository
git clone 'https://github.com/bursam/htu21d-f.git'

#Change to the directory and run the example
cd htu21d-f
python read_htu21df_example.py

#alternatively, you can set the execution permission
chmod u+x ./read_htu21df_example.py
#and from then you can run it as an executable file
./read_htu21df_example.py
```
