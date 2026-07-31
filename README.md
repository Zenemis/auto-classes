# auto-classes

Application pour automatiser la création de classes d'élèves respectant des règles
(avec possibilité d'écrire des règles personnalisées).

## Stack

- Python
- CustomTkinter (UI)
- pronotepy (import des élèves depuis Pronote)
- CLI (debug)
- Nuitka (bundling)

## Structure

```
src/auto_classes/
    core/       # entités métier (Student, Classroom, ClassroomSet)
    rules/      # contraintes, y compris règles customisées
    algorithm/  # génération des répartitions (backtracking)
    pronote/    # import des listes d'élèves depuis Pronote (pronotepy)
    serialization/  # config JSON, et lecture des listes d'élèves en CSV
    ui/         # interface CustomTkinter
    cli/        # interface en ligne de commande pour le debug
tests/
build/          # scripts de bundling Nuitka
```

### Import CSV

Le bouton **Importer** ouvre un fichier CSV — typiquement un export Pronote — et n'en
lit que les colonnes **Nom** et **Prénom**. Tout le reste (date de naissance, classe,
projet d'accompagnement, allergies) est ignoré : rien de tout cela ne sert à la
répartition, et une partie relève de données sensibles.

Si l'une des deux colonnes manque, le fichier est refusé, avec la liste des colonnes
effectivement trouvées — sans quoi l'utilisateur ne sait pas si son fichier a été mal
découpé ou mal nommé.

Sont reconnus sans réglage : le point-virgule, la virgule et la tabulation ; l'UTF-8
(avec ou sans BOM) et l'ANSI Windows ; les libellés en majuscules, sans accent ou entre
guillemets ; les colonnes dans n'importe quel ordre. « Prénom d'usage », voisine de
« Prénom » dans les exports Pronote, n'est jamais prise pour elle.

Les noms sont importés sous la forme « NOM Prénom », la même que l'import Pronote en
ligne : un élève entré par les deux chemins n'apparaît qu'une fois.

Deux fichiers d'essai dans `samples/`, écrits comme un vrai export Pronote
(point-virgule, ANSI Windows, fins de ligne CRLF) :

| Fichier | Ce qu'il sert à voir |
| --- | --- |
| `eleves-cm2c.csv` | un import nominal : 23 élèves d'un CM2 |
| `eleves-sans-colonne-prenom.csv` | le refus : « Prénom » absente, « Prénom d'usage » présente |

Les élèves sont fictifs.

### Import Pronote

Le bouton **Pronote** ouvre une fenêtre de connexion (adresse de l'établissement,
identifiant, mot de passe, ENT facultatif), puis importe tous les élèves des classes
accessibles au compte.

**Limite importante : un compte Professeurs ne fonctionne pas.** pronotepy ne gère que
les espaces Élève, Parent et — partiellement — Vie scolaire, et seul l'espace **Vie
scolaire** publie les listes de classes de l'établissement. Un enseignant doit donc
obtenir un accès Vie scolaire auprès de son établissement. L'application le diagnostique
et le dit ; elle ne peut pas le contourner.

Deux détails pris en charge automatiquement :

- l'adresse saisie est réécrite vers `viescolaire.html`, quelle que soit la page fournie
  (`professeur.html`, `eleve.html`, ou la racine `/pronote/`) ;
- un élève inscrit dans deux classes (groupe d'option) n'est importé qu'une fois.

Les échecs sont traduits en messages actionnables : identifiants refusés, ENT, double
authentification, serveur injoignable, compte sans accès aux classes.

### UI

```
ui/
    theme.py        jetons de style : couleurs, métriques, polices, glyphes
    models.py       entités éditables (id stable, survivent aux renommages)
    session.py      état de la session en mémoire + signaux de rafraîchissement
    interaction.py  élève sélectionné et outil de contrainte armé
    generation.py   appel de generate_classes hors du thread Tk
    components/     briques réutilisables, sans connaissance du modèle
    views/          une classe par zone d'écran
    app.py          fenêtre principale, assemblage des deux onglets
```

Les vues ne se parlent jamais directement : elles écrivent dans `SessionState` /
`InteractionState` et se rafraîchissent sur leurs signaux. Rien n'est persisté entre
deux lancements du logiciel.

Deux onglets :

- **Configuration** — bande de menu (importer, Pronote, générer), bande des classes
  (nom, effectifs, tags), bande des élèves avec l'inspecteur de contraintes à droite.
- **Propositions** — liste des propositions à gauche, détail de la proposition
  sélectionnée à droite.

## Développement

```bash
pip install -e ".[dev]"
python -m auto_classes.cli --config config.json   # lance la CLI
python -m auto_classes.ui                         # lance l'UI
python -m auto_classes.ui --demo                  # UI avec un jeu d'essai
```

### Mode debug de l'exécutable

Le binaire se lance d'un double-clic : il n'y a pas de ligne de commande où écrire
`--demo`. Tenir **les deux touches Ctrl** (gauche *et* droite) au démarrage a le même
effet. Il faut les maintenir jusqu'à l'ouverture de la fenêtre : l'exécutable *onefile*
se décompresse d'abord, et l'état du clavier n'est lu qu'au démarrage de Python.

Le raccourci exige les deux Ctrl pour ne pas se déclencher sur un Ctrl+clic malencontreux
sur le raccourci de lancement, et il ne lit que l'état *courant* des touches : un Ctrl
relâché juste avant ne compte pas. Hors de Windows, il n'existe pas.

Les tests :

```bash
python -m pytest          # tests unitaires + tests d'intégration (oracle par force brute)
python -m pytest tests    # tests unitaires seuls
```

## Build (Nuitka)

```bash
python build/build.py
```

Produit dans `dist/` un exécutable autonome nommé d'après la version et la plateforme
(`auto-classes-0.1.0-windows-x86_64.exe`) accompagné de son empreinte `.sha256`.

| Option | Effet |
| --- | --- |
| `--output-dir DIR` | dossier de sortie (défaut `dist/`) |
| `--no-checksum` | ne pas écrire le `.sha256` |
| `--dry-run` | afficher la commande Nuitka sans compiler |
| `--print-version` | afficher la version du paquet |

Nuitka ne sait pas lier le Python distribué par le Microsoft Store (pas de
`python3xx.lib`) : il faut un CPython de python.org. Le script s'arrête avec un message
explicite plutôt que d'échouer dix minutes plus tard dans le backend C.

## CI / CD

- **CI** (`.github/workflows/ci.yml`) — sur chaque PR et sur `main` : toute la suite de
  tests, sous Python 3.11, 3.13 et 3.14, sur Windows (les tests d'UI ont besoin d'un vrai Tk).
- **CD** (`.github/workflows/cd.yml`) — sur `main` et sur les tags `v*` : rejoue la CI,
  puis construit l'exécutable et le publie comme artefact de build.
- **Release** — sur un tag `vX.Y.Z` : les empreintes sont revérifiées, puis une release
  GitHub est créée avec les `.exe` et leurs `.sha256`. Le tag doit correspondre au
  `__version__` du paquet, sinon le build s'arrête.

Publier une version :

```bash
git tag v0.1.0 && git push origin v0.1.0
```

Vérifier un binaire téléchargé :

```bash
sha256sum --check auto-classes-0.1.0-windows-x86_64.exe.sha256
```

Le blocage des PR rouges est un réglage du dépôt, pas du dépôt de code : dans
*Settings → Rules / Branch protection* sur `main`, exiger les checks
`Tests (Python 3.11)`, `Tests (Python 3.13)` et `Tests (Python 3.14)`.
