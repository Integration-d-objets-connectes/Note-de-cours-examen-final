# Résumé d’examen — NoSQL (420-5P0)

[Fiche modélisation](01-modelisation.md) · [Fiche insertion](02-insertion.md) · [Fiche requêtes](03-requetes.md) · [Énoncé HydroCégep](../README.md)

## 1. Passer de l’énoncé au modèle

1. **Pars de la maquette et des décisions du Pi.** Pour chaque donnée, indique qui la produit, son type et son unité, où elle est utilisée et pendant combien de temps on doit la garder. Vérifie que le matériel produit les données nécessaires. Si un résultat se déduit facilement, prévois les données sources et calcule-le à la lecture. [Analyse et modélisation](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation)
2. **Remplace ou s’ajoute ?** Le mode automatique remplace une valeur, donc champ courant. Le débit mesuré toutes les minutes s’ajoute, donc série temporelle. Une alerte ponctuelle s’ajoute, donc document dans une collection ordinaire. Une action peut avoir les deux effets, comme changer le filtre et garder la trace du changement. [Modélisation](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation/modelisation)
3. **Intègre, référence ou copie.** Sous-document pour de petits champs lus ensemble. Tableau pour une liste bornée. Référence pour une entité partagée ou un historique croissant. Copie minimale pour l’affichage fréquent ou pour figer une valeur historique. Exemple `utilisateur.id` pointe vers la fiche et `utilisateur.nom` permet l’affichage de l’événement. [Modélisation](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/analyse-et-modelisation/modelisation)
4. **Choisis le `_id`.** Utilise un identifiant métier unique et stable comme `hydrocegep-01`, ou un `ObjectId` généré. Réutilise la valeur et le type exacts dans les références. [NoSQL — Modèle document](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/nosql-modele-document)

## 2. Préparer et vérifier tes insertions

- Crée la série temporelle avant sa première insertion. `timeField` désigne la date, `metaField` identifie la source de la mesure, `granularity` décrit l’échelle temporelle et une durée de conservation peut être définie si le besoin le prévoit. [Opérations CRUD](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/operations-crud)
- Insère les entités indépendantes et récupère leurs identifiants avec `inserted_id`. Fabrique ensuite des listes pour `insert_many`. Les dates sont des `datetime` avec fuseau. Pour « aujourd’hui », calcule d’abord minuit dans le fuseau local. [MongoDB](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/mongodb)
- Pour HydroCégep, vérifie séparément les **60 mesures**, les **20 remplissages**, les **5 minimum de chaque côté de minuit** et la **présence d’un changement par technicien et d’une alerte** parmi les quatre événements. Compare la date du compteur courant à celle du dernier changement. [Énoncé HydroCégep](../README.md)

## 3. Écrire la requête dans le bon ordre

| Si la consigne dit… | Écris… |
|---|---|
| Combien de bouteilles depuis minuit ? | `count_documents` avec date et fontaine |
| Combien de litres ? | `$match` puis `$group` avec `{"$sum": "$volume"}` |
| Seulement le débit et l’heure | Projection `{"_id": 0, "debit": 1, "horodatage": 1}` |
| Les trois derniers | Tri décroissant sur l’heure puis `limit(3)` |
| Les dix dernières minutes | Filtre sur l’heure avec `$gte` et tri selon l’affichage |
| Les alertes ou les changements | `{"type": {"$in": ["alerte", "changement_filtre"]}}` |
| Type facultatif | Ajoute la clé `type` uniquement quand une valeur est fournie |
| Changer un réglage | `update_one` avec `$set` et le chemin pointé |
| Ajouter un volume au compteur | `$inc` sur le chemin du compteur |
| Modifier un actionneur dans un tableau | Filtre sur son nom, puis `$set` sur `actionneurs.$.etat` |
| Moyenne par heure | `$match`, `$group` par `$dateTrunc` avec `$avg`, puis `$sort` |
| Changer le filtre | `insert_one` dans l’historique, puis `$set` de la date et du compteur à zéro |

Avec `find`, sépare le filtre (quels documents) de la projection (quels champs). Avec `find_one`, passe le tri via `sort=[("horodatage", -1)]` si tu veux le plus récent. Dans `$group`, `_id: None` rassemble tous les documents filtrés et `_id: "$fontaine_id"` donne un groupe par fontaine. [Opérations CRUD](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/base-de-donnees-nosql/operations-crud)

## Mini-examen corrigé

1. **AquaVeille affiche l’état actuel du chauffage et ses vingt derniers allumages. Où ranger ces informations ?** L’état courant peut être intégré à l’appareil. Les allumages sont des événements horodatés qui référencent l’appareil. L’écran en affiche vingt, mais l’ensemble peut continuer de croître.
2. **Trois capteurs fixes par appareil, chacun produit des mesures chaque minute. Quel modèle ?** Les descriptions des trois capteurs peuvent être intégrées si elles appartiennent à l’appareil et sont lues avec lui. Les mesures vont dans une série temporelle avec une métadonnée qui identifie la source, par exemple l’appareil et le capteur.
3. **Une liste de responsables doit afficher le rôle, la date d’affectation et les anciennes affectations. Quel modèle ?** Un document d’assignation par période, avec les deux identifiants, le rôle et les dates. L’historique des assignations s’interroge séparément.
4. **On veut les trois alertes les plus récentes d’hier. Quel ordre ?** Filtre sur le type et sur les deux bornes de la journée locale, trie par date décroissante et limite à trois.
5. **Il est 00 h 02 et ton insertion génère dix dates espacées de cinq minutes en reculant depuis maintenant. Quelle contrainte casse ?** La plupart des dates passent à la veille. Génère les dates d’aujourd’hui à l’intérieur de l’intervalle entre minuit et maintenant.
6. **Un tableau de bord affiche cinq bouteilles et trois litres. D’où viennent les valeurs ?** Cinq est le nombre de documents de la période. Trois est la somme de leurs champs `volume`.
