import random
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

import config

client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000, tz_aware=True)
db = client[config.MONGODB_BASE]

COLLECTIONS = (
    "fontaines",
    "utilisateurs",
    "lectures_debit",
    "remplissages",
    "evenements",
)

# Comme DROP TABLE IF EXISTS en SQL. L'argument est le nom de la collection à supprimer.
for nom in COLLECTIONS:
    db.drop_collection(nom)

# Comme CREATE TABLE en SQL. Le premier argument est le nom de la collection.
# timeseries indique le champ de date, la métadonnée qui identifie la série
# et la granularité des mesures.
db.create_collection(
    "lectures_debit",
    timeseries={
        "timeField": "horodatage",
        "metaField": "fontaine_id",
        "granularity": "minutes",
    },
)

maintenant = datetime.now(timezone.utc)
minuit = maintenant.astimezone(config.FUSEAU_LOCAL).replace(
    hour=0, minute=0, second=0, microsecond=0
).astimezone(timezone.utc)
FONTAINE = "hydrocegep-01"


# INSERT INTO utilisateurs (nom) VALUES (...).
# insert_one reçoit un dictionnaire. inserted_id récupère le _id généré pour le réutiliser.
pierre_id = db.utilisateurs.insert_one({"nom": "Pierre"}).inserted_id
lea_id = db.utilisateurs.insert_one({"nom": "Léa"}).inserted_id

# INSERT INTO evenements (...) VALUES (...), (...), ...
# insert_many reçoit une liste de documents. Ici, deux changements et deux alertes.
# utilisateur.id référence le technicien et utilisateur.nom est une copie pour l'affichage.
changement_pierre = maintenant - timedelta(days=11)
db.evenements.insert_many(
    [
        {
            "horodatage": maintenant - timedelta(days=40),
            "fontaine_id": FONTAINE,
            "type": "changement_filtre",
            "utilisateur": {"id": lea_id, "nom": "Léa"},
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
            "utilisateur": {"id": pierre_id, "nom": "Pierre"},
        },
    ]
)

# INSERT INTO fontaines (...) VALUES (...).
# Le document fournit son propre _id et contient les sous-documents config et filtre.
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

# INSERT INTO lectures_debit (...) VALUES (...), ...
# La boucle prépare 60 documents, un par minute, avec un débit nul une minute sur trois.
db.lectures_debit.insert_many(
    [
        {
            "horodatage": maintenant - timedelta(minutes=m),
            "fontaine_id": FONTAINE,
            "debit": 0.0 if m % 3 == 0 else round(random.uniform(0.1, 2.5), 1),
        }
        for m in range(60)
    ]
)

# Répartir les 10 premiers remplissages entre minuit et maintenant,
# même si le script est exécuté juste après minuit.
duree_aujourdhui = maintenant - minuit

remplissages = [
    {
        "horodatage": minuit + duree_aujourdhui * (i / 10),
        "fontaine_id": FONTAINE,
        "volume": round(random.uniform(0.5, 0.8), 1),
    }
    for i in range(10)
]

remplissages += [
    {
        "horodatage": minuit - timedelta(hours=12 + 24 * jour),
        "fontaine_id": FONTAINE,
        "volume": round(random.uniform(0.5, 0.8), 1),
    }
    for jour in range(10)
]

# INSERT INTO remplissages (...) VALUES (...), ...
# Les deux groupes de dates sont réunis dans la liste passée à insert_many.
db.remplissages.insert_many(remplissages)

# SELECT COUNT(*) FROM <collection>. Le filtre vide {} compte tous les documents.
for nom in COLLECTIONS:
    print(f"{nom} : {db[nom].count_documents({})}")

client.close()
