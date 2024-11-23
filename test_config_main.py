# test_config_main.py

import modules.config as config
from modules.test_module import MyClass
def main():
    # Appeler setup_config() pour initialiser la configuration
    config.setup_config()

    # Afficher toutes les variables de configuration
    print("Contenu de config après setup_config() :")
    for attr in dir(config):
        # Ignorer les attributs spéciaux et les méthodes
        if not attr.startswith("__") and not callable(getattr(config, attr)):
            value = getattr(config, attr)
            print(f"{attr} = {value}")

    mymodule = MyClass()

if __name__ == "__main__":
    main()
