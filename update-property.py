"""
update-property.py  ─  Bake Australian property data into data/property.json
════════════════════════════════════════════════════════════════════════════

Source: SQM Research free chart pages (sqmresearch.com.au). Each page embeds
its full series as a JS literal:  var data = [{...}, ...]  — parsed here with
a bracket-balance scan + json.loads.

Per region we fetch 5 pages:
  asking-property-prices  weekly  {date, houses_all, houses_3, units_all, units_2, combined}
  weekly-rents            weekly  same keys
  rental-yield            weekly  {date, houses_all, houses_3, units_all, units_2}
  vacancy-rates           monthly {year, month, listings, properties, vr}
  total-property-listings monthly {year, month, r30, r60, r90, r180, r180p}

Capitals use ?region=<slug>&type=c (city-wide index); towns use ?postcode=NNNN
(canonical postcode); National uses ?national=1; Capital Avg uses ?avg=1.

Usage:
    python update-property.py            # bake everything (~5 min, 0.5s/req)
    python update-property.py SYD NEW    # bake only listed region codes

Merge semantics: regions that fail today keep yesterday's data (same policy
as update-prices.py). Output written atomically (tmp + os.replace).

NOTE: SQM data is published for personal reference. Attribute SQM on the
board; do not resell.
"""

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

