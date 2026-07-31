# auto-classes

Application pour automatiser la création de classes d'élèves respectant des règles
(avec possibilité d'écrire des règles personnalisées).

## Stack

- Python
- CustomTkinter (UI)
- CLI (debug)
- Nuitka (bundling)

## Structure

```
src/auto_classes/
    core/       # entités métier (Student, Classroom, ClassroomSet)
    rules/      # contraintes, y compris règles customisées
    algorithm/  # génération des répartitions (backtracking)
    serialization/
    ui/         # interface CustomTkinter
    cli/        # interface en ligne de commande pour le debug
tests/
build/          # scripts de bundling Nuitka
```

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
