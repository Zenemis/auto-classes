"""Raccourci de debug pour l'exécutable : les deux Ctrl enfoncés au lancement.

Une fois l'application distribuée en binaire, on la démarre d'un double-clic : il n'y a
plus de ligne de commande où écrire `--demo`. Tenir les deux touches Ctrl pendant le
démarrage rend le jeu d'essai accessible sans exposer de bouton dans l'interface — et
les *deux* Ctrl, parce qu'un seul est trop facile à laisser traîner par accident (un
Ctrl+clic sur le raccourci, par exemple).

L'état du clavier est lu via l'API Windows ; ailleurs, le raccourci n'existe pas et
`--demo` reste le seul chemin.
"""

import ctypes
import sys

# Codes des touches virtuelles Windows : Ctrl gauche et Ctrl droit. `VK_CONTROL` (0x11)
# ne distingue pas les deux, il ne permettrait pas d'exiger la combinaison.
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3

# `GetAsyncKeyState` renvoie l'état dans le bit de poids fort : à 1, la touche est
# enfoncée à l'instant de l'appel. Le bit de poids faible, lui, dit seulement qu'elle
# l'a été depuis le dernier appel — trop laxiste pour ce qu'on veut.
_PRESSED_BIT = 0x8000


def _async_key_state(virtual_key: int) -> int:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
    # Sans `restype` explicite, ctypes interprète le SHORT renvoyé comme un int 32 bits
    # et le bit de poids fort du short se retrouve au milieu de la valeur.
    user32.GetAsyncKeyState.restype = ctypes.c_short
    return user32.GetAsyncKeyState(virtual_key)


def both_control_keys_held() -> bool:
    """Vrai si Ctrl gauche et Ctrl droit sont enfoncés à cet instant.

    Toujours faux hors de Windows. Une erreur de chargement de `user32` (contexte sans
    session graphique) est traitée comme « pas de raccourci » : le démarrage normal de
    l'application ne doit dépendre d'aucune de ces conditions.
    """
    if sys.platform != "win32":
        return False
    try:
        left, right = _async_key_state(VK_LCONTROL), _async_key_state(VK_RCONTROL)
    except (AttributeError, OSError):
        return False
    return bool(left & _PRESSED_BIT) and bool(right & _PRESSED_BIT)
