# Modèle NoSQL - HydroCégep

## Collection `fontaines`
C'est une collection ordinaire, car les valeurs de la fontaine remplacent les anciennes au lieu de s'ajouter. Le `_id` est choisi, car la fontaine a déjà un identifiant unique et stable, plus lisible qu'un `ObjectId` dans les références. Un `ObjectId` généré serait aussi correct, avec le nom gardé comme champ ordinaire.

La configuration et l'état du filtre sont intégrés dans la fontaine, car ils lui appartiennent, sont petits et sont lus avec elle. Le champ `litres_depuis_changement` est un compteur tenu à jour par le Raspberry Pi : il évite d'additionner toutes les lectures depuis le dernier changement. (dans le cas contraire, il faudrait faire la somme de toutes les lectures de débit depuis le changement. C'est une agrégation ($sum) sur des milliers de documents, refaite à chaque affichage. On garde donc un compteur, que le Pi augmente à chaque lecture et que le technicien remet à zéro au changement de filtre.).

Le nombre de bouteilles n'est pas stocké, car il suffit de compter les documents de remplissages.


```python
fontaine = {
    "_id": "hydrocegep-01",
    "nom": "Fontaine du corridor TI",
    "config": {"mode_auto": True, "seuil_alerte_litres": 3000},
    "filtre": {
        "date_changement": datetime(2026, 11, 6, 14, 12, tzinfo=timezone.utc),
        "litres_depuis_changement": 1840.5,
    },
}
```

## Collection `lectures_debit` (time series)
C'est une collection *time series*, car le débit est une mesure périodique (toutes les x sec/min/heure), prise chaque minute, qui s'ajoute sans limite. Le `_id` est un `ObjectId` généré, car rien d'autre que l'heure n'identifie une lecture. Chaque lecture fait référence à la fontaine, car l'historique est illimité et ne peut pas être intégré dans le document de la fontaine.


```python
lecture = {
    "horodatage": datetime(2026, 11, 17, 15, 42, tzinfo=timezone.utc),
    "fontaine_id": "hydrocegep-01",
    "debit": 1.8,
}
```

## Collection `remplissages`
C'est une collection ordinaire, car un remplissage est ponctuel : un document est créé à chaque bouteille, et non à intervalle régulier. Le `_id` est un `ObjectId` généré, et chaque remplissage fait référence à la fontaine pour la même raison citée précédemment.

Les remplissages sont séparés des événements, car ils sont très nombreux et ne sont jamais affichés avec eux. Il serait aussi correct de les mettre dans `evenements` avec le type `"remplissage"`, à condition de les exclure de la liste des derniers événements. Un compteur `bouteilles_total` dans la fontaine, augmenté à chaque bouteille, serait également acceptable. Un compteur pour "aujourd'hui" serait à éviter, car il faudrait le remettre à zéro chaque nuit.


```python
remplissage = {
    "horodatage": datetime(2026, 11, 17, 15, 41, 20, tzinfo=timezone.utc),
    "fontaine_id": "hydrocegep-01",
    "volume": 0.6,
}
```

## Collection `evenements`
C'est une collection ordinaire, car les événements sont des faits ponctuels (pas à une fréquence régulière). Les deux types sont dans la même collection, car ils sont affichés ensemble dans la liste des derniers événements. Une collection par type serait aussi correcte, mais la liste « tous les types » demanderait alors deux requêtes. Le `_id` est un `ObjectId` généré, et chaque événement fait référence à la fontaine, car l'historique est illimité.

Le changement de filtre contient un sous-document `utilisateur`, car on veut savoir qui a changé le filtre. Son `id` est une référence vers `utilisateurs`, car un technicien existe indépendamment des événements et apparaît dans plusieurs d'entre eux. Son `nom` est une copie, qui permet d'afficher « Filtre changé par Pierre » sans lire la collection `utilisateurs` ; c'est acceptable, car un nom change rarement.

Le signalement du filtre n'a pas d'utilisateur, car c'est le Raspberry Pi qui le déclenche. Il garde la valeur de `litres_depuis_changement` au moment du signalement, car le compteur de la fontaine continue d'avancer ensuite.

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
C'est une collection ordinaire, séparée des événements, car un technicien existe par lui-même et apparaît dans plusieurs événements. Le `_id` est un `ObjectId` généré, car rien n'identifie naturellement un technicien dans ce contexte.


```python
utilisateur = {"_id": ObjectId("6738a1f0e4b0a1b2c3d4e5f6"), "nom": "Pierre"}
```
