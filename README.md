# Application de Capture d'Écran et Analyse Vidéo en Temps Réel

Une application pour capturer et analyser votre écran en temps réel avec une interface graphique en PyQt6 et analyse d'image par OpenAI Vision.

## Fonctionnalités

- **Streaming vidéo en temps réel** : Capture continue de l'écran à intervalles configurables
- **Détection d'éléments** : Identifie et encadre des éléments spécifiques sur l'écran avec des couleurs distinctes
- **Analyse automatique** : Option pour analyser automatiquement le contenu de l'écran à intervalles réguliers
- **Interface moderne** : Interface graphique intuitive avec contrôles de streaming et visualisation en direct
- **Stockage organisé** : Sauvegarde des captures dans un dossier dédié avec horodatage

## Installation

1. Assurez-vous d'avoir Python 3.8+ installé
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration de l'API OpenAI

L'application utilise l'API OpenAI pour l'analyse d'images. Vous devez configurer votre clé API avant d'utiliser l'application :

### Sous Windows
```bash
set OPENAI_API_KEY=votre_clé_api
```

### Sous Linux/Mac
```bash
export OPENAI_API_KEY=votre_clé_api
```

## Utilisation

Vous avez deux façons de lancer l'application :

1. Méthode simple (recommandée) :
```bash
python run.py
```

2. Méthode alternative :
```bash
python -m src
```

### Guide d'utilisation

1. **Démarrer le streaming** : Cliquez sur le bouton "Démarrer le streaming" pour commencer la capture en temps réel
2. **Ajuster la vitesse** : Utilisez le slider pour définir l'intervalle entre chaque capture (1-10 secondes)
3. **Analyse automatique** : Cochez cette option pour analyser automatiquement l'écran à intervalles réguliers
4. **Détection d'éléments** : Entrez ce que vous souhaitez détecter (ex: "boutons", "icônes", "menu", etc.) et cliquez sur "Détecter"

Les éléments détectés seront encadrés sur l'image avec des couleurs distinctes et numérotés pour faciliter l'identification.

## Branches

- **main** : Version stable avec capture d'écran statique
- **video-streaming-feature** : Version avec streaming vidéo en temps réel et détection d'éléments améliorée 