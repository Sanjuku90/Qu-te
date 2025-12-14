# QuestMoney

## Overview
Application web de quêtes permettant aux utilisateurs de gagner de l'argent en complétant des quêtes quotidiennes. Les utilisateurs déposent de l'argent via BNB (BEP20) et gagnent 50% de leur dépôt à chaque quête complétée (max 4 quêtes par jour).

## Architecture
- **Backend**: Flask avec Flask-Login pour l'authentification
- **Base de données**: PostgreSQL avec Flask-SQLAlchemy
- **Frontend**: Templates Jinja2 avec CSS moderne
- **Sécurité**: Protection CSRF sur tous les formulaires

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
│   ├── deposit.html    # Page de dépôt avec adresse BNB
│   └── history.html    # Historique des quêtes
├── static/
│   ├── style.css       # Styles CSS professionnels
│   └── script.js       # JavaScript frontend
```

## Configuration
- **Adresse de dépôt BNB (BEP20)**: 0x4dc2eac23fa51001d5acc94889177ec066cc389c
- **Minimum de dépôt**: 200$
- **Gain par quête**: 50% du dépôt
- **Quêtes par jour**: 4 maximum

## Fonctionnalités
- Inscription/Connexion utilisateur sécurisée
- Dépôt via cryptomonnaie BNB (BEP20)
- 4 quêtes disponibles par jour
- Gain de 50% du dépôt par quête complétée
- Retrait des gains (limite journalière de 150$)
- Historique des quêtes complétées
- Système de parrainage avec bonus de 10$ au premier dépôt du filleul
- Page de profil avec modification du mot de passe et statistiques de parrainage

## Lancement local
```bash
python app.py
```
Le serveur démarre sur le port 5000.

## Déploiement sur Render

Le projet est configuré pour le déploiement sur Render. Fichiers de configuration:
- `Procfile` - Commande de démarrage pour Render
- `render.yaml` - Blueprint Render avec configuration complète
- `runtime.txt` - Version Python spécifiée
- `requirements.txt` - Dépendances Python

### Étapes de déploiement sur Render:
1. Créer un compte sur https://render.com
2. Connecter votre dépôt GitHub
3. Utiliser le fichier `render.yaml` pour créer automatiquement:
   - Une base de données PostgreSQL
   - Un service web Python
4. Variables d'environnement requises:
   - `DATABASE_URL` - Générée automatiquement par Render
   - `SECRET_KEY` - Générée automatiquement par Render
