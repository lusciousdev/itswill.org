import pandas as pd
import os
import re
import sys
import json
import django
from pathlib import Path
from django.core.exceptions import ValidationError
from django.conf import settings
import argparse
import colorsys
import humanize
import random
from unidecode import unidecode

sys.path.append(".")
  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from itswill_org.models import *

color_list = [
  ( 90, 0.9, 0.9),
  (240, 0.9, 0.9),
  ( 30, 0.9, 0.9),
  (180, 0.9, 0.9),
  (330, 0.9, 0.9),
  (120, 0.9, 0.9),
  (270, 0.9, 0.9),
  ( 60, 0.9, 0.9),
  (210, 0.9, 0.9),
  (  0, 0.9, 0.9),
  (150, 0.9, 0.9),
  (300, 0.9, 0.9),
  
  (105, 0.6, 0.7),
  (255, 0.6, 0.7),
  ( 45, 0.6, 0.7),
  (195, 0.6, 0.7),
  (345, 0.6, 0.7),
  (135, 0.6, 0.7),
  (285, 0.6, 0.7),
  ( 75, 0.6, 0.7),
  (225, 0.6, 0.7),
  ( 15, 0.6, 0.7),
  (165, 0.6, 0.7),
  (315, 0.6, 0.7),
  
  ( 90, 0.6, 0.9),
  (240, 0.6, 0.9),
  ( 30, 0.6, 0.9),
  (180, 0.6, 0.9),
  (330, 0.6, 0.9),
  (120, 0.6, 0.9),
  (270, 0.6, 0.9),
  ( 60, 0.6, 0.9),
  (210, 0.6, 0.9),
  (  0, 0.6, 0.9),
  (150, 0.6, 0.9),
  (300, 0.6, 0.9),
  
  (105, 0.9, 0.7),
  (255, 0.9, 0.7),
  ( 45, 0.9, 0.7),
  (195, 0.9, 0.7),
  (345, 0.9, 0.7),
  (135, 0.9, 0.7),
  (285, 0.9, 0.7),
  ( 75, 0.9, 0.7),
  (225, 0.9, 0.7),
  ( 15, 0.9, 0.7),
  (165, 0.9, 0.7),
  (315, 0.9, 0.7),
  
  ( 90, 0.9, 0.7),
  (240, 0.9, 0.7),
  ( 30, 0.9, 0.7),
  (180, 0.9, 0.7),
  (330, 0.9, 0.7),
  (120, 0.9, 0.7),
  (270, 0.9, 0.7),
  ( 60, 0.9, 0.7),
  (210, 0.9, 0.7),
  (  0, 0.9, 0.7),
  (150, 0.9, 0.7),
  (300, 0.9, 0.7),
  
  (105, 0.6, 0.9),
  (255, 0.6, 0.9),
  ( 45, 0.6, 0.9),
  (195, 0.6, 0.9),
  (345, 0.6, 0.9),
  (135, 0.6, 0.9),
  (285, 0.6, 0.9),
  ( 75, 0.6, 0.9),
  (225, 0.6, 0.9),
  ( 15, 0.6, 0.9),
  (165, 0.6, 0.9),
  (315, 0.6, 0.9),
  
  ( 90, 0.6, 0.7),
  (240, 0.6, 0.7),
  ( 30, 0.6, 0.7),
  (180, 0.6, 0.7),
  (330, 0.6, 0.7),
  (120, 0.6, 0.7),
  (270, 0.6, 0.7),
  ( 60, 0.6, 0.7),
  (210, 0.6, 0.7),
  (  0, 0.6, 0.7),
  (150, 0.6, 0.7),
  (300, 0.6, 0.7),
  
  (105, 0.9, 0.9),
  (255, 0.9, 0.9),
  ( 45, 0.9, 0.9),
  (195, 0.9, 0.9),
  (345, 0.9, 0.9),
  (135, 0.9, 0.9),
  (285, 0.9, 0.9),
  ( 75, 0.9, 0.9),
  (225, 0.9, 0.9),
  ( 15, 0.9, 0.9),
  (165, 0.9, 0.9),
  (315, 0.9, 0.9),
]

