from machine import Pin, I2C, ADC, PWM, Timer
import time, utime

# Set up some pin allocations for the Analogues and switches
va_pin = ADC(Pin(28))
vb_pin = ADC(Pin(26))
vpot_pin = ADC(Pin(27))

# Set up the I2C for the INA219 chip for current sensing
ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

# Some PWM settings, pin number, frequency, duty cycle limits and start with the PWM outputting the default of the min value.
pwm = PWM(Pin(9))
pwm.freq(100000)
min_pwm = 9000
max_pwm = 42300
pwm_out = min_pwm

# The potentiometer is prone to noise so we are filtering the value using a moving average
v_pot_filt = [0] * 100
v_pot_index = 0

# Basic signals to control logic flow
global timer_elapsed
timer_elapsed = 0
count = 0
first_run = 1

# Need to know the shunt resistance to calculate the current
global SHUNT_OHMS
SHUNT_OHMS = 0.10

# saturation function for anything you want saturated within bounds
def saturate(signal, upper, lower):
    if signal > upper:
        signal = upper
    if signal < lower:
        signal = lower
    return signal

# This is the function executed by the loop timer, it simply sets a flag which is used to control the main loop
def tick(t):
    global timer_elapsed
    timer_elapsed = 1

# These functions relate to the configuring of and reading data from the INA219 Current sensor
class ina219:
    
    # Register Locations
    REG_CONFIG = 0x00
    REG_SHUNTVOLTAGE = 0x01
    REG_BUSVOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05
    
    def __init__(self, sr, address):
        self.address = address
        self.shunt = sr
            
    def vshunt(self):
        # Read Shunt register 1, 2 bytes
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_SHUNTVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big')
        if reg_value > 2**15: #negative
            sign = -1
            for i in range(16): 
                reg_value = (reg_value ^ (1 << i))
        else:
            sign = 1
        return (float(reg_value) * 1e-5 * sign)
        
    def vbus(self):
        # Read Vbus voltage
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_BUSVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big') >> 3
        return float(reg_value) * 0.004
        
    def configure(self):
        #ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x01\x9F') # PG = 1
        #ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x09\x9F') # PG = /2
        ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x19\x9F') # PG = /8
        ina_i2c.writeto_mem(self.address, self.REG_CALIBRATION, b'\x00\x00')


# Here we go, main function, always executes
while True:
    if first_run:
        # for first run, set up the INA link and the loop timer settings
        ina = ina219(SHUNT_OHMS, 64)
        ina.configure()
        first_run = 0
        
        # This starts a 1kHz timer which we use to control the execution of the control loops and sampling
        loop_timer = Timer(mode=Timer.PERIODIC, freq=1000, callback=tick)
    
    # If the timer has elapsed it will execute some functions, otherwise it skips everything and repeats until the timer elapses
    if timer_elapsed == 1: # This is executed at 1kHz
        va = 1.017*(12490/2490)*3.3*(va_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        vb = 1.015*(12490/2490)*3.3*(vb_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        
        vpot_in = 1.026*3.3*(vpot_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        v_pot_filt[v_pot_index] = vpot_in # Adds the new reading to our array of readings at the current index
        v_pot_index = v_pot_index + 1 # Moves the index of the buffer for next time
        if v_pot_index == 100: # Loops it round if it reaches the end
            v_pot_index = 0
        vpot = sum(v_pot_filt)/100 # Actual reading used is the average of the last 100 readings
        
        Vshunt = ina.vshunt()
        
        iL = -(Vshunt/SHUNT_OHMS) # Invert the current sense for Boost
        pwm_ref = saturate(int((vpot/3.3)*65536), max_pwm, min_pwm) # Set up the reference PWM from the pot
        
        # Boost-OL
        if iL > 1: # Current limiting function
            pwm_out = pwm_out - 100 # if there is too much current, knock down the duty cycle
        elif iL < 0.9: # A little hysteresis so it doesnt oscillate around the edge of current limit
            pwm_out = pwm_out + 100 # We are now below the current limit so bring the duty back up
            
        # Saturate the pwm and send it out (not inverted because boost)    
        pwm_out = saturate(pwm_out, pwm_ref, min_pwm)
        duty = int(pwm_out)
        pwm.duty_u16(duty)
        
        # Keep a count of how many times we have executed and reset the timer so we can go back to waiting
        count = count + 1
        timer_elapsed = 0
        
        utime.sleep_ms(20)
        
        # This set of prints executes every 100 loops by default and can be used to output debug or extra info over USB enable or disable lines as needed
        if count > 1:
            output_power = va * iL  # Calculate output power (Va * iL)
            
            print("Va = {:.3f} V".format(va))
            print("Vb = {:.3f} V".format(vb))
            print("Vpot = {:.3f} V".format(vpot))
            print("iL = {:.3f} A".format(iL))
            print("Output Power = {:.3f} W".format(output_power))
            print("duty = {:d}".format(duty))
            print(" ")

            count = 0
