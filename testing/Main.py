# pip install metar-taf-parser-mivek
from MetarTaf import *
import requests

metar_conditions = parse_metar_conditions('KTTN 051853Z 04011KT 9999 VCTS SN FZFG BKN003 OVC010 M02/M02 A3006')
taf_conditions = parse_taf_conditions('TAF LFPG 150500Z 1506/1612 17005KT 6000 SCT012 TEMPO 1506/1509 3000 BR BKN006 PROB40 TEMPO 1506/1508 0400 BCFG BKN002 PROB40 TEMPO 1512/1516 4000 -SHRA FEW030TCU BKN040 BECMG 1520/1522 CAVOK TEMPO 1603/1608 3000 BR BKN006 PROB40 TEMPO 1604/1607 0400 BCFG BKN002 TX17/1512Z TN07/1605Z')

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

metarRaw = GetMetarData("LOWL")
tafRaw = GetTafData("LOWL")


metarParsed = parse_metar_conditions(metarRaw)
print(metarRaw)
output_metar_conditions(metarParsed)
print("")
tafParsed = parse_taf_conditions(tafRaw)
print(tafRaw)
output_taf_conditions(tafParsed)

