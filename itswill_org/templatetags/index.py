from django import template

register = template.Library()

import calendar
import datetime

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
def truncstring(obj, length):
    if len(obj) > length:
        return f"{obj[:length]}..."
    else:
        return obj

@register.filter
def to_percent(obj, sigdigits):
    if obj:
        return "{0:.{sigdigits}%}".format(obj, sigdigits=sigdigits)
    else:
        return obj


@register.filter
def filter_on_index(indexable, index):
    return list(filter(lambda item: item[index], indexable))


@register.filter
def filter_on_not_index(indexable, index):
    return list(filter(lambda item: not item[index], indexable))


@register.filter
def dtformatswap(dtstring: str, format: str):
    return datetime.datetime.strptime(
        dtstring, luscioustwitch.TWITCH_API_TIME_FORMAT
    ).strftime(format)


@register.filter
def month_name(month_number):
    return calendar.month_name[month_number]


@register.filter
def field_from_name(obj, field_name):
    return obj._meta.get_field(field_name)


@register.filter
def typing_time(characters):
    return time_to_pretty_string(characters // 5, False)


@register.filter
def time_to_pretty_string(input: int, abbr: bool = False):
    days, rem = divmod(input, (3600 * 24))
    hours, rem = divmod(rem, 3600)
    minutes, rem = divmod(rem, 60)
    seconds = rem

    output = ""

    msd_hit = False
    if days > 0:
        output += f"{days}d " if abbr else f"{days} days, "
        msd_hit = True
    if msd_hit or hours > 0:
        output += f"{hours}h " if abbr else f"{hours} hours, "
        msd_hit = True
    if msd_hit or minutes > 0:
        output += (
            f"{minutes}m {seconds}s"
            if abbr
            else f"{minutes} minutes and {seconds} seconds"
        )
        msd_hit = True

    if not msd_hit:
        output += f"{seconds}s" if abbr else f"{seconds} seconds"

    return output


@register.filter
def divide(numerator: int, divisor: int):
    return numerator / divisor


@register.filter
def intdivide(numerator: int, divisor: int):
    return numerator // divisor

@register.filter
def remove_port(host: str):
    return host.split(":")[0]
