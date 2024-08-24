from django import template
register = template.Library()

@register.filter
def index(indexable, i):
    return indexable[i]
  
@register.filter
def firstn(indexable, n):
  return indexable[:n]

@register.filter
def keyvalue(dictionary, key):
  return dictionary[key]