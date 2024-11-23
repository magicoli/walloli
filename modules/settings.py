# modules/settings.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

from PyQt5 import QtWidgets, QtCore, QtGui
import os
import argparse

import modules.config as config
import modules.utils as utils   # all functions accessible with utils.function()
from modules.utils import *     # main functions accessible as function() for ease of use, e.g. log(), error(), exit_with_error()

class SettingsDialog(QtWidgets.QDialog):
    """
    Application settings dialog box for the application.
    """

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setModal(True)
        self.resize(400, 300)
        self.settings = QtCore.QSettings('Magiiic', 'WallOli')

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Sélection des répertoires
        dir_layout = QtWidgets.QHBoxLayout()
        self.dir_line_edit = QtWidgets.QLineEdit()
        self.dir_browse_button = QtWidgets.QPushButton("Parcourir")
        self.dir_browse_button.clicked.connect(self.browse_directories)
        dir_layout.addWidget(QtWidgets.QLabel("Répertoires de vidéos :"))
        dir_layout.addWidget(self.dir_line_edit)
        dir_layout.addWidget(self.dir_browse_button)
        layout.addLayout(dir_layout)

        # Nombre de vidéos par écran ou au total
        videos_layout = QtWidgets.QFormLayout()
        self.videos_per_screen_spin = QtWidgets.QSpinBox()
        self.videos_per_screen_spin.setRange(1, 100)
        self.videos_total_spin = QtWidgets.QSpinBox()
        self.videos_total_spin.setRange(1, 1000)
        videos_layout.addRow("Vidéos par écran :", self.videos_per_screen_spin)
        videos_layout.addRow("Vidéos totales :", self.videos_total_spin)
        layout.addLayout(videos_layout)

        # Sélection de l'écran
        self.screen_combo = QtWidgets.QComboBox()
        layout.addWidget(QtWidgets.QLabel("Écran à utiliser :"))
        layout.addWidget(self.screen_combo)

        # Option Panscan
        self.panscan_checkbox = QtWidgets.QCheckBox("Activer l'option Panscan")
        layout.addWidget(self.panscan_checkbox)

        # Contrôle du volume
        volume_layout = QtWidgets.QHBoxLayout()
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_label = QtWidgets.QLabel("Volume : 40")
        self.volume_slider.setValue(40)
        self.volume_slider.valueChanged.connect(lambda val: self.volume_label.setText(f"Volume : {val}"))
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)

        # Boutons OK et Annuler
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def browse_directories(self):
        directories = QtWidgets.QFileDialog.getExistingDirectory(self, "Sélectionner les répertoires de vidéos", os.path.expanduser("~"), QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if directories:
            self.dir_line_edit.setText(directories)

    def load_settings(self):
        """
        Charger les paramètres enregistrés précédemment.
        """
        directories = self.settings.value('directories', '')
        self.dir_line_edit.setText(directories)

        videos_per_screen = int(self.settings.value('videos_per_screen', 1))
        self.videos_per_screen_spin.setValue(videos_per_screen)

        videos_total = int(self.settings.value('videos_total', 1))
        self.videos_total_spin.setValue(videos_total)

        current_screen = self.settings.value('selected_screen', 'Écran 1')
        self.screen_combo.addItems(self.get_available_screens())
        index = self.screen_combo.findText(current_screen)
        if index != -1:
            self.screen_combo.setCurrentIndex(index)

        panscan = self.settings.value('panscan', False, type=bool)
        self.panscan_checkbox.setChecked(panscan)

        volume = int(self.settings.value('volume', 40))
        self.volume_slider.setValue(volume)

    def get_available_screens(self):
        """
        Récupérer la liste des écrans disponibles.
        """
        available_screens = []
        desktop = QtWidgets.QApplication.desktop()
        for i in range(desktop.screenCount()):
            screen_geometry = desktop.screenGeometry(i)
            available_screens.append(f"Écran {i + 1} ({screen_geometry.width()}x{screen_geometry.height()})")
        return available_screens

    def accept(self):
        """
        Enregistrer les paramètres lorsque l'utilisateur clique sur OK.
        """
        directories = self.dir_line_edit.text()
        self.settings.setValue('directories', directories)

        videos_per_screen = self.videos_per_screen_spin.value()
        self.settings.setValue('videos_per_screen', videos_per_screen)

        videos_total = self.videos_total_spin.value()
        self.settings.setValue('videos_total', videos_total)

        selected_screen = self.screen_combo.currentText()
        self.settings.setValue('selected_screen', selected_screen)

        panscan = self.panscan_checkbox.isChecked()
        self.settings.setValue('panscan', panscan)

        volume = self.volume_slider.value()
        self.settings.setValue('volume', volume)

        log("Paramètres enregistrés.")
        super(SettingsDialog, self).accept()

class Settings:
    required_fields = ['directories', 'videos_per_screen', 'videos_total', 'selected_screen', 'panscan', 'volume', 'verbose', 'quiet', 'singleloop', 'max', 'days']

    def __init__(self):
        self.settings = QtCore.QSettings('Magiiic', 'WallOli')
        self.define_arguments()
        self.ensure_config_fields()
        self.map_arguments_to_config()
        # self.read_settings()

    def define_arguments(self):
        self.parser = argparse.ArgumentParser(description="Video Wall")
        self.parser.add_argument('-s', '--screen', type=int, help='Screen number')
        self.parser.add_argument('-n', '--number', type=int, default=1, help='Number of players per screen')
        self.parser.add_argument('-N', '--total-number', type=int, default=None, help='Total number of players, overrides -n')
        self.parser.add_argument('-b', '--bestfit', action='store_true', help='Try to fit the best number of players on the screens')
        self.parser.add_argument('-d', '--days', type=int, help='Number of days to look back for videos')
        self.parser.add_argument('-p', '--panscan', type=float, default=0, help='Panscan value')
        self.parser.add_argument('-V', '--volume', type=utils.valid_volume, default=config.volume, help='Volume level (0-100)')
        self.parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbose mode (can be used multiple times)')
        self.parser.add_argument('-l', '--singleloop', action='store_true', help='Single loop mode (partially implemented)')
        self.parser.add_argument('-m', '--max', type=int, help='Maximum number of videos in single-loop mode (partially implemented)')
        self.parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (suppresses all log outputs except CRITICAL)')
        self.parser.add_argument('directories', nargs='*', help='Directories to search for videos')
        self.args = self.parser.parse_args()

    def ensure_config_fields(self):
        """
        Assure que toutes les configurations requises existent dans config.
        """
        for field in self.required_fields:
            if not hasattr(config, field):
                setattr(config, field, None)

    def map_arguments_to_config(self):
        """
        Transférer les arguments de la ligne de commande dans config.
        """
        for arg_key, arg_value in vars(self.args).items():
            if arg_value is not None:
                setattr(config, arg_key, arg_value)

        # Vérifier la variable d'environnement DEBUG
        if os.getenv('DEBUG') == 'true':
            config.verbose = 2
            config.quiet = False  # Override quiet mode
