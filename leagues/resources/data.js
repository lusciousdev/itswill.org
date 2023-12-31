var data = (function (exports) {
  var choices = {
    "regions": {
      "pretty_name": "Regions",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League"
        },
        {
          "name": "Asgarnia",
          "image": "https://oldschool.runescape.wiki/images/Asgarnia_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Asgarnia"
        },
        {
          "name": "Fremennik",
          "image": "https://oldschool.runescape.wiki/images/Fremennik_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Fremennik"
        },
        {
          "name": "Kandarin",
          "image": "https://oldschool.runescape.wiki/images/Kandarin_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Kandarin"
        },
        {
          "name": "Desert",
          "image": "https://oldschool.runescape.wiki/images/Desert_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Desert"
        },
        {
          "name": "Morytania",
          "image": "https://oldschool.runescape.wiki/images/Morytania_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Morytania"
        },
        {
          "name": "Tirannwn",
          "image": "https://oldschool.runescape.wiki/images/Tirannwn_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Tirannwn"
        },
        {
          "name": "Wilderness",
          "image": "https://oldschool.runescape.wiki/images/Wilderness_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Wilderness"
        },
        {
          "name": "Kourend",
          "image": "https://oldschool.runescape.wiki/images/Kourend_Area_Badge.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Areas/Kourend"
        }
      ]
    },
    "tier1": {
      "pretty_name": "Tier 1",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Endless Harvest",
          "image": "https://oldschool.runescape.wiki/images/thumb/Endless_Harvest_detail.png/100px-Endless_Harvest_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Endless_Harvest"
        },
        {
          "name": "Production Prodigy",
          "image": "https://oldschool.runescape.wiki/images/thumb/Production_Prodigy_detail.png/100px-Production_Prodigy_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Production_Prodigy"
        },
        {
          "name": "Trickster",
          "image": "https://oldschool.runescape.wiki/images/thumb/Trickster_detail.png/100px-Trickster_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trickster"
        }
      ]
    },
    "tier2": {
      "pretty_name": "Tier 2",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Globetrotter",
          "image": "https://oldschool.runescape.wiki/images/thumb/Globetrotter_detail.png/100px-Globetrotter_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Globetrotter"
        },
        {
          "name": "Fairy's Flight",
          "image": "https://oldschool.runescape.wiki/images/thumb/Fairy%27s_Flight_detail.png/100px-Fairy%27s_Flight_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Fairy%27s_Flight"
        }
      ]
    },
    "tier3": {
      "pretty_name": "Tier 3",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Banker's Note",
          "image": "https://oldschool.runescape.wiki/images/thumb/Banker%27s_Note_detail.png/100px-Banker%27s_Note_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Banker%27s_Note"
        },
        {
          "name": "Fire Sale",
          "image": "https://oldschool.runescape.wiki/images/thumb/Fire_Sale_detail.png/100px-Fire_Sale_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Fire_Sale"
        }
      ]
    },
    "tier4": {
      "pretty_name": "Tier 4",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Archer's Embrace",
          "image": "https://oldschool.runescape.wiki/images/thumb/Archer%27s_Embrace_detail.png/100px-Archer%27s_Embrace_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Archer%27s_Embrace"
        },
        {
          "name": "Brawler's Resolve",
          "image": "https://oldschool.runescape.wiki/images/thumb/Brawler%27s_Resolve_detail.png/100px-Brawler%27s_Resolve_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Brawler%27s_Resolve"
        },
        {
          "name": "Superior Sorcerer",
          "image": "https://oldschool.runescape.wiki/images/thumb/Superior_Sorcerer_detail.png/100px-Superior_Sorcerer_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Superior_Sorcerer"
        }
      ]
    },
    "tier5": {
      "pretty_name": "Tier 5",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Treasure Seeker",
          "image": "https://oldschool.runescape.wiki/images/thumb/Treasure_Seeker_detail.png/100px-Treasure_Seeker_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Treasure_Seeker"
        },
        {
          "name": "Bloodthirsty",
          "image": "https://oldschool.runescape.wiki/images/thumb/Bloodthirsty_detail.png/100px-Bloodthirsty_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Bloodthirsty"
        },
        {
          "name": "Infernal Gathering",
          "image": "https://oldschool.runescape.wiki/images/thumb/Infernal_Gathering_detail.png/100px-Infernal_Gathering_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Infernal_Gathering"
        }
      ]
    },
    "tier6": {
      "pretty_name": "Tier 6",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Equilibrium",
          "image": "https://oldschool.runescape.wiki/images/thumb/Equilibrium_detail.png/100px-Equilibrium_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Equilibrium"
        },
        {
          "name": "Farmer's Fortune",
          "image": "https://oldschool.runescape.wiki/images/thumb/Farmer%27s_Fortune_detail.png/100px-Farmer%27s_Fortune_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Farmer%27s_Fortune"
        },
        {
          "name": "Ruinous Powers",
          "image": "https://oldschool.runescape.wiki/images/thumb/Ruinous_Powers_%28relic%29_detail.png/100px-Ruinous_Powers_%28relic%29_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Ruinous_Powers_(relic)"
        }
      ]
    },
    "tier7": {
      "pretty_name": "Tier 7",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Soul Stealer",
          "image": "https://oldschool.runescape.wiki/images/thumb/Soul_Stealer_detail.png/100px-Soul_Stealer_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Soul_Stealer"
        },
        {
          "name": "Weapon Master",
          "image": "https://oldschool.runescape.wiki/images/thumb/Weapon_Master_detail.png/100px-Weapon_Master_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Weapon_Master"
        },
        {
          "name": "Berserker",
          "image": "https://oldschool.runescape.wiki/images/thumb/Berserker_detail.png/100px-Berserker_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Berserker"
        }
      ]
    },
    "tier8": {
      "pretty_name": "Tier 8",
      "choices": [
        {
          "name": "Locked",
          "image": "./resources/locked.png",
          "wiki": "https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Relics"
        },
        {
          "name": "Executioner",
          "image": "https://oldschool.runescape.wiki/images/thumb/Executioner_detail.png/100px-Executioner_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Executioner"
        },
        {
          "name": "Undying Retribution",
          "image": "https://oldschool.runescape.wiki/images/thumb/Undying_Retribution_detail.png/100px-Undying_Retribution_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Undying_Retribution"
        },
        {
          "name": "Guardian",
          "image": "https://oldschool.runescape.wiki/images/thumb/Guardian_detail.png/100px-Guardian_detail.png",
          "wiki": "https://oldschool.runescape.wiki/w/Guardian_(Trailblazer_Reloaded)"
        },
      ]
    }
  };

  exports.choices = choices;

  return exports;

})({});