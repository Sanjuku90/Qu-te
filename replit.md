# QuestMoney

## Overview
Application web de quêtes permettant aux utilisateurs de gagner de l'argent en complétant des quêtes quotidiennes. Les utilisateurs déposent de l'argent et gagnent 50% de leur dépôt à chaque quête complétée (max 4 quêtes par jour).

## Architecture
- **Backend**: Flask avec Flask-Login pour l'authentification
- **Base de données**: PostgreSQL avec Flask-SQLAlchemy
- **Frontend**: Templates Jinja2 avec CSS/JS vanilla

## Structure du projet
```
├── app.py              # Application Flask principale
├── models.py           # Modèles SQLAlchemy (User, Quest, QuestCompletion)
├── templates/          # Templates HTML
│   ├── base.html       # Template de base
│   ├── index.html      # Page d'accueil
│   ├── login.html      # Connexion
│   ├── register.html   # Inscription
│   ├── dashboard.html  # Tableau de bord avec quêtes
│   ├── deposit.html    # Page de dépôt
│   └── history.html    # Historique des quêtes
├── static/
│   ├── style.css       # Styles CSS
│   └── script.js       # JavaScript frontend
```

## Fonctionnalités
- Inscription/Connexion utilisateur
- Ajout d'argent au solde
- Dépôt pour débloquer les quêtes
- 4 quêtes disponibles par jour
- Gain de 50% du dépôt par quête complétée
- Retrait des gains
- Historique des quêtes complétées

## Lancement
```bash
python app.py
```
Le serveur démarre sur le port 5000.
