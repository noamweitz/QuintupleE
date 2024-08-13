from external_sync import getExternalTick
import time

def test_sync():
    prevTick = getExternalTick()

    while True:
        curTick = getExternalTick()

        if prevTick != curTick:
            # print(f"prevTick: {prevTick}, curTick: {curTick}")
            t = time.time()
            with open("exact.csv", "a") as file:
                file.write(f"{t},{curTick}\n")
            prevTick = curTick
    

if __name__ == "__main__":
    test_sync()