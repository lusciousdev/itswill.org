from django import template
register = template.Library()

import datetime
import calendar
import luscioustwitch

@register.filter
def index(indexable, i):
    return indexable[i]
  
@register.filter
def firstn(indexable, n):
  return indexable[:n]

@register.filter
def keyvalue(dictionary, key):
  return dictionary[key]

@register.filter
def to_percent(obj, sigdigits):
  if obj:
    return "{0:.{sigdigits}%}".format(obj, sigdigits = sigdigits)
  else:
    return obj
  
@register.filter
def filter_on_index(indexable, index):
  return list(filter(lambda item: item[index], indexable))

@register.filter
def filter_on_not_index(indexable, index):
  return list(filter(lambda item: not item[index], indexable))

@register.filter
def dtformatswap(dtstring : str, format : str):
  return datetime.datetime.strptime(dtstring, luscioustwitch.TWITCH_API_TIME_FORMAT).strftime(format)

@register.filter
def month_name(month_number):
  return calendar.month_name[month_number]

@register.filter
def field_from_name(obj, field_name):
  return obj._meta.get_field(field_name)