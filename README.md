# fresko-donnees

Les données des villes que l'app **Fresko** télécharge à la demande : pour
chaque ville, le réseau piéton avec l'ombre de chaque rue heure par heure
(trois saisons), les parcs ombragés, les points d'eau et quelques lieux
utiles.

Une ville publiée ici apparaît dans l'app **sans mise à jour de l'app** :
celle-ci relit le catalogue au démarrage et propose la ville (ou sa
nouvelle version) dans le choix de la ville.

| Ville | Version | Zone |
|---|---|---|
| Paris | voir [`villes.json`](villes.json) | Métropole du Grand Paris |

Grenoble est intégrée directement à l'app et n'est pas publiée ici.

## Comment c'est organisé

- **[`villes.json`](villes.json)**, le catalogue : une entrée par ville,
  avec son nom, son centre, sa version et, pour chaque fichier, son
  adresse, sa taille et son empreinte SHA-256.
- **Les releases** : les fichiers d'une ville sont attachés à une release
  nommée `<ville>-v<version>` (ex. `paris-v1`). Une release publiée ne se
  modifie plus : une nouvelle version = une nouvelle release.

L'app refuse un fichier dont la taille ou l'empreinte ne correspond pas au
catalogue : un téléchargement tronqué ou un fichier remplacé par erreur
n'est jamais chargé.

### Les fichiers d'une ville

| Fichier | Contenu |
|---|---|
| `graphe_routage.bin` | Réseau piéton, ombre de chaque tronçon de 8 h à 20 h (été, équinoxe, hiver), obstacles pour le profil poussette/PMR (escaliers, surfaces difficiles) |
| `parcs_ombrages.json` | Parcs et jardins, avec leur part d'ombre |
| `fontaines.json` | Points d'eau potable |
| `restaurants.json` | Restaurants et restauration rapide |
| `parking.json` | Parkings |
| `pharmacies.json` | Pharmacies |
| `distributeurs.json` | Distributeurs de billets |

## Publier une ville (ou une nouvelle version)

Les fichiers se fabriquent avec le **kit ville** (`fresko-kit-ville.zip`,
voir le dépôt `fresko-python`) : on choisit une zone (commune, quartier,
cercle ou zone dessinée), on dépose la BD TOPO de l'IGN du ou des
départements, et le kit produit un dossier `A_PUBLIER/<ville>-v<version>`.

Puis, **dans cet ordre** :

1. **Release** : [Releases > Draft a new release](../../releases/new),
   tag = le nom du dossier (ex. `paris-v2`), joindre tous les fichiers du
   dossier **sauf `villes.json`**, puis « Publish release ».
2. **Catalogue** : remplacer `villes.json` à la racine de ce dépôt par
   celui du dossier.

L'ordre compte : si le catalogue est mis à jour avant la release, l'app
voit une nouvelle version dont les fichiers n'existent pas encore, et le
téléchargement échoue.

Le `villes.json` produit par le kit reprend le catalogue en ligne au
moment du calcul, avec la ville ajoutée ou remplacée. Si une autre ville a
été publiée entre-temps, relancer le kit (les calculs longs, ombres
comprises, sont gardés : il ne refait que les dernières étapes, quelques
minutes) ou fusionner les deux catalogues à la main.

### Versions

- Une nouvelle ville commence en version 1.
- Pour mettre à jour une ville, on publie la version suivante sous le
  **même identifiant** (`"id"`) : l'app de chacun propose alors
  « Nouvelle version de … disponible ». Le kit calcule la version tout
  seul ; pour remplacer une ville existante, renseigner son `ID` dans
  `ZONE.txt`.
- Les anciennes releases peuvent rester : l'app ne télécharge que la
  version du catalogue.

## Données et licences

- Réseau piéton, arbres, parcs, points d'eau, lieux :
  © les contributeurs d'[OpenStreetMap](https://www.openstreetmap.org/copyright),
  sous licence ODbL.
- Bâtiments et hauteurs (calcul des ombres) :
  [BD TOPO®](https://geoservices.ign.fr/bdtopo) de l'IGN, Licence Ouverte
  Etalab 2.0.
