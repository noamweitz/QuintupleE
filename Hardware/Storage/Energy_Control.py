from machine import Pin, I2C, ADC, PWM, Timer
import time, utime

# Initialization
va_pin = ADC(Pin(28))
vb_pin = ADC(Pin(26))
ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

pwm = PWM(Pin(9))
pwm.freq(100000)
min_pwm = 9000
max_pwm = 43500
pwm_out = min_pwm

C = 0.25  # Capacitance in Farads
SHUNT_OHMS = 0.10

# PID Gains for different energy levels
low_energy_gains = {'kp': 10, 'ki': 10, 'kd': 10}
mid_energy_gains = {'kp': 20, 'ki': 10, 'kd': 20}
high_energy_gains = {'kp': 25, 'ki': 15, 'kd': 20}

# Control variables
v_err_int = 0
previous_v_err = 0

# Tolerance for error
tolerance = 0.15  # Reduced Tolerance
stability_threshold = 0.005  # Reduced Stability Threshold
stability_samples = 10
stability_wait_time = 150  # Reduced Stability Wait Time

# Saturate function
def saturate(signal, upper, lower): 
    return max(min(signal, upper), lower)

# INA219 Class
class ina219:
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
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_SHUNTVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big')
        if reg_value > 2**15:  # Negative
            sign = -1
            reg_value = (~reg_value & 0xFFFF) + 1
        else:
            sign = 1
        return float(reg_value) * 1e-5 * sign

    def vbus(self):
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_BUSVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big') >> 3
        return float(reg_value) * 0.004

    def configure(self):
        ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x19\x9F')
        ina_i2c.writeto_mem(self.address, self.REG_CALIBRATION, b'\x00\x00')

# Function to get user input for desired energy
def get_desired_energy():
    while True:
        try:
            E_desired = float(input("Enter the desired energy in Joules (between 6.4 and 31.4): "))
            if 6.4 <= E_desired <= 31.4:
                return E_desired
            else:
                print("Please enter a value between 6.4 and 31.4 Joules.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

# Function to wait until voltage stabilizes with averaging
def wait_for_stability():
    stable = False
    samples = []
    for _ in range(stability_samples):
        current_va = va_pin.read_u16() / 65536 * 3.3
        samples.append(current_va)
        utime.sleep_ms(stability_wait_time // stability_samples)
    avg_va = sum(samples) / len(samples)
    max_diff = max(abs(v - avg_va) for v in samples)
    if max_diff < stability_threshold:
        stable = True
    return stable

# Start with no energy stored (9000)
duty = int(9000)
pwm.duty_u16(duty)

wait_for_stability()

# Get initial desired energy
E_desired = 6.4

# Initialize the start time
start_time = utime.ticks_ms()

previous_input = None  # Variable to store the previous input

while True:
    va = 1.017 * (12490 / 2490) * 3.3 * (va_pin.read_u16() / 65536)  # Va calculation
    vb = 1.015 * (12490 / 2490) * 3.3 * (vb_pin.read_u16() / 65536)  # Vb calculation
    ina = ina219(0.1, 0x40)  # Initialize INA219 with address 0x40
    Vshunt = ina.vshunt()
    iL = -(Vshunt / SHUNT_OHMS)  # Invert the current sense for Boost

    # Calculate stored energy
    E_stored = round(0.5 * C * va**2 , 1)
    
    # Select PID gains and pwm_out calculation based on energy levels
    if 0 <= E_stored <= 20:
        kp_v = low_energy_gains['kp']
        ki_v = low_energy_gains['ki']
        kd_v = low_energy_gains['kd']
        pwm_multiplier = 1.045
    elif 20 < E_stored <= 27:
        kp_v = mid_energy_gains['kp']
        ki_v = mid_energy_gains['ki']
        kd_v = mid_energy_gains['kd']
        pwm_multiplier = 1.05
    elif 27 < E_stored <= 35:
        kp_v = high_energy_gains['kp']
        ki_v = high_energy_gains['ki']
        kd_v = high_energy_gains['kd']
        pwm_multiplier = 1.065
    else:
        continue  # Out of desired range, continue to the next loop iteration

    # Check if the stored energy is within tolerance of the desired energy
    if abs(E_stored - E_desired) < tolerance:
        v_err_int = 0  # Reset integral terms
        if wait_for_stability():  # Wait for voltage to stabilize
            output_power = va * iL
            current_time = utime.ticks_ms()
            elapsed_time = utime.ticks_diff(current_time, start_time)
            print(f"\nEnergy {E_stored:.2f}J reached the desired level {E_desired:.2f}J in {elapsed_time/1000} s")
            
            # Check for new desired energy input
            new_E_desired = get_desired_energy()
                        # Ignore new input if it's too close to the current or previous input
            while abs(new_E_desired - E_stored) < tolerance or (previous_input is not None and abs(new_E_desired - previous_input) < tolerance):
                print("New desired energy is too close to the current or previous value. \nPlease enter a different value.")
                new_E_desired = get_desired_energy()

            E_desired = new_E_desired
            previous_input = E_desired  # Update previous input
            start_time = utime.ticks_ms()  # Reset the start time

    else:
        # Energy Control (Outer Loop)
        V_ref = (2 * E_desired / C) ** 0.5
        v_err = V_ref - va
        v_err_int += v_err  # Integrate the voltage error
        v_err_der = v_err - previous_v_err  # Derivative of voltage error
        previous_v_err = v_err

        # Reference current
        I_ref = kp_v * v_err + ki_v * v_err_int + kd_v * v_err_der

        # Limit I_ref to ±0.35 A
        I_ref = saturate(I_ref, 0.35, -0.35)

        # Calculate PWM duty
        pwm_out = ((V_ref - vb) / V_ref * 64536) * pwm_multiplier
        pwm_out = saturate(pwm_out, max_pwm, min_pwm)
        duty = int(pwm_out)
        pwm.duty_u16(duty)

        # Calculate adaptive step size
        energy_diff = abs(E_stored - E_desired)
        adaptive_step = max(100, min(1000, int(energy_diff * 1000)))

        # Adjust PWM duty based on stability and energy difference
        if not wait_for_stability():
            duty += adaptive_step  # Increase duty if not stable
            pwm.duty_u16(duty)
        else:
            if E_stored > E_desired + tolerance:  # Check for overestimation
                duty -= adaptive_step  # Decrease duty if overestimated
                pwm.duty_u16(duty)
 
    # Print data in consistent format
    current_time = utime.ticks_ms()
    elapsed_time = utime.ticks_diff(current_time, start_time)
    print(f"E: {(E_stored):.1f} J, Duty: {duty/65536 * 100:.0f}, iL: {iL*1000} mA")

