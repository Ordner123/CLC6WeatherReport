from metar_taf_parser.parser.parser import MetarParser, FMValidity, TAFParser
from datetime import datetime, timedelta

class MetarConditions:
  def __init__(self, station=None, time=None, windSpeed=None, windDirection=None,
                windDegrees=None, temperature=None, dewPoint=None, visibility=None):
      self.station = station
      self.time = time
      self.windSpeed = windSpeed
      self.windDirection = windDirection
      self.windDegrees = windDegrees
      self.temperature = temperature
      self.dewPoint = dewPoint
      self.visibility = visibility

  # Dictionary representation for easier output and storage
  def to_dict(self):
    return self.__dict__
  
  @staticmethod
  def from_dict(data):
      return MetarConditions(**data)

class TAFTrend:
  def __init__(self, validityStart=None, validityEnd=None, visibilityDistance=None,
                cloudHeights: list[int] = None, windSpeed=None, windDirection=None,
                windDegrees=None):
    self.validityStart = validityStart
    self.validityEnd = validityEnd
    self.visibilityDistance = visibilityDistance
    self.cloudHeights = cloudHeights or []
    self.windSpeed = windSpeed
    self.windDirection = windDirection
    self.windDegrees = windDegrees

  def to_dict(self):
    return {
        "validityStart": self.validityStart,
        "validityEnd": self.validityEnd,
        "visibilityDistance": self.visibilityDistance,
        "cloudHeights": self.cloudHeights,
        "windSpeed": self.windSpeed,
        "windDirection": self.windDirection,
        "windDegrees": self.windDegrees
    }
  
  @staticmethod
  def from_dict(data):
      return TAFTrend(**data)

class TAFConditions:
  def __init__(self, station=None, issueTime=None, maxTemperature=None, minTemperature=None,
               windSpeed=None, windDirection=None, windDegrees=None, visibility=None,
               trends: list[TAFTrend] = None):
    self.station = station
    self.issueTime = issueTime
    self.maxTemperature = maxTemperature
    self.minTemperature = minTemperature
    self.windSpeed = windSpeed
    self.windDirection = windDirection
    self.windDegrees = windDegrees
    self.visibility = visibility
    self.trends = trends or []

  def to_dict(self):
    return {
        "station": self.station,
        "issueTime": self.issueTime,
        "maxTemperature": self.maxTemperature,
        "minTemperature": self.minTemperature,
        "windSpeed": self.windSpeed,
        "windDirection": self.windDirection,
        "windDegrees": self.windDegrees,
        "visibility": self.visibility,
        "trends": [trend.to_dict() for trend in self.trends]
    }
  
  @staticmethod
  def from_dict(data):
     return TAFConditions(
         station=data.get("station"),
         issueTime=data.get("issueTime"),
         maxTemperature=data.get("maxTemperature"),
         minTemperature=data.get("minTemperature"),
         windSpeed=data.get("windSpeed"),
         windDirection=data.get("windDirection"),
         windDegrees=data.get("windDegrees"),
         visibility=data.get("visibility"),
         trends=[TAFTrend.from_dict(trend) for trend in data.get("trends", [])]
     )
  
def output_metar_conditions(conditions: 'MetarConditions'):
  if not conditions:
    print("No valid METAR conditions available.")
    return
  print(f"Station: {conditions.station}")
  print(f"Time: {conditions.time}")
  print(f"Wind: {conditions.windDirection} ({conditions.windDegrees}°) at {conditions.windSpeed} kt")
  print(f"Temperature: {conditions.temperature}°C")
  print(f"Dew Point: {conditions.dewPoint}°C")
  print(f"Visibility: {conditions.visibility}")

def output_taf_conditions(conditions: 'TAFConditions'):
  if not conditions:
    print("No valid TAF conditions available.")
    return
  print(f"Station: {conditions.station}")
  print(f"Issue Time: {conditions.issueTime}")
  print(f"Max Temperature: {conditions.maxTemperature}°C")
  print(f"Min Temperature: {conditions.minTemperature}°C")
  print(f"Wind: {conditions.windDirection} ({conditions.windDegrees}°) at {conditions.windSpeed} kt")
  print(f"Visibility: {conditions.visibility}")
  print("Trends:")
  for trend in conditions.trends:
    print(f"  Validity: {trend.validityStart} to {trend.validityEnd}")
    print(f"  Visibility: {trend.visibilityDistance}")
    print(f"  Cloud Heights: {trend.cloudHeights}")
    print(f"  Wind: {trend.windDirection} ({trend.windDegrees}°) at {trend.windSpeed} kt")

