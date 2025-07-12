import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                           QVBoxLayout, QLabel, QWidget, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QScreen

class ScreenshotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Capture d'écran")
        self.setGeometry(100, 100, 800, 600)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Bouton de capture
        self.capture_button = QPushButton("Capturer l'écran")
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.capture_button.clicked.connect(self.take_screenshot)
        layout.addWidget(self.capture_button)
        
        # Zone de prévisualisation
        self.preview_label = QLabel("Prévisualisation de la capture")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)
        
        # Créer le dossier de sauvegarde s'il n'existe pas
        self.screenshots_dir = os.path.join(os.path.expanduser("~"), "Screenshots")
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)

    def take_screenshot(self):
        # Capture de l'écran
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        
        # Sauvegarder la capture
        screenshot.save(filepath)
        
        # Afficher la prévisualisation
        scaled_pixmap = screenshot.scaled(780, 500, Qt.AspectRatioMode.KeepAspectRatio)
        self.preview_label.setPixmap(scaled_pixmap)
        
        # Afficher un message de confirmation dans le titre
        self.setWindowTitle(f"Capture d'écran - Sauvegardée dans {filepath}")

def main():
    app = QApplication(sys.argv)
    
    # Application du style moderne
    app.setStyle("Fusion")
    
    window = ScreenshotApp()
    window.show()
    sys.exit(app.exec()) 