# Fiche de révision MongoDB

Les exemples utilisent PyMongo avec les collections HydroCégep. Dans `mongosh`, les méthodes équivalentes s’écrivent par exemple `findOne`, `insertMany` et `deleteMany`.

## Supprimer des documents ou une collection

| But | PyMongo | `mongosh` | Équivalent SQL |
|---|---|---|---|
| Supprimer au plus une alerte | `db.evenements.delete_one({"type": "alerte"})` | `db.evenements.deleteOne({type: "alerte"})` | Suppression d’une ligne correspondante |
| Supprimer toutes les alertes | `db.evenements.delete_many({"type": "alerte"})` | `db.evenements.deleteMany({type: "alerte"})` | `DELETE FROM evenements WHERE type = 'alerte'` |
| Vider la collection en gardant ses index | `db.evenements.delete_many({})` | `db.evenements.deleteMany({})` | `DELETE FROM evenements` |
| Supprimer la collection et ses index | `db.drop_collection("evenements")` | `db.evenements.drop()` | `DROP TABLE evenements` |

Le filtre vide `{}` sélectionne tous les documents. Dans `mongosh`, l’ancienne méthode `remove({})` vide aussi une collection ordinaire et exige le filtre vide explicite. Elle est dépréciée dans `mongosh` et a été retirée de PyMongo 4. [Suppression avec PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/delete/) · [Ancien `remove`](https://www.mongodb.com/docs/manual/reference/method/db.collection.remove/) · [Migration vers PyMongo 4](https://pymongo.readthedocs.io/en/4.0/migrate-to-pymongo4.html#collection-remove-is-removed) · [Suppression d’une collection](https://www.mongodb.com/docs/manual/reference/method/db.collection.drop/)

## Lire, filtrer et compter

```python
# SELECT filtre FROM fontaines WHERE _id = 'hydrocegep-01' LIMIT 1
db.fontaines.find_one({"_id": "hydrocegep-01"}, {"_id": 0, "filtre": 1})

# Les 3 dernières alertes, avec seulement leur date et leur type
alertes = db.evenements.find(
    {"type": "alerte"},
    {"_id": 0, "horodatage": 1, "type": 1},
).sort("horodatage", -1).limit(3)

# SELECT COUNT(*) FROM evenements WHERE type = 'alerte'
db.evenements.count_documents({"type": "alerte"})
```

- Le premier argument de `find` et de `find_one` est le **filtre** (`WHERE`). Le deuxième est la **projection** (`SELECT`). Une projection avec `1` inclut le champ. Avec une projection d’inclusion, utilise `"_id": 0` pour masquer l’identifiant.
- Plusieurs champs dans un filtre forment un `AND`. Utilise `$or` avec une liste de conditions, `$in` pour une liste de valeurs possibles et `$gte` ou `$lt` pour les bornes `>=` ou `<`.
- `sort("horodatage", 1)` trie de la plus ancienne date à la plus récente. `-1` inverse l’ordre. `limit(3)` limite le résultat à trois documents.
- Pour les remplissages d’aujourd’hui, calcule minuit dans le fuseau local avec `datetime`, puis filtre avec `{"horodatage": {"$gte": minuit}}`.

## Insérer et modifier

```python
# INSERT INTO utilisateurs (nom) VALUES (...)
lea_id = db.utilisateurs.insert_one({"nom": "Léa"}).inserted_id
db.utilisateurs.insert_many([{"nom": "Pierre"}, {"nom": "Nora"}])

# UPDATE fontaines SET ... WHERE _id = ...
db.fontaines.update_one(
    {"_id": "hydrocegep-01"},
    {"$set": {"config.mode_auto": False}},
)
```

`insert_one` reçoit un document et `insert_many` reçoit une liste. `inserted_id` permet de récupérer l’identifiant du document créé. Pour `update_one` et `update_many`, le premier argument désigne les documents à modifier. Le deuxième décrit la modification. `$set` fixe une valeur, `$inc` l’incrémente et le point dans `config.mode_auto` accède au champ imbriqué. [Exemples CRUD PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/) · [Mises à jour PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/update/)

## Agréger et modéliser

```python
# Litres versés par fontaine pour les remplissages d'au moins 0,5 L
totaux = db.remplissages.aggregate([
    {"$match": {"volume": {"$gte": 0.5}}},
    {"$group": {"_id": "$fontaine_id", "litres": {"$sum": "$volume"}}},
])
```

`$match` filtre les documents comme `WHERE`. `$group` regroupe par la valeur de son `_id` et calcule les résultats comme `GROUP BY`. [Fiche sur les requêtes](03-requetes.md)

Dans HydroCégep, les remplissages et les événements sont des documents ponctuels. Les lectures de débit sont périodiques et vont dans une **collection de séries temporelles**. Pour repartir de zéro, le [script d’insertion](../insertion_donnees.py) supprime `lectures_debit`, puis la recrée avec `horodatage` comme `timeField` et `fontaine_id` comme `metaField`. [Fiche sur la modélisation](01-modelisation.md) · [Fiche sur l’insertion](02-insertion.md)
