from mqtt_client import *
from time import sleep

if __name__ == "__main__":
    pv = MClient(smps_type=SUN_TOPIC)
    storage = MClient(smps_type=STORAGE_TOPIC)
    ext_grid = MClient(smps_type=EXT_GRID_TOPIC)
    l1 = MClient(smps_type=LOAD_TOPICS[0])
    l2 = MClient(smps_type=LOAD_TOPICS[1])
    l3 = MClient(smps_type=LOAD_TOPICS[2])
    l4 = MClient(smps_type=LOAD_TOPICS[3])
    
    while True:
        pv.send_sun_data(gen_smps("pv"))
        storage.send_storage_smps(gen_smps("storage"))
        ext_grid.send_ext_grid_smps(gen_smps("external-grid"))
        l1.send_load(1, gen_smps("l1"))
        l2.send_load(2, gen_smps("l2"))
        l3.send_load(3, gen_smps("l3"))
        l4.send_load(4, gen_smps("l4"))
        sleep(5)