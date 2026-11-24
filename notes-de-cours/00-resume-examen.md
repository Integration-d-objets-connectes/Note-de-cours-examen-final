# Révision d’examen · NoSQL

[Fiche MongoDB et équivalents SQL](04-fiche-mongodb.md)

| Étape | À savoir faire | Fiche |
|---|---|---|
| **1. Modéliser** | Champ courant, historique, intégration, référence, copie, relations 1:1 / 1:N / N:N | [Modélisation](01-modelisation.md) |
| **2. Insérer** | Créer la série temporelle, récupérer les IDs, générer les dates et vérifier les quantités | [Insertion](02-insertion.md) |
| **3. Interroger** | Filtrer, compter, projeter, trier, limiter, mettre à jour et agréger | [Requêtes](03-requetes.md) |

## HydroCégep en un coup d’œil

| Donnée | Où ? | Opération |
|---|---|---|
| Réglages et état du filtre | `fontaines` | `find_one`, `$set`, `$inc` |
| Débit par minute | `lectures_debit`, time series | Filtre par date + projection + tri |
| Bouteilles remplies | `remplissages` | Compte pour les bouteilles, somme de `volume` pour les litres |
| Alertes et changements | `evenements` | Type facultatif + tri décroissant + limite |
| Techniciens | `utilisateurs` | ID référencé dans les changements |

**Minimums** — 1 fontaine · 2 techniciens · 60 lectures · 20 remplissages dont au moins 5 aujourd’hui et 5 avant · 4 événements dont une alerte et un changement par technicien.

## Pièges à mémoriser

- **Aujourd’hui** → calcule minuit local, puis convertis-le en UTC.
- **Les n dernières minutes** → filtre par date. **Les n dernières lectures** → tri + limite.
- **Tous les types** → omets la clé `type` du filtre.
- **Changer le filtre** → ajoute un événement et mets à jour la date et le compteur dans la fontaine.
- **Plusieurs à plusieurs** → tableau d’IDs si la liste est petite. Collection d’assignations si le lien porte un rôle, des dates ou un historique.

## Trois questions éclair

| Question | Réponse |
|---|---|
| Les trois alertes les plus récentes d’hier ? | Type + deux bornes de la journée locale + tri décroissant + limite 3. |
| Pourquoi reculer de cinq minutes pour chaque bouteille peut poser problème ? | Juste après minuit, des dates passent à la veille. |
| Où ranger l’état du chauffage et son historique ? | État dans l’appareil, allumages dans les événements. |

[Énoncé HydroCégep](../README.md) · [Modélisation — 420-5P0](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation/modelisation) · [CRUD — 420-5P0](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/operations-crud)
