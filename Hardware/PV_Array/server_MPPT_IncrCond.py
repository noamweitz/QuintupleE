from machine import Pin, I2C, ADC, PWM, Timer
import utime
from mqtt_client import MClient, DEVICE
import machine

try:
    client = MClient(DEVICE.PV_ARRAY)

    # Set up some pin allocations for the Analogues and switches
    va_pin = ADC(Pin(28))
    vb_pin = ADC(Pin(26))
    vpot_pin = ADC(Pin(27))

    # Set up the I2C for the INA219 chip for current sensing
    ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

    # Some PWM settings, pin number, frequency, duty cycle limits and start with the PWM outputting the default of the min value.
    pwm = PWM(Pin(9))
    pwm.freq(100000)
    min_pwm = 20000
    max_pwm = 55000
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


    # Implement a simple moving average filter
    class MovingAverageFilter:
        def __init__(self, size=5):
            self.size = size
            self.values = []

        def add_value(self, value):
            if len(self.values) >= self.size:
                self.values.pop(0)
            self.values.append(value)

        def get_average(self):
            return sum(self.values) / len(self.values) if self.values else 0

    # Adjust the delay dynamically based on the power difference
    def adaptive_delay(prev_power, output_power, base_delay):
        power_diff = abs(output_power - prev_power)
        if power_diff < 0.25:  # threshold for small changes in power
            delay = min(base_delay * 2, 100)  # increase delay, with a maximum of 100 ms
        else:
            delay = max(base_delay // 2, 10)  # decrease delay, with a minimum of 10 ms
        return delay

    # Adjust the step size dynamically based on the power difference
    def adaptive_step_size(prev_power, output_power, step):
        power_diff = abs(output_power - prev_power)
        if power_diff < 0.5:  # threshold for small changes in power
            step = max(step // 2, 10)  # decrease step size, with a minimum of 10
        else:
            step = min(step * 2, 1000)  # increase step size, with a maximum of 1000
        return step

    # Variables for Incremental Conductance
    prev_va = 0
    prev_iL = 0
    current_duty = min_pwm
    step = 1000

    duty = int(65536 - max_pwm)
    pwm.duty_u16(duty)
    print(f"Initialising duty at: {duty}")
    utime.sleep_ms(5000)

    prev_power = 0

    # Moving average filters
    va_filter = MovingAverageFilter(size=5)
    iL_filter = MovingAverageFilter(size=5)

    # Hysteresis band around MPP
    hysteresis_band = 0.05


    with open('/Data.csv', 'w') as file:
        file.write('Time,Power\n')  # Write the header row
        # Here we go, main function, always executes
        start_time = utime.ticks_ms()  # Get the start time in milliseconds
        
        while True:
            if first_run:
                # for first run, set up the INA link and the loop timer settings
                ina = ina219(SHUNT_OHMS, 64, 5)
                ina.configure()
                first_run = 0
                
                # This starts a 1kHz timer which we use to control the execution of the control loops and sampling
                loop_timer = Timer(mode=Timer.PERIODIC, freq=2000, callback=tick)
            
            # If the timer has elapsed it will execute some functions, otherwise it skips everything and repeats until the timer elapses
            if timer_elapsed == 1:  # This is executed at 1kHz
                va = 1.017 * (12490 / 2490) * 3.3 * (va_pin.read_u16() / 65536)  # calibration factor * potential divider ratio * ref voltage * digital reading
                vb = 1.015 * (12490 / 2490) * 3.3 * (vb_pin.read_u16() / 65536)  # calibration factor * potential divider ratio * ref voltage * digital reading
                Vshunt = ina.vshunt()
                iL = Vshunt / SHUNT_OHMS

                # Apply moving average filter
                va_filter.add_value(va)
                iL_filter.add_value(iL)
                va = va_filter.get_average()
                iL = iL_filter.get_average()

                # Incremental Conductance Algorithm
                delta_iL = iL - prev_iL
                delta_va = va - prev_va

                output_power = vb * iL  # Calculate output power (Va * iL)
                output_power = round(output_power, 5)
                prev_power = round(prev_power, 5)
                
                if delta_va != 0:
                    incremental_conductance = delta_iL / delta_va
                    instantaneous_conductance = -iL / va

                    incremental_conductance = round(incremental_conductance, 5)
                    instantaneous_conductance = round(instantaneous_conductance, 5)

                    if incremental_conductance == instantaneous_conductance:
                        # At MPP, no change needed
                        pass
                    elif incremental_conductance > instantaneous_conductance + hysteresis_band:
                        # To the left of MPP, increase voltage (decrease duty cycle)
                        current_duty -= step
                    elif incremental_conductance < instantaneous_conductance - hysteresis_band:
                        # To the right of MPP, decrease voltage (increase duty cycle)
                        current_duty += step
                
                # Adjust the step size
                step = adaptive_step_size(prev_power, output_power, step)
                
                # Ensure the duty cycle stays within bounds
                current_duty = saturate(current_duty, max_pwm, min_pwm)
                duty = int(65536 - current_duty)  # Invert because of hardware requirements
                pwm.duty_u16(duty)  # Set the PWM duty cycle
                
                # Update previous values for next iteration
                prev_va = va
                prev_iL = iL

                # Adjust the delay dynamically
                delay = adaptive_delay(prev_power, output_power, 10)
                utime.sleep_ms(delay)

                # Calculate output power
                output_power = vb * iL  # Calculate output power (Va * iL)

                # Keep a count of how many times we have executed and reset the timer so we can go back to waiting
                count += 1
                timer_elapsed = 0

                # This set of prints executes every 100 loops by default and can be used to output debug or extra info over USB enable or disable lines as needed
                if count > 1:
                    elapsed_time = (utime.ticks_ms() - start_time)
                    
                    print(f"Time = {elapsed_time}s, Po = {output_power:.5f}")
                    file.write(f"{elapsed_time:.2f},{output_power:.5f}\n")
                    count = 0
except Exception as e:
    machine.reset()