BASE = "https://sqmresearch.com.au/property/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "property.json")
# Full untrimmed series for backtesting. NOT fetched by the board and NOT
# committed (gitignored) — it is ~4 MB and would bloat git history weekly.
HIST_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "property-history.json")
SLEEP = 0.5
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ── Region list ──────────────────────────────────────────────────────────────
# code: (name, state, kind, param)
#   kind 'city'     → region=<param>&type=c
#   kind 'postcode' → postcode=<param>
#   kind 'national' → national=1     kind 'avg' → avg=1
REGIONS = {
    # National
    "AUS":  ("Australia (National)", "NAT", "national", ""),
    "CAP8": ("Capital City Average", "NAT", "avg", ""),
    # NSW
    "SYD": ("Sydney",         "NSW", "city",     "nsw-Sydney"),
    "NEW": ("Newcastle",      "NSW", "postcode", "2300"),
    "WOL": ("Wollongong",     "NSW", "postcode", "2500"),
    "GOS": ("Central Coast (Gosford)", "NSW", "postcode", "2250"),
    "PMQ": ("Port Macquarie", "NSW", "postcode", "2444"),
    "CFS": ("Coffs Harbour",  "NSW", "postcode", "2450"),
    "TMW": ("Tamworth",       "NSW", "postcode", "2340"),
    "WGA": ("Wagga Wagga",    "NSW", "postcode", "2650"),
    "ALB": ("Albury",         "NSW", "postcode", "2640"),
    "DBO": ("Dubbo",          "NSW", "postcode", "2830"),
    "ORG": ("Orange",         "NSW", "postcode", "2800"),
    "BXT": ("Bathurst",       "NSW", "postcode", "2795"),
    "BYR": ("Byron Bay",      "NSW", "postcode", "2481"),
    "LIS": ("Lismore",        "NSW", "postcode", "2480"),
    "BNA": ("Ballina",        "NSW", "postcode", "2478"),
    "TWH": ("Tweed Heads",    "NSW", "postcode", "2485"),
    "GFN": ("Grafton",        "NSW", "postcode", "2460"),
    "ARM": ("Armidale",       "NSW", "postcode", "2350"),
    "GBN": ("Goulburn",       "NSW", "postcode", "2580"),
    "QBN": ("Queanbeyan",     "NSW", "postcode", "2620"),
    "NRA": ("Nowra",          "NSW", "postcode", "2541"),
    "BAY": ("Batemans Bay",   "NSW", "postcode", "2536"),
    "ULL": ("Ulladulla",      "NSW", "postcode", "2539"),
    "CES": ("Cessnock",       "NSW", "postcode", "2325"),
    "MTL": ("Maitland",       "NSW", "postcode", "2320"),
    "SNG": ("Singleton",      "NSW", "postcode", "2330"),
    "MUS": ("Muswellbrook",   "NSW", "postcode", "2333"),
    "TRE": ("Taree",          "NSW", "postcode", "2430"),
    "FOR": ("Forster",        "NSW", "postcode", "2428"),
    "GFF": ("Griffith",       "NSW", "postcode", "2680"),
    "BHL": ("Broken Hill",    "NSW", "postcode", "2880"),
    "CWA": ("Cowra",          "NSW", "postcode", "2794"),
    "MDG": ("Mudgee",         "NSW", "postcode", "2850"),
    "KAT": ("Katoomba",       "NSW", "postcode", "2780"),
    "BWL": ("Bowral",         "NSW", "postcode", "2576"),
    "RSH": ("Rouse Hill", "NSW", "postcode", "2155"),
    "MDP": ("Marsden Park", "NSW", "postcode", "2765"),
    "SCH": ("Schofields", "NSW", "postcode", "2762"),
    "LPT": ("Leppington", "NSW", "postcode", "2179"),
    "GRC": ("Gregory Hills", "NSW", "postcode", "2557"),
    "NRL": ("Narellan", "NSW", "postcode", "2567"),
    "PIC": ("Picton", "NSW", "postcode", "2571"),
    "MTG2": ("Mittagong", "NSW", "postcode", "2575"),
    "MSV": ("Moss Vale", "NSW", "postcode", "2577"),
    "WYG": ("Wyong", "NSW", "postcode", "2259"),
    "MST": ("Morisset", "NSW", "postcode", "2264"),
    "RYT": ("Raymond Terrace", "NSW", "postcode", "2324"),
    "CHW": ("Charlestown", "NSW", "postcode", "2290"),
    "BLM": ("Belmont (NSW)", "NSW", "postcode", "2280"),
    "TOR": ("Toronto", "NSW", "postcode", "2283"),
    "MDW": ("Medowie", "NSW", "postcode", "2318"),
    "MRM": ("Merimbula", "NSW", "postcode", "2548"),
    "JND": ("Jindabyne", "NSW", "postcode", "2627"),
    "GUN": ("Gunnedah", "NSW", "postcode", "2380"),
    "YMB": ("Yamba", "NSW", "postcode", "2464"),
    # Large-population Sydney sub-markets + remaining big regional centres
    "PRA": ("Parramatta",     "NSW", "postcode", "2150"),
    "BKT": ("Blacktown",      "NSW", "postcode", "2148"),
    "PNR": ("Penrith",        "NSW", "postcode", "2750"),
    "LVP": ("Liverpool",      "NSW", "postcode", "2170"),
    "CBT": ("Campbelltown",   "NSW", "postcode", "2560"),
    "BKS": ("Bankstown",      "NSW", "postcode", "2200"),
    "FFD": ("Fairfield",      "NSW", "postcode", "2165"),
    "HNB": ("Hornsby",        "NSW", "postcode", "2077"),
    "CSW": ("Chatswood",      "NSW", "postcode", "2067"),
    "RYD": ("Ryde",           "NSW", "postcode", "2112"),
    "HVL": ("Hurstville",     "NSW", "postcode", "2220"),
    "SLD": ("Sutherland",     "NSW", "postcode", "2232"),
    "MLY": ("Manly",          "NSW", "postcode", "2095"),
    "BND": ("Bondi",          "NSW", "postcode", "2026"),
    "CHL": ("Castle Hill",    "NSW", "postcode", "2154"),
    "CMD": ("Camden",         "NSW", "postcode", "2570"),
    "RCH": ("Richmond",       "NSW", "postcode", "2753"),
    "KIA": ("Kiama",          "NSW", "postcode", "2533"),
    "SHB": ("Shellharbour",   "NSW", "postcode", "2529"),
    "NBY": ("Nelson Bay",     "NSW", "postcode", "2315"),
    "COO": ("Cooma",          "NSW", "postcode", "2630"),
    "BEG": ("Bega",           "NSW", "postcode", "2550"),
    "MOR": ("Moree",          "NSW", "postcode", "2400"),
    "INV": ("Inverell",       "NSW", "postcode", "2360"),
    "PKS": ("Parkes",         "NSW", "postcode", "2870"),
    "LTG": ("Lithgow",        "NSW", "postcode", "2790"),
    "TOM": ("Culburra / Jervis Bay / Shoalhaven Coast", "NSW", "postcode", "2540"),
    "CRN": ("Cronulla", "NSW", "postcode", "2230"),
    "HBH": ("Helensburgh", "NSW", "postcode", "2508"),
    "THR": ("Thirroul", "NSW", "postcode", "2515"),
    "CRM": ("Corrimal", "NSW", "postcode", "2518"),
    "FMD": ("Fairy Meadow", "NSW", "postcode", "2519"),
    "WWG": ("Warrawong", "NSW", "postcode", "2502"),
    "PKB": ("Port Kembla", "NSW", "postcode", "2505"),
    "DPT2": ("Dapto", "NSW", "postcode", "2530"),
    "ALP": ("Albion Park", "NSW", "postcode", "2527"),
    "WRL": ("Warilla", "NSW", "postcode", "2528"),
    "GRG": ("Gerringong", "NSW", "postcode", "2534"),
    "BRY": ("Berry", "NSW", "postcode", "2535"),
    "MLT2": ("Milton", "NSW", "postcode", "2538"),
    "MRY2": ("Moruya", "NSW", "postcode", "2537"),
    "NRM": ("Narooma", "NSW", "postcode", "2546"),
    "PMB": ("Pambula", "NSW", "postcode", "2549"),
    "EDN": ("Eden", "NSW", "postcode", "2551"),
    # VIC
    "MEL": ("Melbourne",      "VIC", "city",     "vic-Melbourne"),
    "GEE": ("Geelong",        "VIC", "postcode", "3220"),
    "BAL": ("Ballarat",       "VIC", "postcode", "3350"),
    "BEN": ("Bendigo",        "VIC", "postcode", "3550"),
    "SHP": ("Shepparton",     "VIC", "postcode", "3630"),
    "MIL": ("Mildura",        "VIC", "postcode", "3500"),
    "WRN": ("Warrnambool",    "VIC", "postcode", "3280"),
    "TRA": ("Traralgon",      "VIC", "postcode", "3844"),
    "WOD": ("Wodonga",        "VIC", "postcode", "3690"),
    "WGT": ("Wangaratta",     "VIC", "postcode", "3677"),
    "HSM": ("Horsham",        "VIC", "postcode", "3400"),
    "SLE": ("Sale",           "VIC", "postcode", "3850"),
    "BRN": ("Bairnsdale",     "VIC", "postcode", "3875"),
    "MWL": ("Morwell",        "VIC", "postcode", "3840"),
    "CLC": ("Colac",          "VIC", "postcode", "3250"),
    "HML": ("Hamilton",       "VIC", "postcode", "3300"),
    "ARA": ("Ararat",         "VIC", "postcode", "3377"),
    "CTM": ("Castlemaine",    "VIC", "postcode", "3450"),
    "ECH": ("Echuca",         "VIC", "postcode", "3564"),
    "SWH": ("Swan Hill",      "VIC", "postcode", "3585"),
    "BNL": ("Benalla",        "VIC", "postcode", "3672"),
    "SEY": ("Seymour",        "VIC", "postcode", "3660"),
    "TQY": ("Torquay",        "VIC", "postcode", "3228"),
    "OCG": ("Ocean Grove",    "VIC", "postcode", "3226"),
    "SUN": ("Sunbury",        "VIC", "postcode", "3429"),
    "MLT": ("Melton",         "VIC", "postcode", "3337"),
    "PKM": ("Pakenham",       "VIC", "postcode", "3810"),
    "CRB": ("Cranbourne",     "VIC", "postcode", "3977"),
    "FKN": ("Frankston",      "VIC", "postcode", "3199"),
    "WBE": ("Werribee",       "VIC", "postcode", "3030"),
    "WRG": ("Warragul",       "VIC", "postcode", "3820"),
    "WYV": ("Wyndham Vale", "VIC", "postcode", "3024"),
    "CRS": ("Caroline Springs", "VIC", "postcode", "3023"),
    "SSH": ("Sunshine", "VIC", "postcode", "3020"),
    "STA": ("St Albans", "VIC", "postcode", "3021"),
    "MRD2": ("Mernda", "VIC", "postcode", "3754"),
    "SMR": ("South Morang", "VIC", "postcode", "3752"),
    "ELT": ("Eltham", "VIC", "postcode", "3095"),
    "CRY": ("Croydon", "VIC", "postcode", "3136"),
    "BOR": ("Boronia", "VIC", "postcode", "3155"),
    "RWV": ("Rowville", "VIC", "postcode", "3178"),
    "CLY": ("Clayton", "VIC", "postcode", "3168"),
    "SPV": ("Springvale", "VIC", "postcode", "3171"),
    "KYB": ("Keysborough", "VIC", "postcode", "3173"),
    "CHS": ("Chelsea", "VIC", "postcode", "3196"),
    "CRD2": ("Carrum Downs", "VIC", "postcode", "3201"),
    "LNG": ("Langwarrin", "VIC", "postcode", "3910"),
    "CWS": ("Cowes", "VIC", "postcode", "3922"),
    "BCM": ("Bacchus Marsh", "VIC", "postcode", "3340"),
    "GSB": ("Gisborne", "VIC", "postcode", "3437"),
    "YWG": ("Yarrawonga", "VIC", "postcode", "3730"),
    # Large-population Melbourne sub-markets + remaining regional centres
    "DDG": ("Dandenong",      "VIC", "postcode", "3175"),
    "BXH": ("Box Hill",       "VIC", "postcode", "3128"),
    "GWV": ("Glen Waverley",  "VIC", "postcode", "3150"),
    "RGW": ("Ringwood",       "VIC", "postcode", "3134"),
    "BWK": ("Berwick",        "VIC", "postcode", "3806"),
    "NRW": ("Narre Warren",   "VIC", "postcode", "3805"),
    "TRN": ("Tarneit",        "VIC", "postcode", "3029"),
    "CRG": ("Craigieburn",    "VIC", "postcode", "3064"),
    "EPP": ("Epping (VIC)",   "VIC", "postcode", "3076"),
    "GRB": ("Greensborough",  "VIC", "postcode", "3088"),
    "PRS": ("Preston",        "VIC", "postcode", "3072"),
    "FTS": ("Footscray",      "VIC", "postcode", "3011"),
    "STK": ("St Kilda",       "VIC", "postcode", "3182"),
    "BTN": ("Brighton",       "VIC", "postcode", "3186"),
    "CMB": ("Camberwell",     "VIC", "postcode", "3124"),
    "DNC": ("Doncaster",      "VIC", "postcode", "3108"),
    "MRN": ("Mornington",     "VIC", "postcode", "3931"),
    "RSD": ("Rosebud",        "VIC", "postcode", "3939"),
    "WTG": ("Wonthaggi",      "VIC", "postcode", "3995"),
    "KYN": ("Kyneton",        "VIC", "postcode", "3444"),
    "PLD": ("Portland",       "VIC", "postcode", "3305"),
    "LEO": ("Leongatha",      "VIC", "postcode", "3953"),
    "SEA": ("Seaford (VIC)",  "VIC", "postcode", "3198"),
    # QLD
    "BNE": ("Brisbane",       "QLD", "city",     "qld-Brisbane"),
    "GC":  ("Gold Coast (Southport)",      "QLD", "postcode", "4215"),
    "SC":  ("Sunshine Coast (Maroochydore)", "QLD", "postcode", "4558"),
    "CNS": ("Cairns",         "QLD", "postcode", "4870"),
    "TSV": ("Townsville",     "QLD", "postcode", "4810"),
    "TWB": ("Toowoomba",      "QLD", "postcode", "4350"),
    "MKY": ("Mackay",         "QLD", "postcode", "4740"),
    "ROK": ("Rockhampton",    "QLD", "postcode", "4700"),
    "BDB": ("Bundaberg",      "QLD", "postcode", "4670"),
    "HVB": ("Hervey Bay",     "QLD", "postcode", "4655"),
    "GLT": ("Gladstone",      "QLD", "postcode", "4680"),
    "MBH": ("Maryborough",    "QLD", "postcode", "4650"),
    "GYM": ("Gympie",         "QLD", "postcode", "4570"),
    "YEP": ("Yeppoon",        "QLD", "postcode", "4703"),
    "EMD": ("Emerald",        "QLD", "postcode", "4720"),
    "WWK": ("Warwick",        "QLD", "postcode", "4370"),
    "DAL": ("Dalby",          "QLD", "postcode", "4405"),
    "KGY": ("Kingaroy",       "QLD", "postcode", "4610"),
    "ROM": ("Roma",           "QLD", "postcode", "4455"),
    "CHT": ("Charters Towers", "QLD", "postcode", "4820"),
    "AYR": ("Ayr",            "QLD", "postcode", "4807"),
    "INF": ("Innisfail",      "QLD", "postcode", "4860"),
    "ATH": ("Atherton",       "QLD", "postcode", "4883"),
    "MRB": ("Mareeba",        "QLD", "postcode", "4880"),
    "PTD": ("Port Douglas",   "QLD", "postcode", "4877"),
    "BWN": ("Bowen",          "QLD", "postcode", "4805"),
    "AIR": ("Airlie Beach",   "QLD", "postcode", "4802"),
    "CLD": ("Caloundra",      "QLD", "postcode", "4551"),
    "NSA": ("Noosa Heads",    "QLD", "postcode", "4567"),
    "CGT": ("Coolangatta",    "QLD", "postcode", "4225"),
    "IPS": ("Ipswich",        "QLD", "postcode", "4305"),
    "RCF": ("Redcliffe",      "QLD", "postcode", "4020"),
    "CBL": ("Caboolture",     "QLD", "postcode", "4510"),
    "KLG": ("Kallangur", "QLD", "postcode", "4503"),
    "DCB": ("Deception Bay", "QLD", "postcode", "4508"),
    "MNH": ("Mango Hill", "QLD", "postcode", "4509"),
    "BPG": ("Burpengary", "QLD", "postcode", "4505"),
    "NRB": ("Narangba", "QLD", "postcode", "4504"),
    "ABC": ("Albany Creek", "QLD", "postcode", "4035"),
    "ASP2": ("Aspley", "QLD", "postcode", "4034"),
    "IND": ("Indooroopilly", "QLD", "postcode", "4068"),
    "SNB": ("Sunnybank", "QLD", "postcode", "4109"),
    "CLV2": ("Calamvale", "QLD", "postcode", "4116"),
    "BRP": ("Browns Plains", "QLD", "postcode", "4118"),
    "MSD": ("Marsden", "QLD", "postcode", "4132"),
    "JMB": ("Jimboomba", "QLD", "postcode", "4280"),
    "ORM": ("Ormeau", "QLD", "postcode", "4208"),
    "PIM": ("Pimpama", "QLD", "postcode", "4209"),
    "HLV": ("Helensvale", "QLD", "postcode", "4212"),
    "BLH": ("Burleigh Heads", "QLD", "postcode", "4220"),
    "PLB": ("Palm Beach (QLD)", "QLD", "postcode", "4221"),
    "MLB": ("Mooloolaba", "QLD", "postcode", "4557"),
    "GTT": ("Gatton", "QLD", "postcode", "4343"),
    # Large-population SEQ sub-markets + remaining regional centres
    "SFP": ("Surfers Paradise", "QLD", "postcode", "4217"),
    "RBN": ("Robina",         "QLD", "postcode", "4226"),
    "NRG": ("Nerang",         "QLD", "postcode", "4211"),
    "LGN": ("Logan Central",  "QLD", "postcode", "4114"),
    "SPR": ("Springfield",    "QLD", "postcode", "4300"),
    "CHM": ("Chermside",      "QLD", "postcode", "4032"),
    "CRD": ("Carindale",      "QLD", "postcode", "4152"),
    "STP": ("Strathpine",     "QLD", "postcode", "4500"),
    "CLV": ("Cleveland",      "QLD", "postcode", "4163"),
    "BNH": ("Beenleigh",      "QLD", "postcode", "4207"),
    "BUD": ("Buderim",        "QLD", "postcode", "4556"),
    "NMB": ("Nambour",        "QLD", "postcode", "4560"),
    "BRB": ("Bribie Island",  "QLD", "postcode", "4507"),
    "MTI": ("Mount Isa",      "QLD", "postcode", "4825"),
    "GDW": ("Goondiwindi",    "QLD", "postcode", "4390"),
    "STN": ("Stanthorpe",     "QLD", "postcode", "4380"),
    # WA
    "PER": ("Perth",          "WA", "city",     "wa-Perth"),
    "MDH": ("Mandurah",       "WA", "postcode", "6210"),
    "BUN": ("Bunbury",        "WA", "postcode", "6230"),
    "GER": ("Geraldton",      "WA", "postcode", "6530"),
    "KAL": ("Kalgoorlie",     "WA", "postcode", "6430"),
    "ALY": ("Albany",         "WA", "postcode", "6330"),
    "BSN": ("Busselton",      "WA", "postcode", "6280"),
    "BRM": ("Broome",         "WA", "postcode", "6725"),
    "KTA": ("Karratha",       "WA", "postcode", "6714"),
    "PHD": ("Port Hedland",   "WA", "postcode", "6721"),
    "ESP": ("Esperance",      "WA", "postcode", "6450"),
    "NTH": ("Northam",        "WA", "postcode", "6401"),
    "MGR": ("Margaret River", "WA", "postcode", "6285"),
    "COL": ("Collie",         "WA", "postcode", "6225"),
    "MJP": ("Manjimup",       "WA", "postcode", "6258"),
    "NAR": ("Narrogin",       "WA", "postcode", "6312"),
    "KTN": ("Katanning",      "WA", "postcode", "6317"),
    "MRD": ("Merredin",       "WA", "postcode", "6415"),
    "CVN": ("Carnarvon",      "WA", "postcode", "6701"),
    "EXM": ("Exmouth",        "WA", "postcode", "6707"),
    "NWM": ("Newman",         "WA", "postcode", "6753"),
    "KUN": ("Kununurra",      "WA", "postcode", "6743"),
    "DUN": ("Dunsborough",    "WA", "postcode", "6281"),
    "AUL": ("Australind",     "WA", "postcode", "6233"),
    "RKM": ("Rockingham",     "WA", "postcode", "6168"),
    "JDP": ("Joondalup",      "WA", "postcode", "6027"),
    "ARD": ("Armadale",       "WA", "postcode", "6112"),
    "ELB": ("Ellenbrook",     "WA", "postcode", "6069"),
    "BTL": ("Butler", "WA", "postcode", "6036"),
    "CLK": ("Clarkson", "WA", "postcode", "6030"),
    "ALK": ("Alkimos", "WA", "postcode", "6038"),
    "CRB2": ("Currambine", "WA", "postcode", "6028"),
    "DUC": ("Duncraig", "WA", "postcode", "6023"),
    "BLC2": ("Balcatta", "WA", "postcode", "6021"),
    "DNL2": ("Dianella", "WA", "postcode", "6059"),
    "BYW": ("Bayswater (WA)", "WA", "postcode", "6053"),
    "BSD": ("Bassendean", "WA", "postcode", "6054"),
    "HWY": ("High Wycombe", "WA", "postcode", "6057"),
    "KLM": ("Kalamunda", "WA", "postcode", "6076"),
    "GSN": ("Gosnells", "WA", "postcode", "6110"),
    "THL": ("Thornlie", "WA", "postcode", "6108"),
    "SUC": ("Success", "WA", "postcode", "6164"),
    "SCH2": ("Secret Harbour", "WA", "postcode", "6173"),
    "WRB": ("Warnbro", "WA", "postcode", "6169"),
    "YCP": ("Yanchep", "WA", "postcode", "6035"),
    "MDR": ("Mundaring", "WA", "postcode", "6073"),
    "PJR": ("Pinjarra", "WA", "postcode", "6208"),
    "HVY": ("Harvey", "WA", "postcode", "6220"),
    # Large-population Perth sub-markets
    "FRE": ("Fremantle",      "WA", "postcode", "6160"),
    "MRY": ("Morley",         "WA", "postcode", "6062"),
    "MDL": ("Midland",        "WA", "postcode", "6056"),
    "CNV": ("Canning Vale",   "WA", "postcode", "6155"),
    "BLD": ("Baldivis",       "WA", "postcode", "6171"),
    "WNR": ("Wanneroo",       "WA", "postcode", "6065"),
    "SCB": ("Scarborough",    "WA", "postcode", "6019"),
    "BYF": ("Byford",         "WA", "postcode", "6122"),
    "DNM": ("Denmark",        "WA", "postcode", "6333"),
    # SA
    "ADL": ("Adelaide",       "SA", "city",     "sa-Adelaide"),
    "MTG": ("Mount Gambier",  "SA", "postcode", "5290"),
    "WHY": ("Whyalla",        "SA", "postcode", "5600"),
    "MBR": ("Murray Bridge",  "SA", "postcode", "5253"),
    "PTL": ("Port Lincoln",   "SA", "postcode", "5606"),
    "VHB": ("Victor Harbor",  "SA", "postcode", "5211"),
    "PAU": ("Port Augusta",   "SA", "postcode", "5700"),
    "PPI": ("Port Pirie",     "SA", "postcode", "5540"),
    "GWL": ("Gawler",         "SA", "postcode", "5118"),
    "MTB": ("Mount Barker",   "SA", "postcode", "5251"),
    "GLW": ("Goolwa",         "SA", "postcode", "5214"),
    "WLR": ("Wallaroo",       "SA", "postcode", "5556"),
    "KDN": ("Kadina",         "SA", "postcode", "5554"),
    "CLR": ("Clare",          "SA", "postcode", "5453"),
    "NRC": ("Naracoorte",     "SA", "postcode", "5271"),
    "MLC": ("Millicent",      "SA", "postcode", "5280"),
    "RNK": ("Renmark",        "SA", "postcode", "5341"),
    "BRI": ("Berri",          "SA", "postcode", "5343"),
    "LOX": ("Loxton",         "SA", "postcode", "5333"),
    "CDN": ("Ceduna",         "SA", "postcode", "5690"),
    "RXD": ("Roxby Downs",    "SA", "postcode", "5725"),
    "NRP": ("Nuriootpa",      "SA", "postcode", "5355"),
    "TND": ("Tanunda",        "SA", "postcode", "5352"),
    "STR": ("Strathalbyn",    "SA", "postcode", "5255"),
    "KGI": ("Kingscote",      "SA", "postcode", "5223"),
    "MCV": ("McLaren Vale",   "SA", "postcode", "5171"),
    "GLD": ("Golden Grove", "SA", "postcode", "5125"),
    "MWL2": ("Mawson Lakes", "SA", "postcode", "5095"),
    "PRH": ("Para Hills", "SA", "postcode", "5096"),
    "IGF": ("Ingle Farm", "SA", "postcode", "5098"),
    "CBT2": ("Campbelltown (SA)", "SA", "postcode", "5074"),
    "NRW2": ("Norwood", "SA", "postcode", "5067"),
    "UNL": ("Unley", "SA", "postcode", "5061"),
    "MTC": ("Mitcham", "SA", "postcode", "5062"),
    "BKW": ("Blackwood", "SA", "postcode", "5051"),
    "ABP": ("Aberfoyle Park", "SA", "postcode", "5159"),
    "MPV": ("Morphett Vale", "SA", "postcode", "5162"),
    "CHB": ("Christies Beach", "SA", "postcode", "5165"),
    "SFD": ("Seaford (SA)", "SA", "postcode", "5169"),
    "SMP": ("Semaphore", "SA", "postcode", "5019"),
    "HNB": ("Henley Beach", "SA", "postcode", "5022"),
    "WLK": ("West Lakes", "SA", "postcode", "5021"),
    "PSP": ("Prospect (SA)", "SA", "postcode", "5082"),
    "MRO": ("Marion", "SA", "postcode", "5043"),
    "HLC": ("Hallett Cove", "SA", "postcode", "5158"),
    "AGV": ("Angle Vale", "SA", "postcode", "5117"),
    # Large-population Adelaide sub-markets
    "ELZ": ("Elizabeth",      "SA", "postcode", "5112"),
    "SLB": ("Salisbury",      "SA", "postcode", "5108"),
    "MDB": ("Modbury",        "SA", "postcode", "5092"),
    "GLG": ("Glenelg",        "SA", "postcode", "5045"),
    "NLG": ("Noarlunga Centre", "SA", "postcode", "5168"),
    "ALD": ("Aldinga Beach",  "SA", "postcode", "5173"),
    "MNP": ("Munno Para",     "SA", "postcode", "5115"),
    # TAS
    "HBA": ("Hobart",         "TAS", "city",     "tas-Hobart"),
    "LST": ("Launceston",     "TAS", "postcode", "7250"),
    "DPT": ("Devonport",      "TAS", "postcode", "7310"),
    "BUR": ("Burnie",         "TAS", "postcode", "7320"),
    "ULV": ("Ulverstone",     "TAS", "postcode", "7315"),
    "WYD": ("Wynyard",        "TAS", "postcode", "7325"),
    "SMT": ("Smithton",       "TAS", "postcode", "7330"),
    "QTN": ("Queenstown",     "TAS", "postcode", "7467"),
    "NNF": ("New Norfolk",    "TAS", "postcode", "7140"),
    "HUO": ("Huonville",      "TAS", "postcode", "7109"),
    "KGS": ("Kingston",       "TAS", "postcode", "7050"),
    "SOR": ("Sorell",         "TAS", "postcode", "7172"),
    "BWT": ("Bridgewater",    "TAS", "postcode", "7030"),
    "GLN": ("Glenorchy",      "TAS", "postcode", "7010"),
    "BLV": ("Bellerive",      "TAS", "postcode", "7018"),
    "SCT": ("Scottsdale",     "TAS", "postcode", "7260"),
    "GTN": ("George Town",    "TAS", "postcode", "7253"),
    "DLR": ("Deloraine",      "TAS", "postcode", "7304"),
    "LGF": ("Longford",       "TAS", "postcode", "7301"),
    "STH": ("St Helens",      "TAS", "postcode", "7216"),
    "SWN": ("Swansea",        "TAS", "postcode", "7190"),
    "BIC": ("Bicheno",        "TAS", "postcode", "7215"),
    "PGN": ("Penguin",        "TAS", "postcode", "7316"),
    "SMS": ("Somerset",       "TAS", "postcode", "7322"),
    "NWH": ("Newnham", "TAS", "postcode", "7248"),
    "LGN2": ("Legana", "TAS", "postcode", "7277"),
    "PTH": ("Perth (TAS)", "TAS", "postcode", "7300"),
    "EVD": ("Evandale", "TAS", "postcode", "7212"),
    "CPT": ("Campbell Town", "TAS", "postcode", "7210"),
    "OTL": ("Oatlands", "TAS", "postcode", "7120"),
    "RCH2": ("Richmond (TAS)", "TAS", "postcode", "7025"),
    "DGF": ("Dodges Ferry", "TAS", "postcode", "7173"),
    "CYG": ("Cygnet", "TAS", "postcode", "7112"),
    "GVN": ("Geeveston", "TAS", "postcode", "7116"),
    "DVR": ("Dover", "TAS", "postcode", "7117"),
    "MRG": ("Margate", "TAS", "postcode", "7054"),
    "BMB": ("Blackmans Bay", "TAS", "postcode", "7052"),
    "TRN2": ("Taroona", "TAS", "postcode", "7053"),
    "SDB": ("Sandy Bay", "TAS", "postcode", "7005"),
    "NHB": ("North Hobart", "TAS", "postcode", "7000"),
    "MNH2": ("Moonah", "TAS", "postcode", "7009"),
    "CLM": ("Claremont (TAS)", "TAS", "postcode", "7011"),
    "LDF": ("Lindisfarne", "TAS", "postcode", "7015"),
    "BCF": ("Beaconsfield", "TAS", "postcode", "7270"),
    # ACT / NT
    "CBR": ("Canberra",       "ACT", "city",     "act-Canberra"),
    "DRW": ("Darwin",         "NT",  "city",     "nt-Darwin"),
    "ASP": ("Alice Springs",  "NT",  "postcode", "0870"),
    # ACT districts (Canberra is one city — these are its suburbs/town centres)
    "CIVIC": ("Canberra City",  "ACT", "postcode", "2601"),
    "DKN": ("Dickson",        "ACT", "postcode", "2602"),
    "GRF": ("Griffith (ACT)", "ACT", "postcode", "2603"),
    "KGN": ("Kingston (ACT)", "ACT", "postcode", "2604"),
    "CTN": ("Curtin",         "ACT", "postcode", "2605"),
    "PHL": ("Phillip (Woden)", "ACT", "postcode", "2606"),
    "FAR": ("Farrer",         "ACT", "postcode", "2607"),
    "WSC": ("Weston Creek",   "ACT", "postcode", "2611"),
    "BDN": ("Braddon",        "ACT", "postcode", "2612"),
    "HWK": ("Hawker",         "ACT", "postcode", "2614"),
    "DNL": ("Dunlop",         "ACT", "postcode", "2615"),
    "BLC": ("Belconnen",      "ACT", "postcode", "2617"),
    "TUG": ("Tuggeranong",    "ACT", "postcode", "2900"),
    "KMB": ("Kambah",         "ACT", "postcode", "2902"),
    "WNS": ("Wanniassa",      "ACT", "postcode", "2903"),
    "GWR": ("Gowrie",         "ACT", "postcode", "2904"),
    "CLW": ("Calwell",        "ACT", "postcode", "2905"),
    "GDN": ("Gordon (ACT)",   "ACT", "postcode", "2906"),
    "CRC": ("Crace",          "ACT", "postcode", "2911"),
    "GGL": ("Gungahlin",      "ACT", "postcode", "2912"),
    "NGN": ("Ngunnawal",      "ACT", "postcode", "2913"),
    "BRT": ("Barton", "ACT", "postcode", "2600"),
    "FYS": ("Fyshwick", "ACT", "postcode", "2609"),
    "AMR": ("Amaroo", "ACT", "postcode", "2914"),
    # NT (small market — fewer towns exist than 20)
    "DWC": ("Darwin City",    "NT", "postcode", "0800"),
    "NCL": ("Nightcliff",     "NT", "postcode", "0810"),
    "KRM": ("Karama",         "NT", "postcode", "0812"),
    "FNB": ("Fannie Bay",     "NT", "postcode", "0820"),
    "PLM": ("Palmerston",     "NT", "postcode", "0830"),
    "RSB": ("Rosebery",       "NT", "postcode", "0832"),
    "HWS": ("Howard Springs", "NT", "postcode", "0835"),
    "HDO": ("Humpty Doo",     "NT", "postcode", "0836"),
    "KTH": ("Katherine",      "NT", "postcode", "0850"),
    "TNC": ("Tennant Creek",  "NT", "postcode", "0860"),
    "BRM2": ("Berrimah", "NT", "postcode", "0828"),
    "VRG": ("Virginia (NT)", "NT", "postcode", "0834"),
    "YUL": ("Yulara", "NT", "postcode", "0872"),
    # Nhulunbuy (0880) and Jabiru (0886) omitted — SQM has no price history for
    # them (too few listings); they baked as empty rows.
}

