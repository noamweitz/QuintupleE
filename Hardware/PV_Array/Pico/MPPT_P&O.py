from machine import Pin, I2C, ADC, PWM, Timer
import time, utime

# Set up some pin allocations for the Analogues and switches
va_pin = ADC(Pin(28))
vb_pin = ADC(Pin(26))
ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

# Some PWM settings, pin number, frequency, duty cycle limits and start with the PWM outputting the default of the min value.
pwm = PWM(Pin(9))
pwm.freq(100000)
min_pwm = 20000
max_pwm = 50000
pwm_out = min_pwm

# Basic signals to control logic flow
global timer_elapsed
timer_elapsed = 0
count = 0
first_run = 1

# Need to know the shunt resistance
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
    
    def __init__(self, sr, address, maxi):
        self.address = address
        self.shunt = sr
            
    def vshunt(self):
        # Read Shunt register 1, 2 bytes
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_SHUNTVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big')
        if reg_value > 2**15:  # negative
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
        #ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x01\x9F')  # PG = 1
        #ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x09\x9F')  # PG = /2
        ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x19\x9F')  # PG = /8
        ina_i2c.writeto_mem(self.address, self.REG_CALIBRATION, b'\x00\x00')


# Modify the step size dynamically based on the power difference
def adaptive_step_size(prev_power, output_power, step):
    power_diff = abs(output_power - prev_power)
    if power_diff < 0.05:  # threshold for small changes in power
        step = max(step // 2, 1)  # decrease step size, with a minimum of 1
    else:
        step = min(step * 2, 1000)  # increase step size, with a maximum of 1000
    return step


# Variables for MPPT
current_duty = min_pwm
prev_duty =  min_pwm
prev_power = 0
direction = 1
step = 1000

duty = int(65536 - max_pwm)
pwm.duty_u16(duty)
print(f"Initialising duty at: {duty}")
utime.sleep_ms(1000)


with open('/Data.csv', 'w') as file:
    file.write('Time,Power\n')  # Write the header row
    # Here we go, main function, always executes
    start_time = utime.ticks_ms()  # Get the start time in milliseconds
    # Here we go, main function, always executes
    while True:

        if first_run:
            # for first run, set up the INA link and the loop timer settings
            ina = ina219(SHUNT_OHMS, 64, 5)
            ina.configure()
            first_run = 0
            
            # This starts a 1kHz timer which we use to control the execution of the control loops and sampling
            loop_timer = Timer(mode=Timer.PERIODIC, freq=500, callback=tick)
        
        # If the timer has elapsed it will execute some functions, otherwise it skips everything and repeats until the timer elapses
        if timer_elapsed == 1:  # This is executed at 1kHz
            va = 1.017 * (12490 / 2490) * 3.3 * (va_pin.read_u16() / 65536)  # calibration factor * potential divider ratio * ref voltage * digital reading
            vb = 1.015 * (12490 / 2490) * 3.3 * (vb_pin.read_u16() / 65536)  # calibration factor * potential divider ratio * ref voltage * digital reading
            Vshunt = ina.vshunt()
            iL = Vshunt / SHUNT_OHMS

            # MPPT algorithm
            output_power = vb * iL  # Calculate output power (Va * iL)
            output_power = round(output_power, 5)
            prev_power = round(prev_power, 5)

            # Adjust the step size
            step = adaptive_step_size(prev_power, output_power, step)

            # Compare current power with previous power
            if output_power > prev_power:
                prev_power = output_power
                prev_duty = current_duty
                current_duty += step * direction
            else:
                direction *= -1  # Change the direction
                current_duty = prev_duty + step * direction
            
            # Ensure the duty cycle stays within bounds
            current_duty = saturate(current_duty, max_pwm, min_pwm)
            duty = 65536 - current_duty  # Invert because of hardware requirements
            pwm.duty_u16(duty)  # Set the PWM duty cycle
                
            # Reduces Oscillations in data (for low loads)
            utime.sleep_ms(25)
            
            # Keep a count of how many times we have executed and reset the timer so we can go back to waiting
            count = count + 1
            timer_elapsed = 0

            
            # This set of prints executes every 100 loops by default and can be used to output debug or extra info over USB enable or disable lines as needed
            if count > 20:
                elapsed_time = (utime.ticks_ms() - start_time)
                print(f"Time = {elapsed_time}s, Po = {output_power:.5f}")
                file.write(f"{elapsed_time:.2f},{output_power:.5f}\n")
                count = 0


