from machine import Pin, I2C, ADC, PWM, Timer
import time, utime
import math
from mqtt_client import MClient, DEVICE

client = MClient(DEVICE.STORAGE)


# Initialization
va_pin = ADC(Pin(28))
ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

pwm = PWM(Pin(9))
pwm.freq(100000)
min_pwm = 9000
max_pwm = 42300
pwm_out = min_pwm
duty = 0

C = 0.5  # Capacitance in Farads
SHUNT_OHMS = 0.10
max_capacity = 0.5 * C * 16 * 16
min_capacity = 0.5 * C * 7 * 7

# Basic signals to control logic flow
global timer_elapsed
timer_elapsed = 0
count = 0
first_run = 1

# PID Gains for different power ranges
pid_gains = {
    "0-1": {"kp": 50, "ki": 5, "kd": 10},	# Good enough
    "1-2": {"kp": 25, "ki": 5, "kd": 10},	# Test
    "2-3": {"kp": 10, "ki": 5, "kd": 10},	# Test
}


# Initial PID Gains
kp = pid_gains["0-1"]["kp"]
ki = pid_gains["0-1"]["ki"]
kd = pid_gains["0-1"]["kd"]

# Control variables
v_err_int = 0
previous_v_err = 0
integral_min = -5000  # Minimum integral value
integral_max = 5000   # Maximum integral value

# Saturate function
def saturate(signal, upper, lower): 
    return max(min(signal, upper), lower)

# This is the function executed by the loop timer, it simply sets a flag which is used to control the main loop
def tick(t): 
    global timer_elapsed
    timer_elapsed = 1

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

# Function to get user input for desired power output
def get_desired_power():
    while True:
        try:
            P_desired = float(input("Enter the desired power output in Watts: "))
            if abs(P_desired) <= 3:  # Limiting the absolute value of input to <= 4
                return P_desired
            else:
                print("Power output must be within +-3 Watts of the desired value.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

# Function to calculate State of Charge (SoC)
def calculate_soc(energy_stored):
    return min(100, max(0, (energy_stored - min_capacity) / (max_capacity - min_capacity) * 100))

# Function to update PID gains based on desired power
def update_pid_gains(P_desired):
    global kp, ki, kd
    if 0 <= abs(P_desired) <= 1:
        gains = pid_gains["0-1"]
    elif 1 < abs(P_desired) <= 2:
        gains = pid_gains["1-2"]
    elif 2 < abs(P_desired) <= 3:
        gains = pid_gains["2-3"]
    else:
        gains = pid_gains["0-1"]
    kp, ki, kd = gains["kp"], gains["ki"], gains["kd"]

def duty_from_voltage(voltage, min_pwm):
    # Coefficients of the quadratic equation
    a = 6e-9
    b = -3e-5
    c = 7.1367 - voltage
    
    # Threshold voltage below which we return 9000
    threshold_voltage = 7.3527
    
    if voltage < threshold_voltage:
        return min_pwm
    
    # Calculate the discriminant
    discriminant = b**2 - 4 * a * c
    
    if discriminant < 0:
        raise ValueError("The equation has no real roots.")
    
    # Calculate the two possible solutions for x (duty)
    sqrt_discriminant = math.sqrt(discriminant)
    x1 = (-b + sqrt_discriminant) / (2 * a)
    x2 = (-b - sqrt_discriminant) / (2 * a)
    
    # Return the valid solution
    if x1 >= 0:
        return x1
    else:
        return x2

# 1 second delay to let storage voltage stabilise
utime.sleep_ms(1000)

va = 1.017 * (12490 / 2490) * 3.3 * (va_pin.read_u16() / 65536)  # Va calculation
initial_voltage = va
print(f"Va: {va}")
initial_duty = duty_from_voltage(initial_voltage, min_pwm)  # Calculate initial duty cycle
print(f"Initial Duty: {initial_duty}")
duty = int(initial_duty)
pwm.duty_u16(duty)

### Test above

# Get initial desired power output
P_desired = get_desired_power()
update_pid_gains(P_desired)

# Initialize the start time
power_sum = 0
sample_count = 0
soc = 0

previous_input = None  # Variable to store the previous input

while True:
    if first_run:
        # for first run, set up the INA link and the loop timer settings
        ina = ina219(SHUNT_OHMS, 64, 5)
        ina.configure()
        first_run = 0
        # This starts a 1kHz timer which we use to control the execution of the control loops and sampling
        loop_timer = Timer(mode=Timer.PERIODIC, freq=1000, callback=tick)        
        
    if timer_elapsed == 1: # This is executed at 1kHz
        timer_elapsed = 0  # Reset the timer flag

        va = 1.017 * (12490 / 2490) * 3.3 * (va_pin.read_u16() / 65536)  # Va calculation
        Vshunt = ina.vshunt()
        iL = -(Vshunt / SHUNT_OHMS)  # Invert the current sense for Boost

        # Calculate stored energy
        E_stored = round(0.5 * C * va**2 , 1)
        
        # Calculate power output
        power_output = va * iL
        
        if P_desired == 0:
            if 5 <= soc < 50:
                P_desired = 0.05  # Leakage control for SoC between 5% and 50%
            elif 50 <= soc < 70:
                P_desired = 0.06  # Leakage control for SoC between 50% and 70%
            elif 70 <= soc < 80:
                P_desired = 0.065  # Leakage control for SoC between 50% and 70%
            elif soc >= 80:
                P_desired = 0.07  # Leakage control for SoC above 80%

        elif P_desired > 0:
            if soc >= 90:
                P_desired = 0.07  # Limit charging when SoC is 90% or higher

        elif P_desired < 0:
            if soc <= 5:
                P_desired = 0.05  # Limit discharging when SoC is 5% or lower
                
        # PID Control
        error = P_desired - power_output
        v_err_int += error  # Integrate the error
        v_err_int = saturate(v_err_int, integral_max, integral_min)  # Clamp the integral term
        v_err_deriv = error - previous_v_err  # Calculate the derivative of the error
        
        # Calculate the PID output
        pid_output = kp * error + ki * v_err_int + kd * v_err_deriv
        
        # Update the duty cycle
        duty += int(pid_output)
        duty = saturate(duty, max_pwm, min_pwm)

        # Update the previous error
        previous_v_err = error

        pwm.duty_u16(duty)
        utime.sleep_ms(5)
        

        # Calculate State of Charge (SoC)
        soc = calculate_soc(E_stored)
        
        # Accumulate power for averaging
        power_sum += power_output
        sample_count += 1
        
        # Keep a count of how many times we have executed and reset the timer so we can go back to waiting
        count = count + 1
        timer_elapsed = 0
        
        if count % 25 == 0:
            # Print data in consistent format
            print(f"SoC: {soc:.0f}")

        # Check for new desired power output input and print average power every 5 seconds
        if count >= 1000:
            average_power = power_sum / sample_count
            print(f"Average Power over last 5 seconds: {average_power:.2f} W")
            P_desired = client.get_desired_power()
            update_pid_gains(P_desired)  # Update PID gains based on new desired power
            power_sum = 0  # Reset power sum
            sample_count = 0  # Reset sample count
            count = 0

            client.send_storage_power(average_power)
            client.send_soc(soc)