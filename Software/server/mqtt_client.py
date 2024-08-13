import paho.mqtt.client as paho
import json
from models import FullTick, Day, Tick

# all the picos you can connect to
# sent a message to the pico using the PICO_TOPIC
# then in the message body, send the device in the target
# this is used in hardware as well
class Device:
    STORAGE = "storage"
    EXTERNAL_GRID = "external-grid"
    PV_ARRAY = "pv-array"
    LOADR="loadR"
    LOADY="loadY"
    LOADB="loadB"
    LOADK="loadK"

PICO_TOPIC = "pico"
SERVER_TOPIC = "server"
UI_TOPIC = "ui"

OVERRIDE_TARGET = "override"

class MClient:
    def __init__(self, broker_addr="35.178.119.19", broker_port=1883):
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2)
        self.client.on_connect = handle_connect
        self.client.on_message = self.handle_msg
        self.db_data = {}
        self.manual = False

        if self.client.connect(broker_addr, broker_port, keepalive=1000) != 0:
            raise Exception("Failed to connect to Broker")
        else:
            self.client.loop_start()

    def send_sun_data(self, sun_val):
        self.client.publish(self._get_pico_topic(Device.PV_ARRAY), json.dumps({"target": Device.PV_ARRAY , "payload": sun_val}), 2)

    # def send_external_grid(self, power):
    #     self.client.publish(PICO_TOPIC, json.dumps({"target": Device.EXTERNAL_GRID , "payload": power}), 2)

    def send_storage_power(self, power):
        self.client.publish(self._get_pico_topic(Device.STORAGE), json.dumps({"target": Device.STORAGE, "payload": power}), 2)

    # transmit actual voltage div by 10
    def send_load_power(self, load: str, power):
        self.client.publish(self._get_pico_topic(load), json.dumps({"target": load, "payload": power}), 2)

    def send_override(self):
        self.client.publish(UI_TOPIC, json.dumps({"target": OVERRIDE_TARGET, "payload": self.manual}), 2)

    def end(self):
        self.client.disconnect()

    def reset_db_data(self):
        self.db_data = {}

    def handle_msg(self, client, userdata, message):
        try:
            msg_str = message.payload.decode()
            topic = message.topic
            # print(f"Message received: {msg_str} on topic {topic}")

            data = json.loads(msg_str)

            if "target" not in data or "payload" not in data:
                raise Exception("Invalid message format")
            
            elif data["target"] == OVERRIDE_TARGET:
                if str(data["payload"]) == "req": self.send_override()
                else: self.manual = data["payload"]
            
            elif data["target"] == Device.EXTERNAL_GRID:
                import_power = data["payload"]["import_power"] 
                export_power = data["payload"]["export_power"]
                if import_power == None:
                    # self.db_data["export_power"] += [export_power]
                    self.add_to_dict("export_power", export_power)
                else:
                    # self.db_data["import_power"] += [import_power]
                    self.add_to_dict("import_power", import_power)


            elif data["target"] == Device.PV_ARRAY:
                pv_power = data["payload"]
                # self.db_data["pv_power"] += [pv_power]
                self.add_to_dict("pv_power", pv_power)
            
            elif data["target"] == Device.STORAGE:
                if data["payload"]["type"] == "soc":
                    soc = data["payload"]["value"]
                    self.db_data["soc"] = soc
                    # print(f"SOC: {soc}")
                elif data["payload"]["type"] == "power":
                    storage_power = data["payload"]["value"]
                    # self.db_data["storage_power"] += [storage_power]
                    self.add_to_dict("storage_power", storage_power)

            else:
                # then use target to check what type of load it is
                # target is storing it as a string
                load = data["target"]
                load_power = data["payload"]
                self.add_to_dict(load, load_power)
            
        except Exception as e:
            print(f"Error message: {e}")

    def add_to_dict(self, key, value):
        if key in self.db_data:
            self.db_data[key] += [value]
        else:
            self.db_data[key] = [value]

    def get_full_tick(self, tick: Tick, p_import, p_store, deferables_supplied) -> FullTick | None:
        try:
            return FullTick(
                day=tick.day,
                tick=tick.tick,
                demand=tick.demand,
                sun=tick.sun,
                buy_price=tick.buy_price,
                sell_price=tick.sell_price,
                cost=0.0,
                avg_pv_power=self._get_avg(self.db_data["pv_power"]),
                storage_soc=float(self.db_data["soc"] if "soc" in self.db_data else 0),
                avg_storage_power=self._get_avg(self.db_data["storage_power"] if "storage_power" in self.db_data else [0]),
                avg_import_export_power=self._get_avg(self._get_from_db_data("import_power")) + self._get_avg(self._get_from_db_data("export_power")),
                avg_red_power=self._get_avg(self.db_data[Device.LOADR]),
                avg_blue_power=self._get_avg(self.db_data[Device.LOADB]),
                avg_yellow_power=self._get_avg(self.db_data[Device.LOADY]),
                avg_grey_power=self._get_avg(self.db_data[Device.LOADK]),
                algo_import_power=p_import,
                algo_store_power=p_store,
                algo_blue_power=deferables_supplied[0],
                algo_yellow_power=deferables_supplied[2],
                algo_grey_power=deferables_supplied[1]
            )
        except Exception as e:
            print(f"Failed to create object: {e}")
            return None

    def _get_avg(self, data):
        if len(data) > 0: return float(sum(data) / len(data))
        else: return 0.0
    
    def _get_from_db_data(self, key):
        if key in self.db_data:
            return self.db_data[key]
        else:
            return []
    
    def _get_pico_topic(self, device: str) -> str:
        return f"{PICO_TOPIC}/{device}"
            



def handle_connect(client, userdata, flags, rc, o):
    if rc != 0:
        raise Exception("Failed to connect to broker")
    client.subscribe(SERVER_TOPIC)
    print("Connected to Broker")
