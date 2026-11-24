# Fiche 1 — Modélisation NoSQL

[Insertion →](02-insertion.md)

## 1. Repérer les données dans l’énoncé

| Indice | Document ou champ |
|---|---|
| « Modifier le mode automatique » | Configuration courante dans `fontaines.config` |
| « Litres depuis le dernier changement » | Date et compteur dans `fontaines.filtre` |
| « Chaque minute, même à zéro » | Un document par mesure dans `lectures_debit` |
| « À chaque bouteille » | Un document par remplissage avec le volume en litres |
| « Conserver les alertes et les changements » | Un document par événement avec un champ `type` |
| « Par quel technicien » | Une référence à `utilisateurs._id` |

## 2. Choisir le type de collection et le _id

| Collection | Type et justification | Identifiant |
|---|---|---|
| `fontaines` | Ordinaire. On modifie principalement l’état courant. | Identifiant métier stable, par exemple `hydrocegep-01` |
| `utilisateurs` | Ordinaire. Chaque technicien a sa fiche. | ObjectId généré |
| `lectures_debit` | Time series. Mesures périodiques consultées par fenêtre de temps. | ObjectId généré |
| `remplissages` | Ordinaire dans cet exercice. Chaque bouteille donne lieu à un enregistrement ponctuel. | ObjectId généré |
| `evenements` | Ordinaire. Alertes et changements sont des faits ponctuels qu’on affiche ensemble. | ObjectId généré |

Pour une variante, justifie le type de collection par la nature des données et les accès attendus. Un horodatage peut aussi figurer dans une collection ordinaire.

## 3. Intégrer, référencer ou copier

| Patron | Quand l’utiliser | Exemple |
|---|---|---|
| Sous-document | Petit ensemble de champs appartenant au parent et lus avec lui | `config`, `filtre` |
| Tableau intégré | Liste bornée dont les éléments appartiennent au parent | Petite liste de réglages prédéfinis |
| Référence | Entité indépendante ou historique qui peut croître | `fontaine_id`, `utilisateur.id` |
| Copie pour l’affichage | Éviter une lecture supplémentaire et, selon le besoin, garder la valeur historique | `utilisateur.nom` dans un changement |
| Valeur historique | Figer une valeur au moment d’un événement | Litres au moment d’une alerte |
| Compteur maintenu | Lire souvent un total courant sans parcourir son historique | Litres depuis le dernier changement |

## 4. Écrire un exemple réaliste par collection

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

Les exemples emploient `seuil_alerte_litres`, comme les scripts. Le [modèle du dépôt](../modele.md) emploie `duree_vie_filtre` pour ce réglage. À l’examen, utilise le même nom dans le modèle, l’insertion et les requêtes.

## Variantes à reconnaître

- **Plusieurs fontaines** → garde `fontaine_id` dans les historiques et filtre les écrans propres à une fontaine.
- **Techniciens assignés à des fontaines** → une liste bornée de références peut suffire. Si l’assignation a un rôle, des dates ou son propre historique, envisage une collection d’assignations.
- **Historique des réglages** → garde la configuration courante et écris un événement avec les réglages modifiés.
- **Nom actuel ou nom au moment des faits** → lis la fiche du technicien pour son nom actuel. Copie le nom dans l’événement pour conserver la valeur historique.
- **Bouteilles ou litres** → compte les documents pour les bouteilles et additionne `volume` pour les litres. Le débit est un taux en L/min. Pour en tirer un volume, tiens compte de la durée représentée par chaque mesure.

**Avant de remettre** — Sous chaque exemple, justifie le type de collection, le choix du `_id`, chaque sous-document ou tableau, chaque référence et chaque valeur copiée.
