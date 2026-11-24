# Fiche 3 — Requêtes MongoDB avec PyMongo

[← Insertion](02-insertion.md) · [Modélisation](01-modelisation.md)

## 1. Traduire les mots de la question

| Consigne | Patron |
|---|---|
| Combien de documents ? | `count_documents(filtre)` |
| Lire un état ou un document unique | `find_one(filtre, projection)` |
| Lister plusieurs documents | `find(filtre, projection)` |
| Depuis une date | `{"horodatage": {"$gte": debut}}` |
| Entre deux bornes adjacentes | `{"horodatage": {"$gte": debut, "$lt": fin}}` |
| Afficher seulement certains champs | Projection avec les champs à `1` et `"_id": 0` |
| Plus ancien d’abord | `.sort("horodatage", 1)` |
| Les trois derniers | `.sort("horodatage", -1).limit(3)` |
| Modifier un champ imbriqué | `{"$set": {"sous_document.champ": valeur}}` |
| Augmenter un compteur | `{"$inc": {"sous_document.compteur": valeur}}` |
| Calculer un total, une moyenne ou un résultat par groupe | `aggregate()` avec `$match` et `$group` |

## 2. Refaire les sept requêtes d’HydroCégep

Reprends le calcul des dates de la [fiche d’insertion](02-insertion.md). Utilise `MongoClient(..., tz_aware=True)` pour convertir les dates lues en heure locale.

### 1 et 2 — Bouteilles depuis minuit et au total

```python
par_fontaine = {"fontaine_id": fontaine_id}
par_id = {"_id": fontaine_id}
aujourdhui = {"horodatage": {"$gte": minuit, "$lte": maintenant}}

print(db.remplissages.count_documents({**par_fontaine, **aujourdhui}))
print(db.remplissages.count_documents(par_fontaine))
```

Pour une journée complète, utilise une borne de début incluse et le minuit suivant exclu. Construis les deux minuits dans le fuseau local pour tenir compte des changements d’heure.

### 3 — État du filtre

```python
fontaine = db.fontaines.find_one(par_id, {"_id": 0, "filtre": 1})
if fontaine:
    filtre = fontaine["filtre"]
    print(filtre["litres_depuis_changement"], filtre["date_changement"].astimezone(fuseau))
```

### 4 — Débit des n dernières minutes

```python
n = 10
depuis = maintenant - timedelta(minutes=n)
lectures = db.lectures_debit.find(
    {**par_fontaine, "horodatage": {"$gte": depuis, "$lte": maintenant}},
    {"_id": 0, "horodatage": 1, "debit": 1},
).sort("horodatage", 1)

for lecture in lectures:
    print(lecture["horodatage"].astimezone(fuseau), lecture["debit"])
```

« Les dernières minutes » impose un intervalle. « Les dernières mesures » impose un tri décroissant suivi de `limit(n)`.

### 5 — Modifier la configuration

```python
db.fontaines.update_one(par_id, {"$set": {
    "config.mode_auto": False,
    "config.seuil_alerte_litres": 2500,
}})
print(db.fontaines.find_one(par_id, {"_id": 0, "config": 1}))
```

La notation pointée cible les champs demandés. Affecter `config` en entier remplace le sous-document.

### 6 — Trois événements récents, type facultatif

```python
type_evenement = None  # ou "alerte" ou "changement_filtre"
filtre_evenements = dict(par_fontaine)
if type_evenement is not None:
    filtre_evenements["type"] = type_evenement

for evenement in db.evenements.find(filtre_evenements).sort("horodatage", -1).limit(3):
    print(evenement["horodatage"].astimezone(fuseau), evenement["type"])
```

Quand `None` signifie « tous les types », omets le critère `type`. Le filtre `{"type": None}` chercherait les valeurs nulles ou les champs absents.

### 7 — Enregistrer un changement et remettre le filtre à zéro

```python
# lea_id représente l'identifiant du technicien sélectionné.
technicien = db.utilisateurs.find_one({"_id": lea_id})
date_changement = datetime.now(timezone.utc)

if technicien and db.fontaines.find_one(par_id, {"_id": 1}):
    db.evenements.insert_one({
        **par_fontaine,
        "horodatage": date_changement,
        "type": "changement_filtre",
        "utilisateur": {"id": technicien["_id"], "nom": technicien["nom"]},
    })
    db.fontaines.update_one(par_id, {"$set": {
        "filtre.date_changement": date_changement,
        "filtre.litres_depuis_changement": 0,
    }})
    print(db.fontaines.find_one(par_id, {"_id": 0, "filtre": 1}))
```

Réutilise la même date dans les deux écritures. Si une variante exige qu’elles réussissent ou échouent ensemble, utilise une transaction sur un déploiement qui la prend en charge.

## 3. Reconnaître les variantes

**Somme et moyenne pour une période**

```python
resultat = db.remplissages.aggregate([
    {"$match": {**par_fontaine, **aujourdhui}},
    {"$group": {
        "_id": None,
        "bouteilles": {"$sum": 1},
        "litres": {"$sum": "$volume"},
        "volume_moyen": {"$avg": "$volume"},
    }},
])
print(next(resultat, {"bouteilles": 0, "litres": 0, "volume_moyen": None}))
```

- **Par fontaine** → groupe avec `"_id": "$fontaine_id"`. Omet le filtre d’une fontaine précise pour inclure toutes les fontaines.
- **Par type d’événement** → groupe avec `"_id": "$type"` et compte avec `{"$sum": 1}`.
- **Dernier changement** → filtre sur `type: "changement_filtre"`, trie par date décroissante et prends le premier.
- **Débit maximal** → filtre la période puis applique `{"$max": "$debit"}`. Pour obtenir aussi la date du maximum, trie les documents par débit décroissant et prends le premier.
- **Alertes au-dessus de 3 000 L** → filtre sur le type et sur `{"litres_depuis_changement": {"$gt": 3000}}`.
- **Augmenter les litres consommés** → utilise `$inc` sur `filtre.litres_depuis_changement` avec le volume mesuré.
- **Trouver les changements d’un technicien** → ajoute `{"utilisateur.id": identifiant}` à ton filtre, avec le même type d’identifiant que dans les documents.

**Avant de remettre** — Vérifie la collection, le filtre, les bornes de date, les champs projetés, le sens du tri et l’affichage. Lorsque la consigne demande de modifier l’état et de garder un historique, vérifie les deux écritures.
