import random
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

import config

client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000, tz_aware=True)
db = client[config.MONGODB_BASE]

db.create_collection(
    "lectures_debit",
    timeseries={
        "timeField": "horodatage",
        "metaField": "fontaine_id",
        "granularity": "minutes",
    },
)

maintenant = datetime.now(timezone.utc)
minuit = datetime.now(config.FUSEAU_LOCAL).replace(
    hour=0, minute=0, second=0, microsecond=0
)
FONTAINE = "hydrocegep-01"


pierre_id = db.utilisateurs.insert_one({"nom": "Pierre"}).inserted_id
lea_id = db.utilisateurs.insert_one({"nom": "Léa"}).inserted_id

# Événements : 2 changements de filtre (un par technicien) et 2 alertes
changement_pierre = maintenant - timedelta(days=11)
db.evenements.insert_many(
    [
        {
            "horodatage": maintenant - timedelta(days=40),
            "fontaine_id": FONTAINE,
            "type": "changement_filtre",
            "utilisateur": {"id": lea_id, "nom": "Julie"},
        },
        {
            "horodatage": maintenant - timedelta(days=13),
            "fontaine_id": FONTAINE,
            "type": "alerte",
            "litres_depuis_changement": 3012.0,
        },
        {
            "horodatage": maintenant - timedelta(days=12),
            "fontaine_id": FONTAINE,
            "type": "alerte",
            "litres_depuis_changement": 3140.5,
        },
        {
            "horodatage": changement_pierre,
            "fontaine_id": FONTAINE,
            "type": "changement_filtre",
            "utilisateur": {"id": pierre_id, "nom": "Marc"},
        },
    ]
)

# Fontaine (_id choisi)
db.fontaines.insert_one(
    {
        "_id": FONTAINE,
        "nom": "Fontaine du corridor TI",
        "config": {"mode_auto": True, "seuil_alerte_litres": 3000},
        "filtre": {
            "date_changement": changement_pierre,
            "litres_depuis_changement": 1840.5,
        },
    }
)

# Lectures_debit : une par minute pendant la dernière heure, débit nul une minute sur trois
db.lectures_debit.insert_many(
    [
        {
            "horodatage": maintenant - timedelta(minutes=m),
            "fontaine_id": FONTAINE,
            "debit": round(random.uniform(0, 2.5), 1),
        }
        for m in range(60)
    ]
)

# Remplissages : 10 aujourd'hui (entre minuit et maintenant) et 10 les jours précédents
duree_aujourdhui = maintenant - minuit

remplissages = [
    {
        "horodatage": maintenant - timedelta(minutes=5 * i),
        "fontaine_id": FONTAINE,
        "volume": round(random.uniform(0.5, 0.8), 1),
    }
    for i in range(10)
]

remplissages += [
    {
        "horodatage": maintenant - timedelta(days=jour + 1),  # un par jour précédent
        "fontaine_id": FONTAINE,
        "volume": round(random.uniform(0.5, 0.8), 1),
    }
    for jour in range(10)
]

db.remplissages.insert_many(remplissages)

for nom in (
    "fontaines",
    "utilisateurs",
    "lectures_debit",
    "remplissages",
    "evenements",
):
    print(f"{nom} : {db[nom].count_documents({})}")

client.close()
