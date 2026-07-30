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

## Build (Nuitka)

```bash
python build/build.py
```