multi_answer_questions = [
  "What types of itswill videos do you typically watch?",
  "What are your 3 favorite variety games/genres?",
  "Do you have any Twitch extensions installed?",
  "Which RuneScape games do you play?",
  "What sports do you watch?",
  "What sports do you play?",
  "What types of games do you play?",
  "What OSRS content do you enjoy?",
]

keep_none = [
  "What types of itswill videos do you typically watch?",
  "What are your 3 favorite variety games/genres?",
  "Do you have any Twitch extensions installed?",
  "Which RuneScape games do you play?",
  "What sports do you watch?",
  "What sports do you play?",
  "What types of games do you play?",
  "What hobbies do you enjoy?",
]

open_input_questions = [
  "What is your favorite variety stream of all time?",
  "What hobbies do you enjoy?",
  "What's your favorite movie?",
  "Which kind of pets do you have?",
  "Who would you like to see itswill collaborate with? (optional)",
  "What games would you like to see itswill play? (optional)",
  "What's your favorite emote? (optional)",
  "Who's your favorite chatter? (optional)",
  "Do you have any recommendations for overlay features? (optional)",
]

skip_question = [
  "Do you have any recommendations for overlay features? (optional)",
]

chart_info = {
  "When did you start watching itswill?": {
    "chart-id": "start-watch",
    "chart-type": "doughnut",
    "include-other": False,
    "answer-ordering": [
      "Before 2019",
      "2019",
      "2020",
      "2021",
      "2022",
      "2023",
      "2024",
      "2025",
    ],
  },
  "How did you discover itswill?": {
		"chart-id": "discovery",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "How often do you watch itswill YouTube videos?": {
		"chart-id": "video-freq",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Never",
      "Rarely / When I miss a stream",
      "Often",
      "Every video",
    ]
	},
  "Are you subscribed to itswill on YouTube?": {
		"chart-id": "yt-sub",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "How often do you watch itswill?": {
		"chart-id": "twitch-freq",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Less than once per week",
      "1-2 days per week",
      "3-5 days per week",
      "Every stream",
      "I only watch the vods"
    ]
	},
  "How would you rate your overall experience watching itswill?": {
		"chart-id": "experience",
		"chart-type": "bar",
    "include-other": False,
		"answer-ordering": None
	},
  "Are you subscribed to itswill on Twitch?": {
		"chart-id": "twitch-sub",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "Are you now or have you ever been banned in the itswill Livestream?": {
		"chart-id": "banned",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "What do you primarily watch itswill for?": {
		"chart-id": "primary-content",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What's your favorite type of stream?": {
		"chart-id": "favorite-content",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Variety",
      "Pet Hunting",
      "Leagues",
      "Dead Man Mode"
    ]
	},
  "What types of itswill videos do you typically watch?": {
		"chart-id": "video-types",
		"chart-type": "bar",
    "include-other": False,
	},
  "What is your favorite day-specific stream archetype?": {
		"chart-id": "archetype",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What was your favorite itswill Special Edition Livestream?": {
		"chart-id": "special-edition",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What are your 3 favorite variety games/genres?": {
		"chart-id": "fave-games",
		"chart-type": "bar",
    "include-other": False,
    "alt-labels": lambda label: label if "(" not in label else label[:label.index("(")-1]
	},
  "What is your favorite variety stream of all time?": {
		"chart-id": "fave-stream",
		"chart-type": "bar",
    "max-answers": 32,
    "include-other": False,
	},
  "What stream content would you most like to see come to life?": {
		"chart-id": "stream-ideas",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "How do you typically discover the stream has started?": {
		"chart-id": "stream-start",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "Do you have any Twitch extensions installed?": {
		"chart-id": "extensions",
		"chart-type": "bar",
    "include-other": False,
	},
  "How much do you chat?": {
		"chart-id": "chat-activity",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Lurker",
      "Occasional chatter",
      "Active chatter",
    ]
	},
  "Has the itswill Livestream been a positive force in your life?": {
		"chart-id": "positive-force",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "Are you a member of the itswill Discord server?": {
		"chart-id": "discord-member",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "How many hours do you spend on Twitch per day? (average)": {
		"chart-id": "time-on-twitch",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "<1",
      "1-2",
      "3-4",
      "5-6",
      "7-8",
      "9-10",
      "10+",
    ]
	},
  "Other than itswill, how many streamers do you consistently watch?": {
		"chart-id": "other-streamers",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": None
	},
  "How do you watch Twitch?": {
		"chart-id": "watching-twitch",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "Which RuneScape games do you play?": {
		"chart-id": "rs-games",
		"chart-type": "bar",
    "include-other": False,
		"answer-ordering": [
      "OSRS (main game)",
      "OSRS (leagues)",
      "OSRS (DMM)",
      "RS3",
      "2004Scape",
      "RS Classic",
      "OSRS Private Servers",
      "None",
    ]
	},
  "Do you play Old School RuneScape?": {
		"chart-id": "osrs",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "What is your current age?": {
		"chart-id": "age",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "<18",
      "18-23",
      "24-29",
      "30-35",
      "36-41",
      "42-50",
      "50+",
    ]
	},
  "Are you right or left handed?": {
		"chart-id": "handedness",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "Do you identify as LGBTQ+?": {
		"chart-id": "lgbt",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
      "Unsure",
      "unsure",
    ]
	},
  "What is your gender identity?": {
		"chart-id": "gender",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What is your sexuality?": {
		"chart-id": "sexuality",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What is your current relationship status?": {
		"chart-id": "relationship",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Single",
      "In a relationship",
      "Divorced",
      "It's Complicated"
    ]
	},
  "What country are you from?": {
		"chart-id": "country-origin",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What country do you currently live in?": {
		"chart-id": "country-home",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "Do you have a driver's license?": {
		"chart-id": "drivers-license",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Yes",
      "No",
    ]
	},
  "Highest education level?": {
		"chart-id": "education",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Less than high school",
      "High school",
      "Associates degree",
      "Bachelor's degree",
      "Master's degree",
      "Doctorate",
    ]
	},
  "What is your current employment status?": {
		"chart-id": "employment",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What sports do you watch?": {
		"chart-id": "sports-watched",
		"chart-type": "bar",
    "include-other": False,
	},
  "What sports do you play?": {
		"chart-id": "sports-played",
		"chart-type": "bar",
    "include-other": False,
	},
  "What types of games do you play?": {
		"chart-id": "games-played",
		"chart-type": "bar",
    "include-other": False,
	},
  "What hobbies do you enjoy?": {
		"chart-id": "hobbies",
		"chart-type": "bar",
    "include-other": False,
	},
  "What's your favorite movie?": {
		"chart-id": "fave-movie",
		"chart-type": "bar",
    "include-other": False,
    "max-answers": 30,
	},
  "Have you read a book in the last 5 years?": {
		"chart-id": "reading",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Do you have a pet?": {
		"chart-id": "pet-ownership",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Type of subscription?": {
		"chart-id": "sub-type",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "Prime",
      "Tier 1",
      "Tier 2",
      "Tier 3",
    ]
	},
  "Was your subscription gifted?": {
		"chart-id": "gifted",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "How often do you interact with the itswill Discord?": {
		"chart-id": "discord-interact",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Never", "Infrequently", "Daily" ]
	},
  "What is your current total level in OSRS?": {
		"chart-id": "total-level",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [
      "< 750",
      "750-1250",
      "1251-1500",
      "1501-1750",
      "1751-2000",
      "2001-2100",
      "2101-2200",
      "2201-2276",
      "2277",
    ]
	},
  "What game mode do you spend most of your time playing?": {
		"chart-id": "game-mode",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "How many OSRS accounts do you have?": {
		"chart-id": "num-accounts",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": None
	},
  "Have you ever gotten a fire cape?": {
		"chart-id": "fire-cape",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ]
	},
  "Have you ever gotten an infernal cape?": {
		"chart-id": "infernal-cape",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ]
	},
  "What is your favorite skill in OSRS?": {
		"chart-id": "favorite-skill",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What is your least favorite skill in OSRS?": {
		"chart-id": "least-favorite-skill",
		"chart-type": "doughnut",
    "include-other": False,
	},
  "What OSRS content do you enjoy?": {
		"chart-id": "osrs-content",
		"chart-type": "bar",
    "include-other": False,
	},
  "How do you feel about Sailing?": {
		"chart-id": "sailing",
		"chart-type": "bar",
    "include-other": False,
		"answer-ordering": None
	},
  "What state do you live in?": {
		"chart-id": "state",
		"chart-type": "bar",
    "include-other": False,
    "max-answers": 100,
	},
  "Do you work part or full time?": {
		"chart-id": "full-time",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Part time", "Full time" ],
	},
  "What's your field of work?": {
		"chart-id": "field-of-work",
		"chart-type": "bar",
    "include-other": False,
    "max-answers": 25,
	},
  "Which kind of pets do you have?": {
		"chart-id": "pet-kind",
		"chart-type": "bar",
    "include-other": False,
	},
  "Who would you like to see itswill collaborate with? (optional)": {
		"chart-id": "collab",
		"chart-type": "bar",
    "include-other": False,
	},
  "What games would you like to see itswill play? (optional)": {
		"chart-id": "game-ideas",
		"chart-type": "bar",
    "include-other": False,
	},
  "What's your favorite emote? (optional)": {
		"chart-id": "emote",
		"chart-type": "bar",
    "include-other": False,
	},
  "Who's your favorite chatter? (optional)": {
		"chart-id": "fave-chatter",
		"chart-type": "bar",
    "include-other": False,
	},
  "When should the 15 minute buffer start?": {
		"chart-id": "buffer",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "5:00:01 (5:15:01 should be late)", "5:01:00 (5:16:00 should be late)", ]
	},
  "Who's your favorite mod? (optional)": {
		"chart-id": "fave-mod",
		"chart-type": "bar",
    "include-other": False,
    "alt-labels": lambda label: "AMAB" if label.startswith("None") else label
	},
  "Is hot chocolate a candy?": {
		"chart-id": "hot-chocolate",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Is \"cock and balls\" redundant? Are the balls included in the definition of cock?": {
		"chart-id": "cock-n-balls",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Have you ever worn pajama pants outside your house?": {
		"chart-id": "pajamas",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Have you ever cheated on a test?": {
		"chart-id": "cheaters",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Have you ever stolen something from the supermarket?": {
		"chart-id": "theft",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Do you think aliens exist?": {
		"chart-id": "aliens",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Do you think ghosts exist?": {
		"chart-id": "ghosts",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "Are you a furry?": {
		"chart-id": "furry",
		"chart-type": "doughnut",
    "include-other": False,
		"answer-ordering": [ "Yes", "No" ],
	},
  "How tall are you?": {
		"chart-id": "height",
		"chart-type": "bar",
    "include-other": False,
		"answer-ordering": [
      "< 5' (< 152cm)",
      "5'-5'3\" (152cm-160cm)",
      "5'4\"-5'7\" (162cm-170cm)",
      "5'8\"-5'11 (172cm-180cm)",
      "6'-6'3\" (183cm-190cm)",
      "> 6'3 (> 190cm)",
    ]
	},
  "What's your number? Be honest.": {
		"chart-id": "norwood",
		"chart-type": "bar",
    "include-other": False,
		"answer-ordering": None
	},
}

open_input_delim = re.compile(r";")

def standardize_answer(ans : str):
  simplified = ans
  simplified = simplified.strip()
  simplified = simplified.replace(".", "").replace(",", "").replace("-", "").replace("&", "and").replace("the", "").replace("The", "").replace(" ", "").replace("\u2019", "").replace("'", "")
  simplified = simplified.lower()
  
  return simplified

def tally_item(d : dict, key : typing.Union[str, int], incr = 1, keep_none = False):
  if type(key) == str:
    key = key.encode().decode('UTF-8').strip()
      
    if key.lower() in ["nan", "", "na"]:
      if not keep_none:
        return
      else:
        key = "None"
    
  if key not in d:
    d[key] = incr
  else:
    d[key] += incr
    
def float_rgb_to_hex(color : typing.Tuple[int, int, int]):
  return '#%02x%02x%02x' % (int(255*color[0]), int(255*color[1]), int(255*color[2]))
    
def count_results(dataframe : pd.DataFrame, start_index = 0, input_results = None) -> dict:
  results = {} if input_results is None else input_results
  for key in dataframe.keys():
    old_key = key
    key = key.strip()
    column : pd.Series = dataframe[old_key]
    if key not in results:
      results[key] = { "responses": 0, "answers": { } }
    
    for item in column[start_index:]:
      if pd.isnull(item):
        if key in keep_none:
          item = "None"
        else:
          continue
      
      tally_item(results[key], "responses")
      
      if key in skip_question:
        continue
      elif key in multi_answer_questions:
        for indiv in item.split(";"):
          tally_item(results[key]["answers"], indiv, keep_none = (key in keep_none))
      elif key in open_input_questions:
        item = item.replace("Drawing / Art", "Drawing or Art")
        for indiv in re.split(open_input_delim, item):
          if indiv in [";",",","/"]:
            continue
          
          tally_item(results[key]["answers"], indiv)
      else:
        if type(item) == float and item == int(item):
          item = str(int(item))
        tally_item(results[key]["answers"], str(item))
    
    results[key]["answers"] = {k: v for k, v in sorted(results[key]["answers"].items(), key = lambda kvp: kvp[1], reverse = True)}
  return results
    
def condense_results(results : dict) -> dict:
  condensed_results = {}
  answer_map = {}
  for key in results.keys():
    old_key = key
    key = key.strip()
    if key in skip_question:
      continue
    condensed_results[key] = { "responses": results[old_key]["responses"], "answers": { } }
    
    for answer, count in results[old_key]["answers"].items():
      answer = "Doctorate" if old_key == "Highest education level?" and answer == "PhD" else answer
      if key in multi_answer_questions:
        for indiv in answer.split(";"):
          if indiv in [";"]:
            continue
          
          simp_form = standardize_answer(indiv)
          if simp_form == "":
            continue
          if simp_form not in answer_map:
            answer_map[simp_form] = indiv
            
          tally_item(condensed_results[key]["answers"], answer_map[simp_form], count, keep_none = True)
      elif key in open_input_questions:
        for indiv in re.split(open_input_delim, answer):
          if indiv in [";", "/"]:
            continue
          
          simp_form = standardize_answer(indiv)
          if simp_form == "":
            continue
          if simp_form not in answer_map:
            answer_map[simp_form] = indiv
            
          tally_item(condensed_results[key]["answers"], answer_map[simp_form], count)
      else:
        simp_form = answer if type(answer) is not str else standardize_answer(answer)
        if simp_form not in answer_map:
          answer_map[simp_form] = answer
          
        tally_item(condensed_results[key]["answers"], answer_map[simp_form], count)
    
    condensed_results[key]["answers"] = {k: v for k, v in sorted(condensed_results[key]["answers"].items(), key = lambda kvp: kvp[1], reverse = True)}
    
  return condensed_results

def generate_chart_data(results : dict):
  chart_data = { "charts": {} }
  for key in results.keys():
    cinfo = chart_info[key]
    
    max_len = 20 if cinfo["chart-type"] == "bar" else 12
    
    if "max-answers" in cinfo:
      max_len = cinfo["max-answers"]
    
    if "answer-ordering" in cinfo:
      ordering = cinfo["answer-ordering"]
      results[key]["answers"] = {k: v for k, v in sorted(results[key]["answers"].items(), key = lambda kvp: kvp[0] if not ordering else ordering.index(kvp[0]))}
      
    dataset_len = min(max_len, len(results[key]["answers"].keys()))
    include_others = (len(results[key]["answers"].keys()) > max_len)
    
    def generate_color_list(num_colors):
      start_index = random.randint(0, len(color_list) - 1)
      rotated_list = color_list[start_index:] + color_list[:start_index]
      return [float_rgb_to_hex(colorsys.hsv_to_rgb((c[0]/360.0), c[1], c[2])) for c in rotated_list[:num_colors]]
      # color_list = []
      # h_val = random.randint(0, 255)
      # for i in range(0, num_colors):
      #   h_val += random.randint(56, 112)
      #   h_val %= 255
      #   
      #   color_list.append(float_rgb_to_hex(colorsys.hsv_to_rgb((h_val / 255.0), 0.7, 0.95)))
      # return color_list
    
    labels = list(results[key]["answers"].keys())[:dataset_len]
    
    if "alt-labels" in cinfo:
      labels = [cinfo["alt-labels"](label) for label in labels]
    
    bgColors = generate_color_list(dataset_len)
    data = list(results[key]["answers"].values())[:dataset_len]
    
    if cinfo["include-other"] and include_others:
      labels.pop()
      labels.append("Other")
      data.pop()
      data.append(sum(list(results[key]["answers"].values())[dataset_len:]))
    
    chart_data["charts"][cinfo["chart-id"]] = {
      "title": f"{key.replace("(optional)", "").strip()}",
      "subtitle": f"({humanize.intcomma(results[key]["responses"])} responses)",
      "data": {
        "type": cinfo["chart-type"],
        "data": {
          "labels": labels,
          "datasets": [{
            "label": '',
            "backgroundColor": bgColors,
            "responses": results[key]["responses"],
            "data": data,
          }]
        },
        "options": {
          "responsive": True,
          "maintainAspectRatio": False,
          "plugins": {
            "legend": {
              "display": (cinfo["chart-type"] == "doughnut"),
              "position": 'right',
            }
          }
        }
      }
    }
      
  return chart_data
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  
  subparser = parser.add_subparsers(help = "sub-commands help")
  
  sp = subparser.add_parser("count")
  sp.set_defaults(cmd = 'count')
  sp.add_argument("csv_path")
  sp.add_argument("out_path", default = "results.json")
  sp.add_argument("--skip-condense", "-s", action = 'store_true')
  sp.add_argument("--start-at", "-c", default = 0, type = int)
  sp.add_argument("--append-file", "-i")
  
  sp = subparser.add_parser("condense")
  sp.set_defaults(cmd = 'condense')
  sp.add_argument("json_path")
  sp.add_argument("out_path", default = "results.json")
  
  sp = subparser.add_parser("charts")
  sp.set_defaults(cmd = 'charts')
  sp.add_argument("json_path")
  sp.add_argument("out_path", default = "charts.json")
  
  args = parser.parse_args()
  
  if args.cmd == 'count':
    dataframe : pd.DataFrame = pd.read_csv(args.csv_path)
    dataframe.drop("Timestamp", axis = 1, inplace = True)
    
    input_results = {}
    if args.append_file:
      with open(args.append_file, 'r', encoding = "UTF-8") as fp:
        input_results = json.load(fp)
    
    counted = count_results(dataframe, start_index = args.start_at, input_results = input_results)
    
    if not args.skip_condense:
      counted = condense_results(counted)

    with open(args.out_path, 'w') as fp:
      json.dump(counted, fp, indent = 2, ensure_ascii = False)
  
  elif args.cmd == 'condense':
    with open(args.json_path, 'r', encoding = 'UTF-8') as fp:
      input_results = json.load(fp)
    
    counted = condense_results(input_results)

    with open(args.out_path, 'w', encoding = "UTF-8") as fp:
      json.dump(counted, fp, indent = 2, ensure_ascii = False)
  
  elif args.cmd == 'charts':
    with open(args.json_path, 'r', encoding = "UTF-8") as fp:
      input_results = json.load(fp)
    
    charts = generate_chart_data(input_results)

    with open(args.out_path, 'w', encoding = "UTF-8") as fp:
      json.dump(charts, fp, indent = 2, ensure_ascii = False)