PAGES = {
    "price": "asking-property-prices",
    "rent":  "weekly-rents",
    "yield": "rental-yield",
    "vac":   "vacancy-rates",
    "stock": "total-property-listings",
}


def build_url(page, kind, param):
    url = BASE + PAGES[page]
    if kind == "national":
        return url + "?national=1"
    if kind == "avg":
        return url + "?avg=1"
    if kind == "city":
        return url + "?region=" + param + "&type=c"
    return url + "?postcode=" + param


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"    FAIL {url}: {e}")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def extract_series(html):
    """Locate `var data = [ ... ]` and json.loads it via bracket-balance scan."""
    if not html:
        return None
    m = re.search(r"var\s+data\s*=\s*\[", html)
    if not m:
        return None
    start = html.index("[", m.start())
    depth = 0
    for i in range(start, len(html)):
        c = html[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start:i + 1])
                except json.JSONDecodeError as e:
                    print(f"    JSON parse error: {e}")
                    return None
    return None


def month_key(row):
    return "%04d-%02d" % (int(row["year"]), int(row["month"]))


def drop_partial_month(rows):
    """SQM monthly series include the in-progress month with near-zero counts;
    the site's charts hide it. Drop any trailing rows >= the current month."""
    cur = datetime.now(timezone.utc).strftime("%Y-%m")
    return [r for r in rows if month_key(r) < cur]


