from machine import Pin, I2C, ADC, PWM, Timer
import utime
from mqtt_client import MClient, DEVICE

utime.sleep(5)

client = MClient(DEVICE.PV_ARRAY)

# Initialization
vb_pin = ADC(Pin(26))
ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

pwm = PWM(Pin(9))
pwm.freq(100000)
min_pwm = 1000
max_pwm = 64536
pwm_out = min_pwm

# Constants
SHUNT_OHMS = 0.10
MPP = 2.8

# Initialize variables
irradiance = 100
power_sum = 0
sample_count = 0
P_desired = MPP

# Basic signals to control logic flow
global timer_elapsed
timer_elapsed = 0
count = 0
first_run = 1

# PID Gains
kp = 1000
ki = 5
kd = 0

# Control variables
v_err_int = 0
previous_v_err = 0
integral_min = -5000
integral_max = 5000

# Tolerance for error
stability_threshold = 0.005
stability_samples = 10
stability_wait_time = 150

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
        if reg_value > 2**15: #negative
            sign = -1
            for i in range(16): 
                reg_value = (reg_value ^ (1 << i))
        else:
            sign = 1
        return float(reg_value) * 1e-5 * sign
        
    def vbus(self):
        # Read Vbus voltage
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_BUSVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big') >> 3
        return float(reg_value) * 0.004
        
    def configure(self):
        ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x19\x9F') # PG = /8
        ina_i2c.writeto_mem(self.address, self.REG_CALIBRATION, b'\x00\x00')

# Function to saturate signal
def saturate(signal, upper, lower): 
    return max(min(signal, upper), lower)

# This is the function executed by the loop timer, it simply sets a flag which is used to control the main loop
def tick(t): 
    global timer_elapsed
    timer_elapsed = 1

# Function to get user input for desired power output
def get_irradiance():
    while True:
        try:
            Irradiance = float(input("Enter irradiance as %: "))
            if 0 <= Irradiance <= 100:  # Limiting the value of input to between 0 and 100
                return Irradiance
            else:
                print("Irradiance % is not valid")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

# PID Controller update
def update_pid(error):
    global v_err_int, previous_v_err
    v_err_int += error
    v_err_int = saturate(v_err_int, integral_max, integral_min)
    pid_output = kp * error + ki * v_err_int + kd * (error - previous_v_err)
    previous_v_err = error
    return pid_output

# Initial setup
duty = int(min_pwm)
duty = saturate(duty, max_pwm, min_pwm)
pwm.duty_u16(duty)

# Main loop
while True:
    if first_run:
        # For the first run, set up the INA link and the loop timer settings
        ina = ina219(SHUNT_OHMS, 64, 5)
        ina.configure()
        first_run = 0
        # This starts a 1kHz timer which we use to control the execution of the control loops and sampling
        loop_timer = Timer(mode=Timer.PERIODIC, freq=2000, callback=tick)        

    if timer_elapsed == 1:  # This is executed at 1kHz
        timer_elapsed = 0  # Reset the timer flag

        # Measure Vb and calculate iL
        vb = 1.015 * (12490 / 2490) * 3.3 * (vb_pin.read_u16() / 65536)  # Vb calculation
        Vshunt = ina.vshunt()
        iL = Vshunt / SHUNT_OHMS  # Current calculation
        
        # Calculate power output
        power_output = vb * iL

        # Calculate error between desired power and measured power output
        error = P_desired - power_output

        # Update PID controller
        pid_output = update_pid(error)

        # Adjust PWM duty cycle based on PID output
        pwm_out += int(pid_output)
        pwm_out = saturate(pwm_out, max_pwm, min_pwm)
        duty = int(65536-pwm_out) # Invert because reasons
        pwm.duty_u16(duty)

        # Accumulate power for averaging
        power_sum += power_output
        sample_count += 1

        count += 1

        # every 10s
        # Check for new desired power output input and print average power every 5 seconds
        if count >= 100:
            irradiance = client.get_irradiance()
            client.send_pv_power(power_output)
            
            P_desired = round ((irradiance * MPP) / 100, 2)
            power_sum = 0  # Reset power sum
            sample_count = 0  # Reset sample count
            count = 0


