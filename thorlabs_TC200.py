import serial

class Controller:
    '''
    Basic device adaptor for Thorlabs TC200 Temperature Controller.
    - More commands are available and have not been implemented.
    Test code runs and seems robust.
    '''
    def __init__(self,
                 which_port,
                 sensor,        # 'PTC100', 'PTC1000' or 'NTC10K'
                 tmax_C=50,     # set the max allowable temperature in Celsius
                 name='TC200',
                 verbose=True,
                 very_verbose=False):
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        if self.verbose: print("%s: opening..."%self.name, end='')
        try:
            self.port = serial.Serial(
                port=which_port, baudrate=115200, timeout=2)
        except serial.serialutil.SerialException:
            raise IOError(
                '%s: no connection on port %s'%(self.name, which_port))
        if self.verbose: print(" done.")
        assert self._get_identity() == 'THORLABS TC200 VERSION 2.0'
        self._set_sensor(sensor)
        self._set_mode('normal') # 'cycle' mode cmd's not implemented
        self._set_tmax(tmax_C)
        self._get_enable_status()
        self.get_tactual()

    def _get_commands(self):
        cmd = b'commands?\r'
        if self.verbose: print('%s: sending cmd ='%self.name, cmd)
        self.port.write(cmd)
        commands = self.port.readline().decode('ascii').split('\r')
        if self.verbose:
            print('%s: commands list:'%self.name)
            for command in commands:
                print('%s: %s'%(self.name, command))
        return commands

    def _get_config(self):
        cmd = b'config?\r'
        if self.verbose: print('%s: sending cmd ='%self.name, cmd)
        self.port.write(cmd)
        configs = self.port.readline().decode('ascii').split('\r')
        if self.verbose:
            print('%s: config list:'%self.name)
            for config in configs:
                print('%s: %s'%(self.name, config))
        return configs

    def _send(self, cmd, query=True):
        cmd = cmd + b'\r'
        if self.very_verbose: print('%s: sending cmd ='%self.name, cmd)
        self.port.write(cmd)
        echo = self.port.read_until(b'\r')
        if self.very_verbose: print('%s: -> echo = '%self.name, echo)
        response = None
        if query:
            response = self.port.read_until(b'\r')
            if self.very_verbose:
                print('%s: -> response = '%self.name, response)
            response = response.decode('ascii').strip()
        trailing_bytes = self.port.read(2)
        if trailing_bytes == b'> ':
            pass # remove trailing '> ' and continue
        else:
            error = trailing_bytes + self.port.readline()
            if cmd == b'mode=normal\r': # avoid spurious error from 'normal'
                self.port.read(3) # remove trailing '>  ' and continue
            else:
                print('%s: -> error = '%self.name, error)
                raise Exception('***Controller Error***')
        return response

    def _get_identity(self):
        if self.verbose:
            print('%s: getting identity'%self.name)
        cmd = b'id?'
        self.identity = self._send(cmd)
        if self.verbose:
            print('%s: -> identity = %s'%(self.name, self.identity))
        return self.identity

    def _get_enable_status(self):
        if self.very_verbose: print('%s: getting enable status'%self.name)
        cmd = b'stat?\r'
        self.port.write(cmd)
        echo = self.port.read_until(b'\r')
        if self.very_verbose: print('%s: -> echo = '%self.name, echo)
        status_bytes = self.port.read_until(b' > ')[:2] # remove b' > '
        # these bit masks are not documented and were found via testing...
        self.sensor_alarm = bool(status_bytes[0] & 0b00000100)
        self.enabled = bool(status_bytes[1] & 0b00000001)
        if self.very_verbose:
            print('%s: -> sensor_alarm = %s'%(self.name, self.sensor_alarm))
            print('%s: -> enabled = %s'%(self.name, self.enabled))
        assert not self.sensor_alarm, '***Controller Error -> sensor alarm***'
        return self.enabled

    def _get_sensor(self):
        if self.verbose:
            print('%s: getting sensor'%self.name)
        cmd = b'sns?'
        self.sensor = self._send(cmd).split(' = ')[1].split(',')[0]
        if self.verbose:
            print('%s: -> sensor = %s'%(self.name, self.sensor))
        return self.sensor

    def _set_sensor(self, sensor):
        if self.verbose:
            print('%s: setting sensor = %s'%(self.name, sensor))
        assert sensor in ('PTC100', 'PTC1000', 'NTC10K')
        cmd = b'sns=' + bytes(sensor.lower(), 'ascii')
        if sensor in ('PTC100', 'PTC1000'):
            self._send(cmd, query=False)
        if sensor == 'NTC10K':
            self._send(cmd, query=True)
        assert self._get_sensor() == sensor
        if self.verbose:
            print('%s: done setting sensor'%self.name)
        return None

    def _set_mode(self, mode):
        if self.verbose:
            print('%s: setting mode = %s'%(self.name, mode))
        assert mode in ('normal', 'cycle')
        cmd = b'mode=' + bytes(mode, 'ascii')
        self._send(cmd, query=False)
        if self.verbose:
            print('%s: done setting mode'%self.name)
        return None

    def _get_tmax(self):
        if self.verbose:
            print('%s: getting max temperature'%self.name)
        cmd = b'tmax?'
        self.tmax_C = float(self._send(cmd))
        if self.verbose:
            print('%s: -> tmax_C = %s'%(self.name, self.tmax_C))
        return self.tmax_C

    def _set_tmax(self, tmax_C): # tested 20 <= tmax_C <= 205 in steps of 0.1
        if self.verbose:
            print('%s: setting max temperature (C) = %s'%(self.name, tmax_C))
        assert isinstance(tmax_C, int) or isinstance(tmax_C, float)
        assert 20 <= tmax_C <= 205
        tmax_C = round(tmax_C, 1) # 1.d.p for controller
        cmd = b'tmax=%f'%tmax_C
        self._send(cmd, query=False)
        assert self._get_tmax() == tmax_C
        if self.verbose:
            print('%s: done setting max temperature'%self.name)
        return None

    def get_tactual(self):
        if self.verbose:
            print('%s: getting actual temperature'%self.name)
        cmd = b'tact?'
        self.tact_C = float(self._send(cmd).split(' ')[0])
        if self.verbose:
            print('%s: -> tact_C = %s'%(self.name, self.tact_C))
        return self.tact_C

    def get_tset(self):
        if self.verbose:
            print('%s: getting set temperature'%self.name)
        cmd = b'tset?'
        self.tset_C = float(self._send(cmd).split(' ')[0])
        if self.verbose:
            print('%s: -> tset_C = %s'%(self.name, self.tset_C))
        return self.tset_C

    def set_tset(self, tset_C): # tested 20 <= tmax_C <= 205 in steps of 0.1
        if self.verbose:
            print('%s: setting set temperature (C) = %s'%(self.name, tset_C))
        assert isinstance(tset_C, int) or isinstance(tset_C, float)
        assert 20 <= tset_C <= self.tmax_C
        tset_C = round(tset_C, 1) # 1.d.p for controller
        cmd = b'tset=%f'%tset_C
        self._send(cmd, query=False)
        assert self.get_tset() == tset_C
        if self.verbose:
            print('%s: done setting set temperature'%self.name)
        return None

    def set_enable(self, enable):
        if self.verbose:
            print('%s: setting enable = %s'%(self.name, enable))
        assert enable in (True, False)
        if self._get_enable_status() == enable:
            return None
        else: # toggle enable
            cmd = b'ens'
            self._send(cmd, query=False)
        if self.verbose:
            print('%s: done setting enable'%self.name)
        return None

    def reached_temp(self, ttol_C=0.1): # ttol_C = temperature tolerance (C)
        self.reached_tset = False
        self.get_tactual()
        if self.tset_C - ttol_C <= self.tact_C <= self.tset_C + ttol_C:
            self.reached_tset = True
        if self.verbose:
            print('%s: -> tset_C = %s'%(self.name, self.tset_C))
            print('%s: -> reached_tset = %s'%(self.name, self.reached_tset))
        return self.reached_tset

    def close(self):
        if self.verbose: print("%s: closing..."%self.name, end='')
        self.port.close()
        if self.verbose: print("done.")
        return None

if __name__ == '__main__':
    import time
    temp_controller = Controller(
        'COM19', sensor='NTC10K', verbose=True, very_verbose=False)

##    temp_controller._get_commands()
##    temp_controller._get_config()

    print('\n# Set temperature and enable:')
    temp_controller.set_tset(22)
    temp_controller.set_enable(True)
    print('\n# Check if temperature reached:')
    temp_controller.reached_temp()
    print('\n# Controller should be ''DISABLED'' after ~1 second')
    time.sleep(1)
    temp_controller.set_enable(False)

##    print('\n# Set temperature, enable and block until reached temperature:')
##    temp_controller.set_tset(24)
##    temp_controller.set_enable(True)
##    while True: # this can block forever if the temperature can't be reached...
##        if temp_controller.reached_temp():
##            break
##        print(' -> waiting to reach temperature (%sC)'%temp_controller.tset_C)
##        time.sleep(1)
##    temp_controller.set_enable(False)

    temp_controller.close()
