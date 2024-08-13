from machine import Pin, I2C, ADC, PWM
from PID import PID
from mqtt_client import MClient
from mqtt_client import DEVICE
import machine

try:
    client = MClient(DEVICE.LOADR)

    vret_pin = ADC(Pin(26))
    vout_pin = ADC(Pin(28))
    vin_pin = ADC(Pin(27))
    pwm = PWM(Pin(0))
    pwm.freq(100000)
    pwm_en = Pin(1, Pin.OUT)

    pid = PID(0.7, 15, 0, setpoint=0.35, scale='ms')

    count = 0
    pwm_out = 0
    pwm_ref = 0
    setpoint = 0.0
    delta = 0.05
    r_shunt = 1.02
    # power_req = 0.7
    def power_control(duty,power_req,power):
        if power <= power_req - 0.02:
            duty = saturate(duty + 10)
        elif power >= power_req + 0.02:
            duty = saturate(duty - 10)
        return duty
            
    def saturate(duty):
        if duty > 62500:
            duty = 62500
        if duty < 100:
            duty = 100
        return duty

    while True:
        power_req = client.get_power_req()
        power_req = min(power_req, 1)
        
        pwm_en.value(1)

        vin = 1.026*(12490/2490)*3.3*(vin_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        vout = 1.026*(12490/2490)*3.3*(vout_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        vret = 1*3.3*((vret_pin.read_u16()-350)/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        count = count + 1
        
        
        i_shunt = vret/r_shunt
        power = vout*i_shunt
        pwm_ref = pid(vret)
        pwm_ref = int(pwm_ref*65536)
        pwm_out = power_control(pwm_out, power_req,power) 
        pwm.duty_u16(pwm_out)

        
        
        if count > 500:
            print("Vin = {:.3f}".format(vin))
            print("Vout = {:.3f}".format(vout))
            print("Vret = {:.3f}".format(vret))
            print("Duty = {:.0f}".format(pwm_out))

            print("Output Power = {:.3f}".format(power))
            client.send_load_power(power)
            count = 0
            pid.setpoint = setpoint
except Exception as e:
    machine.reset()