def pct_rank(vals, x):
    """Percentile (0-100) of x within vals."""
    vals = [v for v in vals if v is not None]
    if not vals or x is None:
        return None
    below = sum(1 for v in vals if v <= x)
    return round(100.0 * below / len(vals), 1)


def bake_region(code, name, state, kind, param):
    out = {"name": name, "state": state, "kind": kind, "param": param}
    hist = {"name": name, "state": state}   # full untrimmed series for backtests
    ok = False

    # ── weekly asking prices (signal series) ─────────────────────────────
    rows = extract_series(fetch_html(build_url("price", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("combined") or r.get("houses_all")]
        rows.sort(key=lambda r: r["date"])
        px = [int(round(r.get("combined") or r.get("houses_all") or 0)) for r in rows]
        if len(px) >= 60:
            # Worst peak-to-trough over the FULL history (2009→) before we trim.
            # This is the number that exposes mining-town risk: a 10y window
            # starts after the 2012-16 bust and makes Karratha look tame.
            peak = px[0]
            worst = 0.0
            for v in px:
                peak = max(peak, v)
                if peak:
                    worst = min(worst, v / peak - 1)
            out["ddmax"] = round(worst * 100, 1)
            out["hist_w"] = len(px)
            hist["px"] = [[r["date"], int(round(r.get("combined") or r.get("houses_all") or 0))]
                          for r in rows]
            hist["px_h"] = [[r["date"], int(round(r.get("houses_all") or 0))] for r in rows]
            hist["px_u"] = [[r["date"], int(round(r.get("units_all") or 0))] for r in rows]
            # Keep the last 10 years only. The longest MA pair is 260w and the
            # sparkline draws 520w, so older points are dead weight in a file
            # the board fetches at boot (215 regions x 880w was 1.7 MB).
            out["px"] = px[-520:]
            out["px_end"] = rows[-1]["date"]
            last, y_ago = rows[-1], rows[max(0, len(rows) - 53)]
            out["snap_px"] = {
                "h":   int(round(last.get("houses_all") or 0)) or None,
                "h52": int(round(y_ago.get("houses_all") or 0)) or None,
                "u":   int(round(last.get("units_all") or 0)) or None,
                "u52": int(round(y_ago.get("units_all") or 0)) or None,
            }
            ok = True

    # ── weekly rents ─────────────────────────────────────────────────────
    rows = extract_series(fetch_html(build_url("rent", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("combined") or r.get("houses_all")]
        rows.sort(key=lambda r: r["date"])
        if rows:
            val = lambda r: r.get("combined") or r.get("houses_all")
            last, y_ago = rows[-1], rows[max(0, len(rows) - 53)]
            out["rent"] = round(val(last), 1)
            out["rent52"] = round(val(y_ago), 1)
            hist["rent"] = [[r["date"], round(val(r), 1)] for r in rows if val(r)]
            ok = True

    # ── rental yield (weekly; houses_all preferred) ──────────────────────
    rows = extract_series(fetch_html(build_url("yield", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("houses_all") or r.get("units_all")]
        rows.sort(key=lambda r: r["date"])
        if rows:
            val = lambda r: r.get("houses_all") or r.get("units_all")
            series = [val(r) for r in rows]
            out["yield"] = round(series[-1], 2)
            out["yield_pct"] = pct_rank(series, series[-1])
            hist["yield"] = [[r["date"], round(val(r), 2)] for r in rows if val(r)]
            ok = True

    # ── vacancy (monthly) ────────────────────────────────────────────────
    rows = extract_series(fetch_html(build_url("vac", kind, param)))
    time.sleep(SLEEP)
    if rows:
        rows = [r for r in rows if r.get("vr") is not None]
        rows.sort(key=month_key)
        rows = drop_partial_month(rows)
        if rows:
            vrs = [float(r["vr"]) for r in rows]
            # SQM unit quirk: city pages embed vr as a fraction (0.02 = 2%),
            # postcode pages as percent (0.85 = 0.85%). Normalise to percent —
            # no market's vacancy history maxes out below 0.25% AND fraction
            # series never exceed 0.25 (= 25%).
            if vrs and max(vrs) <= 0.25:
                vrs = [v * 100 for v in vrs]
            vrs = [round(v, 2) for v in vrs]
            out["vac"] = vrs[-1]
            out["vac12"] = vrs[max(0, len(vrs) - 13)]
            out["vac_m"] = vrs[-36:]
            hist["vac"] = [[month_key(r), v] for r, v in zip(rows, vrs)]
            ok = True

    # ── stock on market (monthly; sum of aged buckets) ───────────────────
    rows = extract_series(fetch_html(build_url("stock", kind, param)))
    time.sleep(SLEEP)
    if rows:
        def total(r):
            return sum(int(r.get(k) or 0) for k in ("r30", "r60", "r90", "r180", "r180p"))
        rows.sort(key=month_key)
        rows = drop_partial_month(rows)
        pairs = [(month_key(r), total(r)) for r in rows]
        pairs = [p for p in pairs if p[1] > 0] or pairs
        totals = [t for _, t in pairs]
        if totals:
            out["stock"] = totals[-1]
            out["stock12"] = totals[max(0, len(totals) - 13)]
            out["stock_m"] = totals[-36:]
            hist["stock"] = [[m, t] for m, t in pairs]
            ok = True

    return (out, hist) if ok else (None, None)


def main():
    only = set(sys.argv[1:])
    old = {}
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as f:
                old = json.load(f).get("regions", {})
        except Exception:
            old = {}

    old_hist = {}
    if os.path.exists(HIST_OUT):
        try:
            with open(HIST_OUT, encoding="utf-8") as f:
                old_hist = json.load(f).get("regions", {})
        except Exception:
            old_hist = {}

    regions = {}
    hists = {}
    n = len(REGIONS)
    for i, (code, (name, state, kind, param)) in enumerate(REGIONS.items(), 1):
        if only and code not in only:
            if code in old:
                regions[code] = old[code]
            if code in old_hist:
                hists[code] = old_hist[code]
            continue
        print(f"[{i}/{n}] {code} {name} ...", flush=True)
        try:
            baked, hist = bake_region(code, name, state, kind, param)
        except Exception as e:
            print(f"    ERROR {code}: {e}")
            baked, hist = None, None
        if hist:
            hists[code] = hist
        elif code in old_hist:
            hists[code] = old_hist[code]
        if baked:
            regions[code] = baked
            print(f"    ok: px={len(baked.get('px', []))}w "
                  f"yield={baked.get('yield')} vac={baked.get('vac')}")
        elif code in old:
            regions[code] = old[code]
            print("    kept previous bake")
        else:
            print("    NO DATA")

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "SQM Research (sqmresearch.com.au) — personal reference only",
        "regions": regions,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, OUT)
    size_kb = os.path.getsize(OUT) // 1024
    print(f"\nWrote {OUT} ({size_kb} KB, {len(regions)}/{n} regions)")

    hist_payload = {"updated": payload["updated"], "source": payload["source"], "regions": hists}
    tmp_h = HIST_OUT + ".tmp"
    with open(tmp_h, "w", encoding="utf-8") as f:
        json.dump(hist_payload, f, separators=(",", ":"))
    os.replace(tmp_h, HIST_OUT)
    print(f"Wrote {HIST_OUT} ({os.path.getsize(HIST_OUT) // 1024} KB, backtest history)")


if __name__ == "__main__":
    main()
