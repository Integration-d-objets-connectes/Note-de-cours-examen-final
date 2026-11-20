from datetime import datetime, timedelta, timezone
from pprint import pprint

from pymongo import MongoClient

import config


def heure_locale(date: datetime) -> str:
    return date.astimezone(config.FUSEAU_LOCAL).strftime("%Y-%m-%d %H:%M")


client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000, tz_aware=True)
db = client[config.MONGODB_BASE]

ID_FONTAINE = "hydrocegep-01"
minuit = datetime.now(config.FUSEAU_LOCAL).replace(
    hour=0, minute=0, second=0, microsecond=0
)

bouteilles_aujourdhui = db.remplissages.count_documents(
    {"fontaine_id": ID_FONTAINE, "horodatage": {"$gte": minuit}}
)
print(f"Nombre de bouteilles remplies aujourd'hui : {bouteilles_aujourdhui}")


bouteilles_total = db.remplissages.count_documents({"fontaine_id": ID_FONTAINE})
print(f"Nombre de bouteilles au total : {bouteilles_total}")


fontaine = db.fontaines.find_one({"_id": ID_FONTAINE}, {"_id": 0, "filtre": 1})
filtre = fontaine["filtre"]
print(
    f"{filtre['litres_depuis_changement']} L depuis le changement du {heure_locale(filtre['date_changement'])}"
)


n = 10
depuis = datetime.now(timezone.utc) - timedelta(minutes=n)
lectures_recentes_debits = db.lectures_debit.find(
    {"fontaine_id": ID_FONTAINE, "horodatage": {"$gte": depuis}},
    {"_id": 0, "horodatage": 1, "debit": 1},
).sort("horodatage", 1)

for lecture in lectures_recentes_debits:
    print(heure_locale(lecture["horodatage"]), lecture["debit"], "L/min")


db.fontaines.update_one(
    {"_id": ID_FONTAINE},
    {"$set": {"config.mode_auto": False, "config.seuil_alerte_litres": 2500}},
)
pprint(db.fontaines.find_one({"_id": ID_FONTAINE}, {"_id": 0, "config": 1}))


type_evenement = None

filtre_evenements = {"fontaine_id": ID_FONTAINE}
if type_evenement is not None:
    filtre_evenements["type"] = type_evenement

evenements = (
    db.evenements.find(filtre_evenements, {"_id": 0}).sort("horodatage", -1).limit(3)
)

for evenement in evenements:
    par = (
        f" par {evenement['utilisateur']['nom']}" if "utilisateur" in evenement else ""
    )
    print(heure_locale(evenement["horodatage"]), evenement["type"] + par)


technicien = db.utilisateurs.find_one({"nom": "Léa"})
maintenant = datetime.now(timezone.utc)

db.evenements.insert_one(
    {
        "horodatage": maintenant,
        "fontaine_id": ID_FONTAINE,
        "type": "changement_filtre",
        "utilisateur": {
            "id": technicien["_id"],
            "nom": technicien["nom"],
        },
    }
)
db.fontaines.update_one(
    {"_id": ID_FONTAINE},
    {
        "$set": {
            "filtre.date_changement": maintenant,
            "filtre.litres_depuis_changement": 0,
        }
    },
)
pprint(db.fontaines.find_one({"_id": ID_FONTAINE}, {"_id": 0, "filtre": 1}))


client.close()
