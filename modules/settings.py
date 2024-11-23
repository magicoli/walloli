# modules/settings.py

# All code comments, user outputs and debugs must be in English. Do not remove this line.
# Some commands are commented out for further development. Do not remove them.

from PyQt5 import QtWidgets, QtCore, QtGui
from modules.utils import log
import os

class SettingsDialog(QtWidgets.QDialog):
    """
    Application settings dialog box for the application.
    """

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setModal(True)
        self.resize(400, 300)
        self.settings = QtCore.QSettings('VotreEntreprise', 'VideoWallApp')  # Remplacez par votre organisation et nom d'application

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

    def open_settings_dialog(self):
        """
        Open the settings dialog.
        """
        log("Opening settings dialog")
        dialog = SettingsDialog()
        dialog.settings_changed.connect(self.apply_settings)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            log("Settings dialog accepted")
            self.apply_settings()
        else:
            log("Settings dialog cancelled")

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

