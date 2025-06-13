from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson.json_util import dumps
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import os
import json
from MetarTaf import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Oder z. B. ["http://localhost:64273"] für mehr Sicherheit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Read Mongo URI from env variable
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["aviation"]


class DTORequest(BaseModel):
  stations: List[str]
  startTime: Optional[datetime] = None

class DTOMetarResponse(BaseModel):
  description: str
  issueTime: datetime
  station: str

class DTOStationInfo(BaseModel):
  name: str
  code: str

class DTOTafTrend(BaseModel):
  description: str
  validityStart: datetime
  validityEnd: datetime

class DTOTafResponse(BaseModel):
  description: str
  issueTime: datetime
  station: str
  trends: List[DTOTafTrend]

def createMetarReponse(metar: MetarConditions) -> DTOMetarResponse:
  parts = []

  if metar.station:
      parts.append(f"At station {metar.station}")

  if metar.issueTime:
      parts.append(f"on {metar.issueTime.strftime('%Y-%m-%d')}")
      parts.append(f"at {metar.issueTime.strftime('%H:%M')} UTC")

  if metar.windSpeed is not None:
      if metar.windDirection:
          parts.append(f"the wind is blowing from {metar.windDirection} at {metar.windSpeed} knots")
      else:
          parts.append(f"the wind speed is {metar.windSpeed} knots")

  if metar.visibility:
      parts.append(f"with visibility of {metar.visibility}")

  if metar.temperature is not None and metar.dewPoint is not None:
      parts.append(f"and a temperature of {metar.temperature}°C with a dew point of {metar.dewPoint}°C")
  elif metar.temperature is not None:
      parts.append(f"and a temperature of {metar.temperature}°C")

  sentence = " ".join(parts) + "."
  return DTOMetarResponse(
      description=sentence,
      issueTime=metar.issueTime,
      station=metar.station
  )

def describe_trend(trend: TAFTrend) -> str:
    start = trend.validityStart.strftime("%Y-%m-%d %H:%M UTC") if trend.validityStart else "unknown start"
    end = trend.validityEnd.strftime("%Y-%m-%d %H:%M UTC") if trend.validityEnd else None

    if end:
        time_range = f"From {start} to {end},"
    else:
        time_range = f"Starting from {start},"

    parts = [time_range]

    if trend.windSpeed is not None:
        if trend.windDirection:
            parts.append(f"expect wind from {trend.windDirection} at {trend.windSpeed} knots")
        else:
            parts.append(f"expect wind at {trend.windSpeed} knots")

    if trend.visibilityDistance:
        parts.append(f"with visibility around {trend.visibilityDistance}")

    if trend.cloudHeights:
        cloud_text = ", ".join(f"{h} ft" for h in trend.cloudHeights)
        parts.append(f"and clouds at {cloud_text}")

    if len(parts) == 1:
        parts.append("no significant weather changes expected.")

    return " ".join(parts).capitalize()

def create_taf_response(taf: TAFConditions) -> DTOTafResponse:
    time_str = taf.issueTime.strftime("%Y-%m-%d %H:%M UTC") if taf.issueTime else "unknown time"
    parts = [f"The TAF report for station {taf.station} was issued at {time_str}."]

    if taf.windSpeed is not None:
        if taf.windDirection:
            parts.append(f"General forecast indicates wind from {taf.windDirection} at {taf.windSpeed} knots")
        else:
            parts.append(f"General forecast indicates wind at {taf.windSpeed} knots")

    if taf.visibility:
        parts.append(f"with visibility around {taf.visibility}")

    if taf.maxTemperature is not None:
        parts.append(f"maximum temperature of {taf.maxTemperature}°C")

    if taf.minTemperature is not None:
        parts.append(f"and a minimum of {taf.minTemperature}°C")

    description = " ".join(parts)

    dto_trends = []
    for trend in taf.trends:
        trend_description = describe_trend(trend)
        dto_trends.append(DTOTafTrend(
            description=trend_description,
            validityStart=trend.validityStart,
            validityEnd=trend.validityEnd
        ))

    return DTOTafResponse(
        description=description,
        issueTime=taf.issueTime,
        station=taf.station,
        trends=dto_trends
    )


@app.get("/metar/{station}")
def get_metar(station: str):
    metar_data = db.metar_conditions.find_one(
      {"station": station},
      sort=[("issueTime", -1)]
    )
    if not metar_data:
      raise HTTPException(status_code=404, detail="METAR data not found for the specified station.")

    metar = MetarConditions.from_dict(metar_data)
    response = createMetarReponse(metar)
    return response

@app.post("/metar/query")
def query_metar(request: DTORequest = Body(...)):
  results = []
  for station in request.stations:
    query = {"station": station}
    if request.startTime:
      query["issueTime"] = {"$gte": request.startTime}
      metar_cursor = db.metar_conditions.find(query, sort=[("issueTime", -1)])
      metar_list = list(metar_cursor)
    else:
      metar_data = db.metar_conditions.find_one(query, sort=[("issueTime", -1)])
      metar_list = [metar_data] if metar_data else []
    for metar_data in metar_list:
      if metar_data:
        metar = MetarConditions.from_dict(metar_data)
        response = createMetarReponse(metar)
        results.append(response)
  if not results:
    raise HTTPException(status_code=404, detail="No METAR data found for the specified stations and time.")
  return results

@app.post("/taf/query")
def query_taf(request: DTORequest = Body(...)):
  results = []
  for station in request.stations:
    query = {"station": station}
    if request.startTime:
      query["issueTime"] = {"$gte": request.startTime}
      taf_cursor = db.taf_conditions.find(query, sort=[("issueTime", -1)])
      taf_list = list(taf_cursor)
    else:
      taf_data = db.taf_conditions.find_one(query, sort=[("issueTime", -1)])
      taf_list = [taf_data] if taf_data else []
    for taf_data in taf_list:
      if taf_data:
        taf = TAFConditions.from_dict(taf_data)
        response = create_taf_response(taf)
        results.append(response)
  if not results:
    raise HTTPException(status_code=404, detail="No TAF data found for the specified stations and time.")
  return results

@app.post("/station")
def add_stations(stations: List[DTOStationInfo]):
  results = []
  for station_info in stations:
    station_info_obj = StationInfo(station_info.code, station_info.name)
    result = db.stations.replace_one(
      {"code": station_info.code},
      station_info_obj.to_dict(),
      upsert=True
    )
    if not result.acknowledged:
      raise HTTPException(status_code=500, detail=f"Failed to save station info for code {station_info.code}.")
    results.append({"code": station_info.code, "message": "Station info saved successfully."})
  return results

@app.get("/stations")
def get_stations():
  stations_cursor = db.stations.find()
  stations = [DTOStationInfo(name=station.get("name", ""), code=station.get("code", "")) for station in stations_cursor]
  return stations

if __name__ == "__main__":
    uvicorn.run("ReportApi:app", host="0.0.0.0", port=8000)