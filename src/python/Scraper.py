from MetarTaf import *
import requests
from pymongo import MongoClient
import os

# Mongo setup


mongo_uri = os.environ.get("MONGO_URI")

if not mongo_uri:
    raise EnvironmentError("MONGO_URI not set in environment variables.")

#mongo_uri = "mongodb://localhost:27017"  # Default for local MongoDB instance
client = MongoClient(mongo_uri)
db = client["aviation"]
metar_collection = db["metar_conditions"]
taf_collection = db["taf_conditions"]

def GetAirportCodes():
  # TODO: Load airport codes from a file or database
  #airport_codes = [
  #  "LOWW", "LOWS", "LOWI", "LOWG", "LOWL", "LOWK",
  #  "EDDM", "EDDF", "EHAM", "EGLL"
  #]
  return [doc["code"] for doc in db["stations"].find({}, {"code": 1, "_id": 0})]

def save_metar_to_db(metar_obj: MetarConditions):
    if metar_obj:
        metar_collection.replace_one(
            {"station": metar_obj.station, "issueTime": metar_obj.issueTime},
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
  airport_codes = GetAirportCodes()
  print(f"Found {len(airport_codes)} airport codes to process.")
  for airport_code in airport_codes:
    try:
      metarRaw = GetMetarData(airport_code)
      metarParsed = parse_metar_conditions(metarRaw)
      save_metar_to_db(metarParsed)
      print(f"Processed METAR {airport_code}")
      
      tafRaw = GetTafData(airport_code)
      tafParsed = parse_taf_conditions(tafRaw)
      save_taf_to_db(tafParsed)
      print(f"Processed TAF   {airport_code}")
    except requests.RequestException as e:
      print(f"Error fetching data for {airport_code}: {e}") 
if __name__ == "__main__":
  main()