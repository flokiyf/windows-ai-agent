import sys
import os
import base64
import threading
import json
import io
import random
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                           QVBoxLayout, QLabel, QWidget, QFileDialog, QTextEdit, QHBoxLayout,
                           QLineEdit, QComboBox, QGroupBox, QSlider, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QRect, QTimer
from PyQt6.QtGui import QPixmap, QScreen, QPainter, QPen, QColor, QImage, QFont
from openai import OpenAI
from PIL import Image, ImageDraw, ImageGrab

# Configuration de l'API OpenAI
# Utilisez une variable d'environnement pour la clé API
# Exportez votre clé avec: export OPENAI_API_KEY="votre_clé_api"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Liste de couleurs distinctes pour les rectangles
DISTINCT_COLORS = [
    QColor(255, 0, 0),      # Rouge
    QColor(0, 255, 0),      # Vert
    QColor(0, 0, 255),      # Bleu
    QColor(255, 255, 0),    # Jaune
    QColor(255, 0, 255),    # Magenta
    QColor(0, 255, 255),    # Cyan
    QColor(255, 128, 0),    # Orange
    QColor(128, 0, 255),    # Violet
    QColor(0, 128, 255),    # Bleu ciel
    QColor(255, 0, 128),    # Rose
    QColor(0, 255, 128),    # Vert menthe
    QColor(128, 255, 0),    # Vert lime
    QColor(128, 128, 255),  # Lavande
    QColor(255, 128, 128),  # Rose pâle
    QColor(128, 255, 128),  # Vert pâle
]

# Dictionnaire des noms de couleurs
COLOR_NAMES = {
    (255, 0, 0): "Rouge",
    (0, 255, 0): "Vert",
    (0, 0, 255): "Bleu",
    (255, 255, 0): "Jaune",
    (255, 0, 255): "Magenta",
    (0, 255, 255): "Cyan",
    (255, 128, 0): "Orange",
    (128, 0, 255): "Violet",
    (0, 128, 255): "Bleu ciel",
    (255, 0, 128): "Rose",
    (0, 255, 128): "Vert menthe",
    (128, 255, 0): "Vert lime",
    (128, 128, 255): "Lavande",
    (255, 128, 128): "Rose pâle",
    (128, 255, 128): "Vert pâle",
}

class SignalEmitter(QObject):
    description_ready = pyqtSignal(str)
    detection_ready = pyqtSignal(str, object)  # Signal pour la détection d'objets
    frame_ready = pyqtSignal(QPixmap)  # Signal pour les nouvelles frames

class ScreenCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analyse vidéo en temps réel avec AI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Émetteur de signal pour la communication entre threads
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.description_ready.connect(self.update_description)
        self.signal_emitter.detection_ready.connect(self.update_detection)
        self.signal_emitter.frame_ready.connect(self.update_frame)
        
        # Client OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Boutons en haut
        top_buttons_layout = QHBoxLayout()
        main_layout.addLayout(top_buttons_layout)
        
        # Bouton de démarrage/arrêt du streaming
        self.stream_button = QPushButton("Démarrer le streaming")
        self.stream_button.setStyleSheet("""
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
        self.stream_button.clicked.connect(self.toggle_streaming)
        top_buttons_layout.addWidget(self.stream_button)
        
        # Zone de contrôle du streaming
        stream_control_group = QGroupBox("Contrôle du streaming")
        stream_control_layout = QHBoxLayout(stream_control_group)
        
        # Intervalle de capture
        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setMinimum(1)
        self.interval_slider.setMaximum(10)
        self.interval_slider.setValue(3)
        self.interval_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.interval_slider.setTickInterval(1)
        
        self.interval_label = QLabel("Intervalle: 3s")
        self.interval_slider.valueChanged.connect(self.update_interval_label)
        
        stream_control_layout.addWidget(QLabel("Vitesse:"))
        stream_control_layout.addWidget(self.interval_slider)
        stream_control_layout.addWidget(self.interval_label)
        
        # Option d'analyse automatique
        self.auto_analyze = QCheckBox("Analyse automatique")
        self.auto_analyze.setChecked(False)
        stream_control_layout.addWidget(self.auto_analyze)
        
        top_buttons_layout.addWidget(stream_control_group)
        
        # Zone de recherche d'éléments
        search_group = QGroupBox("Détection d'éléments")
        search_layout = QHBoxLayout(search_group)
        
        # Champ de saisie libre pour la détection
        self.element_input = QLineEdit()
        self.element_input.setPlaceholderText("Entrez ce que vous souhaitez détecter (ex: boutons, liens, logo, texte spécifique...)")
        self.element_input.setMinimumWidth(400)
        search_layout.addWidget(self.element_input, 3)
        
        self.detect_button = QPushButton("Détecter")
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.detect_button.clicked.connect(self.detect_elements)
        search_layout.addWidget(self.detect_button, 1)
        
        top_buttons_layout.addWidget(search_group)
        
        # Layout horizontal pour l'image et la description
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # Zone de prévisualisation
        self.preview_label = QLabel("Prévisualisation du stream")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(700, 500)
        content_layout.addWidget(self.preview_label, 2)
        
        # Zone de description
        description_layout = QVBoxLayout()
        content_layout.addLayout(description_layout, 1)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setPlaceholderText("La description de l'image apparaîtra ici...")
        self.description_text.setMinimumSize(300, 400)
        description_layout.addWidget(self.description_text)
        
        # Zone de détection
        self.detection_text = QTextEdit()
        self.detection_text.setReadOnly(True)
        self.detection_text.setPlaceholderText("Les éléments détectés apparaîtront ici...")
        self.detection_text.setMinimumHeight(100)
        description_layout.addWidget(self.detection_text)
        
        # Créer le dossier de sauvegarde s'il n'existe pas
        self.screenshots_dir = os.path.join(os.path.expanduser("~"), "Screenshots")
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        
        # Variables pour stocker les données
        self.last_screenshot_path = None
        self.current_pixmap = None
        self.original_pixmap = None
        self.detected_elements = []
        self.element_colors = {}  # Pour stocker les couleurs associées à chaque élément
        
        # Variables pour le streaming
        self.streaming = False
        self.stream_thread = None
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self.capture_frame)
        self.last_analysis_time = 0
        self.analysis_interval = 15  # Secondes entre chaque analyse automatique
        
        # Vérification de la clé API
        if not OPENAI_API_KEY:
            self.description_text.setText("⚠️ ATTENTION: Clé API OpenAI non configurée!\n\n"
                                        "Veuillez définir la variable d'environnement OPENAI_API_KEY.\n\n"
                                        "Sous Windows: set OPENAI_API_KEY=votre_clé_api\n"
                                        "Sous Linux/Mac: export OPENAI_API_KEY=votre_clé_api")

    def update_interval_label(self, value):
        self.interval_label.setText(f"Intervalle: {value}s")
    
    def toggle_streaming(self):
        if self.streaming:
            self.stop_streaming()
        else:
            self.start_streaming()
    
    def start_streaming(self):
        # Vérifier si la clé API est configurée
        if not OPENAI_API_KEY:
            self.description_text.setText("⚠️ ERREUR: Clé API OpenAI non configurée!\n\n"
                                        "Veuillez définir la variable d'environnement OPENAI_API_KEY.\n\n"
                                        "Sous Windows: set OPENAI_API_KEY=votre_clé_api\n"
                                        "Sous Linux/Mac: export OPENAI_API_KEY=votre_clé_api")
            return
            
        self.streaming = True
        self.stream_button.setText("Arrêter le streaming")
        self.stream_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        # Démarrer le timer pour capturer des frames
        interval_ms = self.interval_slider.value() * 1000
        self.stream_timer.start(interval_ms)
    
    def stop_streaming(self):
        self.streaming = False
        self.stream_button.setText("Démarrer le streaming")
        self.stream_button.setStyleSheet("""
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
        
        # Arrêter le timer
        self.stream_timer.stop()
    
    def capture_frame(self):
        if not self.streaming:
            return
        
        # Capturer l'écran
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        self.original_pixmap = screenshot
        
        # Générer un nom de fichier unique pour cette frame
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        
        # Sauvegarder la capture
        screenshot.save(filepath)
        self.last_screenshot_path = filepath
        
        # Redimensionner pour l'affichage
        scaled_pixmap = screenshot.scaled(700, 500, Qt.AspectRatioMode.KeepAspectRatio)
        self.current_pixmap = scaled_pixmap
        
        # Émettre le signal avec la nouvelle frame
        self.signal_emitter.frame_ready.emit(scaled_pixmap)
        
        # Si l'analyse automatique est activée et que l'intervalle est écoulé
        current_time = time.time()
        if self.auto_analyze.isChecked() and (current_time - self.last_analysis_time) >= self.analysis_interval:
            self.last_analysis_time = current_time
            threading.Thread(target=self.analyze_image, args=(filepath,)).start()
            
            # Si un élément à détecter est spécifié, lancer la détection
            element_query = self.element_input.text().strip()
            if element_query:
                threading.Thread(target=self.analyze_elements, args=(filepath, element_query)).start()
    
    def update_frame(self, pixmap):
        # Mettre à jour l'affichage avec la nouvelle frame
        self.preview_label.setPixmap(pixmap)
        
        # Si des éléments ont été détectés, les dessiner sur la frame
        if self.detected_elements:
            self.draw_bounding_boxes()
    
    def detect_elements(self):
        if not self.last_screenshot_path:
            self.detection_text.setText("Veuillez d'abord démarrer le streaming.")
            return
        
        # Récupérer le texte saisi par l'utilisateur
        element_query = self.element_input.text().strip()
        
        if not element_query:
            self.detection_text.setText("Veuillez spécifier ce que vous souhaitez détecter.")
            return
            
        self.detection_text.setText(f"Détection de '{element_query}' en cours...")
        self.detect_button.setEnabled(False)
        
        # Lancer la détection dans un thread séparé
        threading.Thread(target=self.analyze_elements, args=(self.last_screenshot_path, element_query)).start()
    
    def analyze_elements(self, image_path, element_query):
        try:
            # Encoder l'image en base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Appeler l'API OpenAI Vision pour la détection d'objets
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"""Identifie et localise précisément tous les éléments correspondant à "{element_query}" dans cette image. 
                            Pour chaque élément détecté, donne-moi:
                            1. Une description courte
                            2. Les coordonnées précises sous forme de rectangle [x, y, largeur, hauteur] où x,y est le coin supérieur gauche
                            
                            Réponds UNIQUEMENT avec un objet JSON valide de cette forme:
                            {{
                                "elements": [
                                    {{
                                        "description": "Description de l'élément",
                                        "coordinates": [x, y, largeur, hauteur]
                                    }},
                                    ...
                                ]
                            }}
                            
                            Ne mets aucun texte avant ou après le JSON. Assure-toi que les coordonnées sont précises et correspondent bien aux éléments visibles."""},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            # Récupérer la réponse JSON
            json_response = response.choices[0].message.content
            detection_data = json.loads(json_response)
            
            # Émettre le signal avec les données de détection
            self.signal_emitter.detection_ready.emit(json_response, detection_data)
            
        except Exception as e:
            # En cas d'erreur, émettre un message d'erreur
            error_message = f"Erreur lors de la détection: {str(e)}"
            self.signal_emitter.detection_ready.emit(error_message, None)
    
    def analyze_image(self, image_path):
        try:
            # Encoder l'image en base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Appeler l'API OpenAI Vision avec le modèle gpt-4-turbo qui supporte la vision
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Décris brièvement ce qui est visible à l'écran."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            
            # Récupérer la description
            description = response.choices[0].message.content
            
            # Émettre le signal avec la description
            self.signal_emitter.description_ready.emit(description)
            
        except Exception as e:
            # En cas d'erreur, émettre un message d'erreur
            error_message = f"Erreur lors de l'analyse de l'image: {str(e)}"
            self.signal_emitter.description_ready.emit(error_message)
    
    def update_description(self, description):
        # Mettre à jour l'interface avec la description
        current_time = datetime.now().strftime("%H:%M:%S")
        self.description_text.append(f"[{current_time}] {description}\n")
        self.description_text.ensureCursorVisible()
    
    def update_detection(self, json_text, detection_data):
        # Réactiver le bouton de détection
        self.detect_button.setEnabled(True)
        
        if detection_data is None:
            self.detection_text.setText(json_text)  # Afficher l'erreur
            return
        
        # Stocker les éléments détectés
        self.detected_elements = detection_data.get('elements', [])
        
        # Assigner une couleur à chaque élément détecté
        self.element_colors = {}
        for i, element in enumerate(self.detected_elements):
            color_index = i % len(DISTINCT_COLORS)
            self.element_colors[i] = DISTINCT_COLORS[color_index]
        
        # Afficher le résumé des éléments détectés avec leurs couleurs
        elements_count = len(self.detected_elements)
        element_query = self.element_input.text().strip()
        summary = f"{elements_count} élément(s) '{element_query}' détecté(s):\n\n"
        
        for i, element in enumerate(self.detected_elements):
            color = self.element_colors[i]
            color_name = self.get_color_name(color)
            summary += f"{i+1}. <span style='color:{color.name()};'>■</span> {element['description']} ({color_name})\n"
        
        self.detection_text.setHtml(summary)
        
        # Dessiner les rectangles sur l'image actuelle
        self.draw_bounding_boxes()
    
    def get_color_name(self, color):
        """Retourne le nom de la couleur en français"""
        rgb = (color.red(), color.green(), color.blue())
        return COLOR_NAMES.get(rgb, "Couleur personnalisée")
    
    def draw_bounding_boxes(self):
        if not self.current_pixmap or not self.detected_elements:
            return
        
        # Créer une copie de l'image originale
        pixmap = self.current_pixmap.copy()
        
        # Obtenir les dimensions de l'image affichée
        display_width = pixmap.width()
        display_height = pixmap.height()
        
        # Obtenir les dimensions de l'image originale
        original_width = self.original_pixmap.width()
        original_height = self.original_pixmap.height()
        
        # Calculer les facteurs d'échelle
        scale_x = display_width / original_width
        scale_y = display_height / original_height
        
        # Créer un peintre pour dessiner sur l'image
        painter = QPainter(pixmap)
        
        # Dessiner un rectangle pour chaque élément détecté avec une couleur unique
        for i, element in enumerate(self.detected_elements):
            coords = element.get('coordinates', [0, 0, 0, 0])
            if len(coords) == 4:
                x, y, width, height = coords
                
                # Ajuster les coordonnées à l'échelle de l'image affichée
                scaled_x = int(x * scale_x)
                scaled_y = int(y * scale_y)
                scaled_width = int(width * scale_x)
                scaled_height = int(height * scale_y)
                
                # Définir le style du pinceau avec la couleur associée à cet élément
                color = self.element_colors[i]
                pen = QPen(color)
                pen.setWidth(3)
                painter.setPen(pen)
                
                # Dessiner le rectangle
                painter.drawRect(scaled_x, scaled_y, scaled_width, scaled_height)
                
                # Ajouter un numéro à côté du rectangle pour l'identifier
                font = QFont()
                font.setBold(True)
                font.setPointSize(12)
                painter.setFont(font)
                painter.drawText(scaled_x, scaled_y - 5, f"{i+1}")
        
        painter.end()
        
        # Mettre à jour l'affichage
        self.preview_label.setPixmap(pixmap)

def main():
    app = QApplication(sys.argv)
    
    # Application du style moderne
    app.setStyle("Fusion")
    
    window = ScreenCaptureApp()
    window.show()
    sys.exit(app.exec()) 