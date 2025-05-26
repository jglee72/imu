# IMU Project
Intially intended for shipboard monitoring (Heave, Tilt, and Pitch) of offshore operations.  
## IMU Explained
IMU stands for Inertial Measurement Unit. It's an electronic device that measures and reports the specific force, angular rate, and sometimes orientation of a body. This is achieved through a combination of accelerometers and gyroscopes, and sometimes magnetometer

## IMU in a Box 
Constructed from a RPi module and an Adafruit Precision NXP 9-DOF. This is basically a version of Adafruit's FXOS8700 and their FXAS21002C
![image](https://github.com/user-attachments/assets/50a53884-9c1b-43cc-aa10-cc0c71fd478f)

Once placed on a network the IMU in a Box would broadcast UDP packages of all available data provided by the NXP chipset, and any other sensor available to the RPI.  An IOS Application was developed (via Pythonista Application) to read and parse this data and to display relavent data.
![IMG_7377](https://github.com/user-attachments/assets/7bb934f8-b376-45e3-83a4-8b0e995068d2)

## Where is it now
The original sole unit is owned by a client, although the project is full open sourced.  

## Potential IMU Future
The IMU in a box as a standalone piece of test equipment which can easily be mimiced by high-end and expensive IMU devices on the market. This was an exellent exercise in adapting a COTs 9-DOF projext board to any Raspberry Pi module, and likely to any microprocessor.  Extensive Research was also involved in the reading and interpreting of Inertia data from this complex chipset.  
