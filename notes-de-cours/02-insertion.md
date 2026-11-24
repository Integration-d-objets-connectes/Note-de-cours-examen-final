# Fiche 2 — Insertion avec PyMongo

[← Modélisation](01-modelisation.md) · [Requêtes →](03-requetes.md)

## 1. Transformer les minimums en quantités à générer

Pour l’[énoncé HydroCégep](../README.md), vise une fontaine, deux techniciens, 60 lectures espacées d’une minute, 10 remplissages aujourd’hui, 10 avant aujourd’hui, deux changements de filtre (un par technicien) et deux alertes.

## 2. Préparer une date de référence et la collection time series

Les blocs supposent que `db` est connecté à une base de pratique vide.

```python
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

fuseau = ZoneInfo("America/Toronto")
maintenant = datetime.now(timezone.utc)
minuit = maintenant.astimezone(fuseau).replace(
    hour=0, minute=0, second=0, microsecond=0
).astimezone(timezone.utc)
fontaine_id = "hydrocegep-01"

db.create_collection("lectures_debit", timeseries={
    "timeField": "horodatage",
    "metaField": "fontaine_id",
    "granularity": "minutes",
})
```

Crée la collection time series avant d’y insérer la première lecture. Pour travailler dans une base déjà initialisée, vérifie que la collection existante a bien les options attendues. Relancer des insertions simples peut dupliquer les historiques ou provoquer un conflit de `_id`.

## 3. Insérer les entités, puis réutiliser leurs identifiants

```python
lea_id = db.utilisateurs.insert_one({"nom": "Léa"}).inserted_id
pierre_id = db.utilisateurs.insert_one({"nom": "Pierre"}).inserted_id
dernier_changement = maintenant - timedelta(days=11)

db.fontaines.insert_one({
    "_id": fontaine_id,
    "nom": "Fontaine du corridor TI",
    "config": {"mode_auto": True, "seuil_alerte_litres": 3000},
    "filtre": {
        "date_changement": dernier_changement,
        "litres_depuis_changement": 1840.5,
    },
})
```

## 4. Générer les données en lots avec insert_many

```python
db.lectures_debit.insert_many([
    {
        "fontaine_id": fontaine_id,
        "horodatage": maintenant - timedelta(minutes=i),
        "debit": 0.0 if i % 3 == 0 else 1.8,
    }
    for i in range(60)
])

duree_aujourdhui = maintenant - minuit
dates_aujourdhui = [minuit + duree_aujourdhui * (i / 10) for i in range(10)]
dates_precedentes = [minuit - timedelta(hours=12 + 24 * i) for i in range(10)]

db.remplissages.insert_many([
    {"fontaine_id": fontaine_id, "horodatage": date, "volume": 0.6}
    for date in dates_aujourdhui + dates_precedentes
])

db.evenements.insert_many([
    {
        "fontaine_id": fontaine_id,
        "horodatage": maintenant - timedelta(days=40),
        "type": "changement_filtre",
        "utilisateur": {"id": lea_id, "nom": "Léa"},
    },
    {
        "fontaine_id": fontaine_id,
        "horodatage": maintenant - timedelta(days=13),
        "type": "alerte",
        "litres_depuis_changement": 3012.0,
    },
    {
        "fontaine_id": fontaine_id,
        "horodatage": maintenant - timedelta(days=12),
        "type": "alerte",
        "litres_depuis_changement": 3140.5,
    },
    {
        "fontaine_id": fontaine_id,
        "horodatage": dernier_changement,
        "type": "changement_filtre",
        "utilisateur": {"id": pierre_id, "nom": "Pierre"},
    },
])
```

## 5. Vérifier les contraintes une par une

| Contrainte | Vérification |
|---|---|
| 60 mesures à une minute d’intervalle | Compte les lectures de la dernière heure, trie-les et vérifie l’écart entre deux dates |
| Au moins 5 remplissages de chaque côté de minuit | Compte avec `$gte` pour aujourd’hui et `$lt` pour les jours précédents |
| Un changement par technicien | Filtre sur `type` et `utilisateur.id` pour chacun |
| Au moins une alerte | Compte les documents de type `alerte` |
| État du filtre cohérent | Compare la date dans la fontaine au dernier changement de l’historique |

**Variantes et pièges.** Pour « une mesure toutes les cinq minutes », génère l’écart avec `timedelta(minutes=5 * i)`. Pour « une mesure aujourd’hui », construis la date à partir du minuit local. En soustrayant plusieurs minutes à l’heure actuelle, tu risques de passer à la veille juste après minuit. Si tu utilises des valeurs aléatoires, fixe d’abord les dates, les types et les quantités imposés, puis fais varier les valeurs libres.

Le [script de pratique](../insertion_donnees.py) associe les bons identifiants à des noms copiés différents. Il annonce aussi des mesures à zéro sans les garantir. Vérifie ces deux points dans ton propre jeu de données.
