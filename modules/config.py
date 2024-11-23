# modules/config.py

from modules import defaults
import argparse
import os

# Dictionary to store configuration values 
config_values = {
    'directories': None,
    'screen': None,
    'days': None,
    'number': None,
    'total_number': None,
    'bestfit': None,
    'panscan': None,
    'volume': None,
    'singleloop': None,
    'max': None,
    'verbose': None,
    'quiet': None,
}
_config_initialized = False  # Variable interne pour vérifier l'initialisation

def setup_config():
    """
    Initialise la configuration de l'application en combinant les valeurs par défaut,
    les paramètres utilisateur et les arguments en ligne de commande.

    Cette fonction doit être appelée une seule fois, généralement depuis le point d'entrée principal (par exemple, main.py).

    Elle met à jour les variables de configuration au niveau du module pour qu'elles soient accessibles par les autres modules.
    """
    global config_values, _config_initialized
    if _config_initialized:
        return  # Ne pas refaire le traitement si déjà initialisé

    # Étape 1 : Copier les variables depuis defaults.py
    for var_name in dir(defaults):
        if not var_name.startswith('__'):
            var_value = getattr(defaults, var_name)
            config_values[var_name] = var_value

    # Étape 2 : Ajouter ou mettre à jour des variables si nécessaire
    # Par exemple, mettre à jour le volume par défaut
    # Vous pouvez personnaliser cette partie selon vos besoins

    # Étape 3 : Traitement des arguments en ligne de commande
    parser = argparse.ArgumentParser(description="Video Wall")
    parser.add_argument('-s', '--screen', type=int, help='Screen number')
    parser.add_argument('-n', '--number', type=int, default=1, help='Number of players per screen')
    parser.add_argument('-N', '--total-number', type=int, default=None, help='Total number of players, overrides -n')
    parser.add_argument('-b', '--bestfit', action='store_true', help='Try to fit the best number of players on the screens')
    parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
    parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
    parser.add_argument('-V', '--volume', type=int, default=config_values['volume'], help='Volume level (0-100)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbose mode (can be used multiple times)')
    parser.add_argument('-l', '--singleloop', action='store_true', help='Single loop mode (partially implemented)')
    parser.add_argument('-m', '--max', type=int, help='Maximum number of videos in single-loop mode (partially implemented)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (suppresses all log outputs except CRITICAL)')
    parser.add_argument('directories', nargs='*', help='Directories to search for videos')
    args = parser.parse_args()

    for key, value in vars(args).items():
        if value is not None:
            config_values[key] = value

    if os.getenv('DEBUG') == 'true':
        config_values['verbose'] = True
        config_values['quiet'] = False  # Désactiver le mode silencieux en cas de DEBUG

    # Étape 5 : Rendre les variables accessibles au niveau du module
    for key, value in config_values.items():
        globals()[key] = value

    globals()['directories'] = config_values['directories']
    _config_initialized = True  # Marquer comme initialisé
