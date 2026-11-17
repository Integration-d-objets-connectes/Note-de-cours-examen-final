# Modèle NoSQL - HydroCégep

## Collection `fontaines`

```python
fontaine = {
    "_id": "hydrocegep-01",
    "nom": "Fontaine du corridor TI",
    "config": {"mode_auto": True, "duree_vie_filtre": 3000},
    "filtre": {
        "date_changement": datetime(2026, 11, 6, 14, 12, tzinfo=timezone.utc),
        "litres_depuis_changement": 1840.5,
    },
}
```

## Collection `lectures_debit` (time series)

```python
lecture = {
    "horodatage": datetime(2026, 11, 17, 15, 42, tzinfo=timezone.utc),
    "fontaine_id": "hydrocegep-01",
    "debit": 1.8,
}
```

## Collection `remplissages`

```python
remplissage = {
    "horodatage": datetime(2026, 11, 17, 15, 41, 20, tzinfo=timezone.utc),
    "fontaine_id": "hydrocegep-01",
    "volume": 0.6,
}
```

## Collection `evenements`
Même collection, plusieurs types d'événements.

Le changement de filtre fait référence à un utilisateur car on veut savoir qui a changé le filtre, 
mais pas dans le signalement du filtre. 

```python
changement_filtre = {
    "horodatage": datetime(2026, 11, 6, 14, 12, tzinfo=timezone.utc),
    "fontaine_id": "hydrocegep-01",
    "type": "changement_filtre",
    "utilisateur": {"id": ObjectId("6738a1f0e4b0a1b2c3d4e5f6"), "nom": "Pierre"},
}

signalement_filtre = {
    "horodatage": datetime(2026, 11, 5, 21, 40, tzinfo=timezone.utc),
    "fontaine_id": "hydrocegep-01",
    "type": "alerte",
    "litres_depuis_changement": 3012.0,
}
```

## Collection `utilisateurs`
```python
utilisateur = {"_id": ObjectId("6738a1f0e4b0a1b2c3d4e5f6"), "nom": "Pierre"}
```