"""Interface CustomTkinter d'auto-classes.

Découpage :
    theme        jetons de style (couleurs, métriques, polices, glyphes)
    models       entités éditables par l'UI, converties vers `core`/`rules`
    session      état de la session en mémoire + signaux de rafraîchissement
    interaction  sélection courante et outil de contrainte armé
    generation   exécution de `generate_classes` hors du thread Tk
    components   briques réutilisables, indépendantes du modèle
    views        une classe par zone d'écran
    app          fenêtre principale et point d'entrée `run()`

`run` n'est pas réexporté ici : importer `auto_classes.ui` ne doit pas construire de
police ni toucher à Tk. Passer par `auto_classes.ui.app`.
"""
