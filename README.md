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
    core/       # logique métier (à venir)
    rules/      # règles de répartition, y compris règles customisées (à venir)
    ui/         # interface CustomTkinter
    cli/        # interface en ligne de commande pour le debug
tests/
build/          # scripts de bundling Nuitka
```

## Développement

```bash
pip install -e ".[dev]"
python -m auto_classes.cli          # lance la CLI
python -m auto_classes.ui           # lance l'UI
```

## Build (Nuitka)

```bash
python build/build.py
```
