from MetarTaf import *
import requests
from pymongo import MongoClient
import os

# Mongo setup


mongo_uri = os.environ.get("MONGO_URI")

if not mongo_uri:
    raise EnvironmentError("MONGO_URI not set in environment variables.")

client = MongoClient(mongo_uri)
db = client["aviation"]
metar_collection = db["metar_conditions"]
taf_collection = db["taf_conditions"]

def GetAirportCodes():
  # TODO: Load airport codes from a file or database
  airport_codes = [
    "LOWW", "LOWS", "LOWI", "LOWG", "LOWL", "LOWK",
    "EDDM", "EDDF", "EHAM", "EGLL"
  ]
  return airport_codes

def save_metar_to_db(metar_obj: MetarConditions):
    if metar_obj:
        metar_collection.replace_one(
            {"station": metar_obj.station, "time": metar_obj.time},
            metar_obj.to_dict(),
            upsert=True
        )

def save_taf_to_db(taf_obj: TAFConditions):
    if taf_obj:
        taf_collection.replace_one(
            {"station": taf_obj.station, "issueTime": taf_obj.issueTime},
            taf_obj.to_dict(),
            upsert=True
        )

def GetMetarData(id: str) -> str:
  url = f"https://aviationweather.gov/api/data/metar?ids={id}&format=raw&taf=false&hours=1"
  response = requests.get(url)
  response.raise_for_status()
  return response.text

def GetTafData(id: str) -> str:
  url = f"https://aviationweather.gov/api/data/taf?ids={id}&format=raw&metar=false&time=valid"
  response = requests.get(url)
  response.raise_for_status()
  text = response.text.replace('\n', '')
  if not text.startswith('TAF'):
    text = 'TAF ' + text
  return text

def main():
  for airport_code in GetAirportCodes():
    try:
      metarRaw = GetMetarData(airport_code)
      tafRaw = GetTafData(airport_code)
      metarParsed = parse_metar_conditions(metarRaw)
      tafParsed = parse_taf_conditions(tafRaw)

      save_metar_to_db(metarParsed)
      save_taf_to_db(tafParsed)

    except requests.RequestException as e:
      print(f"Error fetching data for {airport_code}: {e}") 

if __name__ == "__main__":
  main()