"""Erreurs de la connexion Pronote, déjà formulées pour l'utilisateur.

L'UI se contente d'afficher `str(error)` : c'est ici, au contact de pronotepy, qu'on
sait distinguer un mot de passe erroné d'un espace inaccessible, et c'est donc ici que
le message est rédigé — avec, quand c'est possible, la marche à suivre.
"""


class PronoteError(Exception):
    """Échec d'une connexion ou d'une récupération, avec un message affichable tel quel."""
