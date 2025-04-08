import os
import django
import csv
from django.core.exceptions import ValidationError
import sys
import json
import luscioustwitch
import datetime
from django.conf import settings

sys.path.append(".")
  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from itswill_org.models import *

datapath = "./itswill_org/util/reviews.csv"

SUMMARY_REGEX = re.compile('<.+?>')
    
with open(datapath, 'r', newline='', encoding='utf8') as csvfile:
  reviewreader = csv.reader(csvfile, delimiter=',', quotechar="\"")
  for i, row in enumerate(reviewreader):
    rating = None if row[4] == '' else float(row[4])
    
    title = row[1]
    review_id = f"imported-review-{i}"
    link = ""
    pub_date = datetime.datetime.strptime(row[8], "%Y-%m-%d") if row[0] == "" else datetime.datetime.strptime(row[0], "%Y-%m-%d")
    watched_date = datetime.datetime.strptime(row[8], "%Y-%m-%d")
    film_title = row[1]
    film_year = None if row[2] == "No year" else row[2]
    member_rating = rating
    movie_id = None
    description = row[6]
    description : str = re.sub(SUMMARY_REGEX, ' ', description)
    description = description.strip()
    creator = "willie suede"
    
    obj, created = LetterboxdReview.objects.get_or_create(
      film_title = film_title,
      watched_date = watched_date,
      defaults = {
        "review_id": review_id,
        "pub_date": pub_date,
        "film_title": film_title,
        "film_year": film_year,
        "member_rating": member_rating,
        "movie_id": movie_id,
        "description": description,
        "creator": creator
      }
    )
    