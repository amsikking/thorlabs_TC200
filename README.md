# thorlabs_TC200
Python device adaptor: Thorlabs TC200 temperature controller.
- Tested here with a TLK-H flexible foil heater and a SM1L10H heated lens tube (both have an integrated NTC thermister).
## Quick start:
- Download the Thorlabs GUI and run/check the controller/heater/thermister (a version included here "TC200_Setup_1.6.0.zip"). The GUI install should provide the correct USB driver. 
- Run the test script in 'thorlabs_TC200.py' to control the heater with Python. Make sure to configure the controller with the correct thermister type (NCT or PTC), and set a safe max temperature (tmax_C).
- Datasheets for example heaters/thermisters are included for convenience (TLK-H flexible foil heater, SM1L10H heated lens tube and TH100PT temperature sensor).
