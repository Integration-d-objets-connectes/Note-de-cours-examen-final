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

# SELECT COUNT(*) FROM remplissages WHERE fontaine_id = ... AND horodatage >= minuit.
# Le dictionnaire est le filtre (WHERE). $gte signifie « supérieur ou égal ».
bouteilles_aujourdhui = db.remplissages.count_documents(
    {"fontaine_id": ID_FONTAINE, "horodatage": {"$gte": minuit}}
)
print(f"Nombre de bouteilles remplies aujourd'hui : {bouteilles_aujourdhui}")


# SELECT COUNT(*) FROM remplissages WHERE fontaine_id = ...
bouteilles_total = db.remplissages.count_documents({"fontaine_id": ID_FONTAINE})
print(f"Nombre de bouteilles au total : {bouteilles_total}")


# SELECT filtre FROM fontaines WHERE _id = ... LIMIT 1.
# 1er argument : le filtre (WHERE). 2e : la projection (SELECT).
# Dans la projection, 1 inclut le champ et _id: 0 retire l'identifiant.
fontaine = db.fontaines.find_one({"_id": ID_FONTAINE}, {"_id": 0, "filtre": 1})
filtre = fontaine["filtre"]
print(
    f"{filtre['litres_depuis_changement']} L depuis le changement du {heure_locale(filtre['date_changement'])}"
)


n = 10
depuis = datetime.now(timezone.utc) - timedelta(minutes=n)
# SELECT horodatage, debit FROM lectures_debit
# WHERE fontaine_id = ... AND horodatage >= depuis ORDER BY horodatage ASC.
# find(filtre, projection) permet de lire plusieurs documents. sort(..., 1) trie en ordre croissant.
lectures_recentes_debits = db.lectures_debit.find(
    {"fontaine_id": ID_FONTAINE, "horodatage": {"$gte": depuis}},
    {"_id": 0, "horodatage": 1, "debit": 1},
).sort("horodatage", 1)

for lecture in lectures_recentes_debits:
    print(heure_locale(lecture["horodatage"]), lecture["debit"], "L/min")


# UPDATE fontaines SET ... WHERE _id = ...
# 1er argument : le filtre (WHERE). 2e : les changements ($set, comme SET en SQL).
# update_one modifie au plus un document. Le point indique un champ du sous-document config.
db.fontaines.update_one(
    {"_id": ID_FONTAINE},
    {"$set": {"config.mode_auto": False, "config.seuil_alerte_litres": 2500}},
)
# SELECT config FROM fontaines WHERE _id = ... LIMIT 1 pour vérifier la modification.
pprint(db.fontaines.find_one({"_id": ID_FONTAINE}, {"_id": 0, "config": 1}))


type_evenement = None

# WHERE fontaine_id = ..., avec AND type = ... si un type est choisi.
filtre_evenements = {"fontaine_id": ID_FONTAINE}
if type_evenement is not None:
    filtre_evenements["type"] = type_evenement

# La projection {"_id": 0} retourne tous les champs sauf _id.
# sort(..., -1).limit(3) correspond à ORDER BY horodatage DESC LIMIT 3.
evenements = (
    db.evenements.find(filtre_evenements, {"_id": 0}).sort("horodatage", -1).limit(3)
)

for evenement in evenements:
    par = (
        f" par {evenement['utilisateur']['nom']}" if "utilisateur" in evenement else ""
    )
    print(heure_locale(evenement["horodatage"]), evenement["type"] + par)


# SELECT * FROM utilisateurs WHERE nom = 'Léa' LIMIT 1.
# Sans deuxième argument, find_one retourne tous les champs, dont _id.
technicien = db.utilisateurs.find_one({"nom": "Léa"})
maintenant = datetime.now(timezone.utc)

# INSERT INTO evenements (...) VALUES (...).
# L'argument est le document complet à insérer, avec le sous-document utilisateur.
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
# UPDATE fontaines SET ... WHERE _id = ...
# $set modifie les deux champs du sous-document filtre visés par leur chemin.
db.fontaines.update_one(
    {"_id": ID_FONTAINE},
    {
        "$set": {
            "filtre.date_changement": maintenant,
            "filtre.litres_depuis_changement": 0,
        }
    },
)
# SELECT filtre FROM fontaines WHERE _id = ... LIMIT 1 pour vérifier la remise à zéro.
pprint(db.fontaines.find_one({"_id": ID_FONTAINE}, {"_id": 0, "filtre": 1}))


client.close()
