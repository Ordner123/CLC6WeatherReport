from metar_taf_parser.parser.parser import MetarParser, FMValidity, TAFParser
from datetime import datetime, timedelta

class MetarConditions:
  station: str = None
  time: datetime = None
  windSpeed: int = None
  windDirection: str = None
  windDegrees: int = None
  temperature: int = None
  dewPoint: int = None
  visibility: str = None

  # Dictionary representation for easier output and storage
  def to_dict(self):
    return self.__dict__

class TAFTrend:
  validityStart: datetime = None
  validityEnd: datetime = None
  visibilityDistance: str = None
  cloudHeights: list[int] = []
  windSpeed: int = None
  windDirection: str = None
  windDegrees: int = None

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


class TAFConditions:
  station: str = None
  issueTime: datetime = None
  maxTemperature: int = None
  minTemperature: int = None
  windSpeed: int = None
  windDirection: str = None
  windDegrees: int = None
  visibility: str = None
  trends: list[TAFTrend] = []

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

def output_metar_conditions(conditions: 'MetarConditions'):
  print(f"Station: {conditions.station}")
  print(f"Time: {conditions.time}")
  print(f"Wind: {conditions.windDirection} ({conditions.windDegrees}°) at {conditions.windSpeed} kt")
  print(f"Temperature: {conditions.temperature}°C")
  print(f"Dew Point: {conditions.dewPoint}°C")
  print(f"Visibility: {conditions.visibility}")

def output_taf_conditions(conditions: 'TAFConditions'):
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
    metar = MetarParser().parse(s)
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
    taf = TAFParser().parse(s)
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
