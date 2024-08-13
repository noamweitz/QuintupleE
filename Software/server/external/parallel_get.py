import asyncio
import aiohttp
from models import Day, Tick


# runs an aysnc get request
async def get(client: aiohttp.ClientSession, url):
    res = await client.get(url, ssl=True)
    return await res.json()


# uses connection pooling:
# will use the same tcp connection where it can
async def parallel_get(base_url, paths):
    client = None
    res = None

    # tries 5 times to get a response from the web server
    for i in range(5):
        try:
            client = aiohttp.ClientSession(base_url=base_url)
            res = await asyncio.gather(*[get(client, path) for path in paths])

        except Exception as e:
            print(f"An error occured in parallel get: {e}")
            res = None

        finally:
            if client:
                await client.close()

            # only returns if it gets a response from the web server
            if res != None:
                return res

    # if outside for loop - then it has failed 5 times
    raise Exception("Failed to get data from external server")


# gets current day and tick from external server
def get_day_and_tick(tick_val, tick_len=5):
    endpoints = ["/sun", "/price", "/demand"]
    day = None
    tick = None

    deferables_data = None

    if tick_val == None or tick_val == 59:
        endpoints.append("/deferables")

    data = asyncio.run(
        parallel_get(
            "https://icelec50015.azurewebsites.net/",
            endpoints
        )
    )
    

    sun_data = data[0]
    price_data = data[1]
    demand_data = data[2]

    if len(data) > 3:
        deferables_data = data[3]

        day = Day.model_validate({"day": price_data["day"], "deferables": deferables_data})

    tick = Tick.model_validate(
        {
            "tick": price_data["tick"],
            "sun": sun_data["sun"],
            "demand": demand_data["demand"] * tick_len,
            "sell_price": price_data["sell_price"],
            "buy_price": price_data["buy_price"],
            "day": price_data["day"],
        }
    )

    return day, tick


if __name__ == "__main__":
    urls = ["/sun", "/price", "/demand", "/deferables"]
    print(asyncio.run(parallel_get("https://icelec50015.azurewebsites.net/", urls)))
