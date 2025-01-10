import aiohttp
import asyncio
import html
import re
import uuid
import json

async def postagde_request(trackno):
    url = "https://api.posta.rs/paketi"

    # Generate a random UUID for each request
    transakcija_id = str(uuid.uuid4())

    payload = {
        "TipSerijalizacije": 2,
        "StrKlijent": json.dumps({
            "Username": "MAPeN",
            "Password": "<09;znCF_£..%B{93K##",
            "Jezik": "LAT",
            "IdTipUredjaja": 3,
            "NazivUredjaja": "land",
            "ModelUredjaja": "Redmi 3S",
            "VerzijaOS": "UPSIDE_DOWN_CAKE",
            "VerzijaAplikacije": "2.0.4",
            "IPAdresa": "",
            "Geolokacija": "",
            "Referenca": ""
        }),
        "Servis": 111,
        "IdVrstaTranskacije": 63,
        "IdTransakcija": transakcija_id,
        "StrIn": json.dumps({
            "VrstaUsluge": 1,
            "EksterniBroj": "",
            "PrijemniBroj": trackno
        })
    }

    headers = {
        'Content-Type': 'application/json',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logging.error(f"Error: Request failed with status code {response.status}")
                return None

# Run the event loop
if __name__ == "__main__":
    trackno = input("Enter the track number: ")
    result = asyncio.run(postagde_request(trackno))
#    if "Uručena" in result:
#        print("Delivered.")
    print(result)

