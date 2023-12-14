import aiohttp
import asyncio
import html
import re
import uuid

async def postagde_request(trackno):
    url = "https://wsp.posta.rs/WSPWrapperService.asmx"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "Accept": "*/*",
        "Accept-Language": "sr-Latn,en-US;q=0.9,en;q=0.8",
        "User-Agent": "PTTMOB/1 CFNetwork/1410.0.3 Darwin/22.6.0",
    }

    # Generate a random UUID for each request
    transakcija_id = str(uuid.uuid4())

    # The updated XML template with a random UUID and provided trackno
    xml_request = f"""<?xml version='1.0' encoding='UTF-8'?>
    <v:Envelope xmlns:v='http://schemas.xmlsoap.org/soap/envelope/' xmlns:c='http://schemas.xmlsoap.org/soap/encoding/' xmlns:d='http://www.w3.org/2001/XMLSchema' xmlns:i='http://www.w3.org/2001/XMLSchema-instance'>
      <v:Header />
      <v:Body>
        <Transakcija xmlns='http://posta.rs/webservices/' id='o0' c:root='1'>
          <xmlKlijent i:type='d:string'>&lt;?xml version="1.0" encoding="utf-8"?&gt;&lt;Klijent&gt;&lt;Username&gt;mapuser@ptt.rs&lt;/Username&gt;&lt;IdTipUredjaja&gt;3&lt;/IdTipUredjaja&gt;&lt;VerzijaOS&gt;iOS 8.0 +&lt;/VerzijaOS&gt;&lt;ModelUredjaja&gt;iPhone12,1&lt;/ModelUredjaja&gt;&lt;VerzijaAplikacije&gt;Pošta Srbije, v.1.0.10 (1)&lt;/VerzijaAplikacije&gt;&lt;Jezik&gt;LAT&lt;/Jezik&gt;&lt;/Klijent&gt;</xmlKlijent>
          <servis i:type='d:int'>11</servis>
          <idVrstaTransakcije i:type='d:string'>63</idVrstaTransakcije>
          <idTransakcija i:type='d:string'>{transakcija_id}</idTransakcija>
          <xmlIn i:type='d:string'>&lt;?xml version="1.0" encoding="utf-8"?&gt;&lt;TTKretanjeIn&gt;&lt;VrstaUsluge&gt;1&lt;/VrstaUsluge&gt;&lt;PrijemniBroj&gt;{trackno}&lt;/PrijemniBroj&gt;&lt;/TTKretanjeIn&gt;</xmlIn>
          <xmlOut i:type='d:string' />
          <xmlRezultat i:type='d:string' />
        </Transakcija>
      </v:Body>
    </v:Envelope>
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=xml_request.encode('utf-8')) as response:
            # Ensure the response was successful (status code 200)
            if response.status == 200:
                # Extract data from the response
                response_text = html.unescape(await response.text())
                #print(response_text)
                data_list = await asyncio.to_thread(extract_data, response_text)
                return data_list
            else:
                print(f"Error: Request failed with status code {response.status}")
                return None

def extract_data(response):
    data_list = []

    # Assuming `response` is the content of the response
    response = response.strip()

    search_term = "Pošiljka nije pronađena. Proverite ispravnost unetog broja."

    # Check if the search term is present in the XML response
    if search_term in response:
        return search_term
    else:
        # Extract content within <Status>, <Datum>, and <Mesto> tags
        status_matches = re.findall(r'<Status>(.*?)</Status>', response)
        datum_matches = re.findall(r'<Datum>(.*?)</Datum>', response)
        mesto_matches = re.findall(r'<Mesto>(.*?)</Mesto>', response)

        # Iterate through matches and extract information
        for status, datum, mesto in zip(status_matches, datum_matches, mesto_matches):
            data_list.append({"date": datum, "location": mesto, "status": status})

    return data_list

# Run the event loop
if __name__ == "__main__":
    trackno = input("Enter the track number: ")
    asyncio.run(postagde_request(trackno))
