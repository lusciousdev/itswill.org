import datetime
import pytz
from string import Template

TIMEZONE_NAME = "America/Los_Angeles"
TIMEZONE = pytz.timezone(TIMEZONE_NAME)

class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta : datetime.timedelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    _, hours_12hr = divmod(hours, 12)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["HH"] = '{}'.format(hours_12hr)
    d["h"] = '{}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["m"] = '{}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    d["s"] = '{}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)
  
def smartfmtdelta(tdelta : datetime.timedelta):
  hours, rem = divmod(tdelta.seconds, 3600)
  minutes, _ = divmod(rem, 60)
  
  if hours > 0:
    return strfdelta(tdelta, "%{h}h %{M}m %{S}s")
  elif minutes > 0:
    return strfdelta(tdelta, "%{m}m %{S}s")
  else:
    return strfdelta(tdelta, "%{s}s")

def utc_to_local(utc_dt : datetime.datetime, local_tz):
  return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=local_tz)

def timeadd(time1 : datetime.time, time2 : datetime.time):
  return (datetime.datetime.combine(datetime.date.today(), time1) + datetime.datetime.combine(datetime.date.today(), time2))

def timediff(time1 : datetime.time, time2: datetime.time):
  return (datetime.datetime.combine(datetime.date.today(), time1) - datetime.datetime.combine(datetime.date.today(), time2))