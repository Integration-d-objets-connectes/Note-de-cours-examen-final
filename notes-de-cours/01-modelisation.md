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

## Décider ligne par ligne à partir de la maquette

Pour chaque case de la maquette ou règle automatique, note la **source**, le **type et l’unité**, ce qui **remplace ou s’ajoute**, la **fréquence**, l’**usage** et la **durée de conservation**. Compare cette grille avec ce que le matériel fournit. Si une donnée est calculée à l’affichage, indique les données nécessaires au calcul. [Analyse et modélisation — 420-5P0](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation)

| Besoin | Source et fréquence | Décision et raison |
|---|---|---|
| Mode automatique | Technicien, à chaque modification | Champ booléen dans `config`. La valeur courante remplace l’ancienne. |
| Graphique du débit | Débitmètre et Pi, chaque minute | Série temporelle. Une mesure par minute, y compris à zéro. |
| Nombre de bouteilles aujourd’hui | Calcul à l’affichage | Compte les remplissages depuis minuit local. Le total découle des documents déjà stockés. |
| Nombre de litres depuis le dernier filtre | Pi, quand un volume est comptabilisé | Compteur courant dans `filtre`. Il évite de recalculer l’état à chaque lecture. |
| « Filtre changé il y a 2 h » | Calcul à partir du dernier changement | Stocke l’horodatage. Calcule l’écart avec l’heure actuelle à l’affichage. |
| Alerte avec le volume au déclenchement | Règle du Pi, ponctuelle | Événement ordinaire. Garde une copie du compteur au moment du déclenchement. |
| Coupure d’eau en mode automatique | Décision du Pi au seuil | La décision utilise le mode, le seuil et le compteur. Si la maquette demande aussi « Eau coupée », prévois un état de l’actionneur. Si l’énoncé exige un journal des coupures, ajoute des événements distincts. |

Dans le DFD, trace **débitmètre → service du Pi → lectures** pour les mesures et **technicien → application/API → fontaines + événements** pour le changement de filtre. La première écriture ajoute une mesure. Le changement de filtre remplace l’état courant et ajoute un fait à l’historique.

## Cardinalités et choix de représentation

La cardinalité dit **combien de documents peuvent être liés de chaque côté**. Elle te donne des options. Pour choisir, vérifie si la relation est bornée, si les entités vivent indépendamment et dans quel sens l’écran doit lire les données. Les scénarios ci-dessous prolongent les critères du cours. [Modélisation — 420-5P0](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation/modelisation)

| Relation | Cas | Modèle plausible | Justification |
|---|---|---|---|
| **1:1** | Une fontaine a une seule configuration courante | `fontaine.config = {"mode_auto": True}` | Configuration petite, propre à la fontaine et lue avec elle. |
| **1:1** | Chaque fontaine possède un contrôleur qui a sa propre fiche de maintenance | `fontaine.controleur_id` | Le contrôleur peut être consulté ou remplacé indépendamment. Si le lien doit rester exclusif, il faut le faire respecter. |
| **1:N borné** | Un aquarium a un maximum de trois actionneurs affichés ensemble | `aquarium.actionneurs = [{"nom": "chauffage", "etat": "on"}]` | Groupe petit, propre à l’appareil et lu avec lui. |
| **1:N croissant** | Une fontaine produit une mesure chaque minute | Chaque mesure contient `fontaine_id` | L’historique grandit indépendamment. Filtre les documents enfants par fontaine et date. |
| **N:N implicite** | Plusieurs techniciens ont tous accès à toutes les fontaines selon une règle commune | Règle d’accès fondée sur le rôle | Les couples sont déductibles de la règle. Dans HydroCégep, tous les techniciens ont accès à l’unique fontaine. |
| **N:N, petite liste** | Chaque fontaine a quelques techniciens assignés, sans information propre au lien | `fontaine.technicien_ids = [lea_id, pierre_id]` | Liste bornée d’identifiants. Chaque technicien conserve une seule fiche. |
| **N:N, lien indépendant** | Une fontaine a plusieurs techniciens. Un technicien suit plusieurs fontaines. Chaque assignation a un rôle et une durée | Collection `assignations` avec `fontaine_id`, `technicien_id`, `role`, `debut`, `fin` | Le lien a des attributs, peut être consulté dans les deux sens et peut avoir son propre historique. |

**Attention au sens de la relation.** Avec une collection `assignations`, les techniciens d’une fontaine se trouvent avec `{"fontaine_id": fontaine_id}`. Les fontaines d’un technicien se trouvent avec `{"technicien_id": lea_id}`. Dans la variante avec un tableau de références, les fontaines de Léa se trouvent avec `db.fontaines.find({"technicien_ids": lea_id})`. Maintenir une liste des deux côtés ajoute deux écritures à synchroniser à chaque changement.

**Un changement de filtre et une assignation répondent à deux questions.** L’événement répond à « qui a changé quel filtre et quand ? ». L’assignation répond à « qui est responsable de quelle fontaine sur cette période ? ». Un même couple technicien-fontaine peut apparaître plusieurs fois dans l’historique des changements.

## Trois arbitrages typiques

- **Dernière lecture ou copie dans l’appareil.** Si l’écran affiche rarement le débit courant, lis la mesure la plus récente. Si le tableau de bord lit toujours l’état de la fontaine et le débit ensemble, tu peux garder `derniere_lecture` avec l’heure et la valeur. Le service du Pi doit alors maintenir la copie, qui représente la dernière mesure connue.
- **Alertes et changements ensemble ou séparés.** Les deux types vont dans `evenements` si l’écran affiche les trois derniers tous types confondus. Les remplissages peuvent rester dans leur collection parce qu’ils sont nombreux et surtout consultés pour des compteurs.
- **Nom copié ou nom récupéré.** Copie le nom avec l’ID si l’historique doit l’afficher tel qu’il était au moment du changement. Récupère le document du technicien si l’écran doit afficher son nom actuel après un changement de nom.

**Phrase d’examen** — « Je mets ___ dans ___ parce que l’écran ou la règle ___ en a besoin. La valeur ___, et la relation est ___. Ce choix implique ___ lors de la lecture ou de la mise à jour. »