def validity_to_datetimes(validity, reference: datetime) -> tuple[datetime, datetime]:
  """
  Convert Validity[start_day, start_hour, end_day, end_hour] into actual datetimes
  using a reference datetime (usually TAF issue_time).
  
  Args:
      validity: an object with start_day, start_hour, end_day, end_hour
      reference: datetime with known year/month to anchor the day values

  Returns:
      (start_datetime, end_datetime)
  """
  def resolve(day: int, hour: int) -> datetime:
      base = reference.replace(hour=hour, minute=0, second=0, microsecond=0)
      day_diff = (day - reference.day) % 31  # naive wrap handling
      return base + timedelta(days=day_diff)

  start_dt = resolve(validity.start_day, validity.start_hour)
  # Check if validity is of class FMValidity
  if isinstance(validity, FMValidity):
    # FMValidity only has start_day and start_hour, no end
    end_dt = None
  elif validity.end_hour == 24:
    # Special case for end_hour == 24, meaning the end of the day
    end_dt = resolve(validity.end_day, 0)
    end_dt += timedelta(days=1)
  else:
    end_dt = resolve(validity.end_day, validity.end_hour)
    # Handle day rollover (e.g. 30 22:00 → 01 06:00)
    if end_dt < start_dt:
      end_dt += timedelta(days=1)

  return start_dt, end_dt

def parse_metar_conditions(s):
  """
  Parse METAR conditions from a METAR string.

  Args:
      s: METAR string

  Returns:
      MetarConditions object with parsed data
  """

  conditions = MetarConditions()
  try:
      metar = MetarParser().parse(s)
  except Exception as e:
      print(f"Error parsing METAR: {e}")
      print(f"Raw METAR string: {s}")
      return None

  conditions.station = metar.station
  conditions.time = metar.time
  conditions.windSpeed = metar.wind.speed
  conditions.windDirection = metar.wind.direction
  conditions.windDegrees = metar.wind.degrees
  conditions.temperature = metar.temperature
  conditions.dewPoint = metar.dew_point
  conditions.visibility = metar.visibility.distance if metar.visibility else None

  return conditions

def parse_taf_conditions(s):
  """
  Parse TAF conditions from a TAF string.

  Args:
      s: TAF string

  Returns:
      TAFConditions object with parsed data
  """

  conditions = TAFConditions()
  try:
    taf = TAFParser().parse(s)
  except Exception as e:
    print(f"Error parsing TAF: {e}")
    print(f"Raw TAF string: {s}")
    return None
  conditions.station = taf.station
  d = datetime.now() 
  d.replace(day=taf.day)
  hour, minute, second = map(int, str(taf.time).split(":"))
  d = d.replace(hour=hour, minute=minute, second=second, microsecond=0)

  conditions.issueTime = d
  conditions.maxTemperature = taf.max_temperature.temperature if taf.max_temperature else None
  conditions.minTemperature = taf.min_temperature.temperature if taf.min_temperature else None
  conditions.windSpeed = taf.wind.speed if taf.wind else None
  conditions.windDirection = taf.wind.direction if taf.wind else None
  conditions.windDegrees = taf.wind.degrees if taf.wind else None
  conditions.visibility = taf.visibility.distance if taf.visibility else None
  conditions.trends = []

  for trend in taf.trends:
      trend_obj = TAFTrend()
      trend_obj.validityStart, trend_obj.validityEnd = validity_to_datetimes(trend.validity, d)
      trend_obj.visibilityDistance = trend.visibility.distance if trend.visibility else None
      trend_obj.cloudHeights = [cloud.height for cloud in trend.clouds] if trend.clouds else []
      if trend.wind:
          trend_obj.windSpeed = trend.wind.speed
          trend_obj.windDirection = trend.wind.direction
          trend_obj.windDegrees = trend.wind.degrees
      conditions.trends.append(trend_obj)

  return conditions
