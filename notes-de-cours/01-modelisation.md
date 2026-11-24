# 1 · Modélisation

[Résumé](00-resume-examen.md) · [Insertion →](02-insertion.md)

## Quoi stocker ?

| Si l’énoncé dit… | Écris… | Exemple |
|---|---|---|
| Valeur courante | Champ à mettre à jour | `config.mode_auto` |
| Mesure à intervalle régulier | Série temporelle | Débit chaque minute, même à zéro |
| Événement ponctuel à conserver | Nouveau document ordinaire | Alerte, remplissage, changement de filtre |
| Valeur facile à calculer | Requête sur les données sources | Bouteilles aujourd’hui = compte depuis minuit |
| Compteur utilisé souvent | Champ tenu à jour | Litres depuis le dernier filtre |
| État actuel **et** historique | Champ courant + événement | Date du dernier changement + journal des changements |

## Où le mettre ?

| Relation | Exemple | Choix et raison |
|---|---|---|
| **1:1** | Fontaine → configuration | Sous-document `config`. Petit et lu avec la fontaine. |
| **1:1** | Fontaine → contrôleur avec sa fiche d’entretien | `controleur_id`. Le contrôleur a sa propre fiche. |
| **1:N borné** | Aquarium → trois actionneurs fixes | Tableau `actionneurs`. Petite liste lue avec l’appareil. |
| **1:N croissant** | Fontaine → lectures | `fontaine_id` dans chaque lecture. L’historique grandit. |
| **N:N implicite** | Tous les techniciens ont accès à toutes les fontaines | Règle commune. Aucun couple à enregistrer. |
| **N:N simple** | Quelques responsables par fontaine, chacun peut en suivre plusieurs | `technicien_ids: [lea_id, pierre_id]`. Petite liste de références. |
| **N:N avec historique** | Chaque affectation a un rôle et des dates | Collection `assignations` avec les deux IDs, le rôle, le début et la fin. |

- **Identifiant stable et unique** → `_id` choisi, par exemple `hydrocegep-01`. Sinon, `ObjectId` généré.
- **Nom historique à afficher** → garde la référence `utilisateur.id` et copie `utilisateur.nom`. Pour le nom actuel, lis la fiche.
- **Valeur au moment des faits** → copie le compteur dans l’alerte. Le compteur courant continue d’évoluer.
- **Dernière mesure affichée partout** → une copie avec sa date peut éviter une lecture. Le Pi doit garder cette copie à jour.

## Exemple HydroCégep

```python
from datetime import datetime, timezone

from bson import ObjectId

t = datetime(2026, 11, 24, 15, 42, tzinfo=timezone.utc)
fontaine_id = "hydrocegep-01"
technicien_id = ObjectId()

fontaine = {
    "_id": fontaine_id,
    "nom": "Fontaine du corridor TI",
    "config": {"mode_auto": True, "seuil_alerte_litres": 3000},
    "filtre": {"date_changement": t, "litres_depuis_changement": 0.0},
}
technicien = {"_id": technicien_id, "nom": "Léa"}
lecture = {"fontaine_id": fontaine_id, "horodatage": t, "debit": 0.0}
remplissage = {"fontaine_id": fontaine_id, "horodatage": t, "volume": 0.6}
changement = {
    "fontaine_id": fontaine_id,
    "horodatage": t,
    "type": "changement_filtre",
    "utilisateur": {"id": technicien_id, "nom": "Léa"},
}
alerte = {
    "fontaine_id": fontaine_id,
    "horodatage": datetime(2026, 11, 24, 14, 30, tzinfo=timezone.utc),
    "type": "alerte",
    "litres_depuis_changement": 3012.0,
}
```

Les fiches utilisent `seuil_alerte_litres`, comme les scripts. Le [modèle initial](../modele.md) utilise `duree_vie_filtre`. Garde le même nom dans tes trois parties.

**À justifier sous chaque document** — Type de collection, `_id`, chaque sous-document ou tableau, chaque référence et chaque copie.

[Analyse et modélisation — 420-5P0](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation) · [Choix de modélisation — 420-5P0](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation/modelisation)
