# Messagerie Instantanée
# Plateforme de Gestion d'Amis, Conversations et Groupes

Ce projet est une application web en Python utilisant Flask pour la gestion d'amis, la messagerie (en temps réel et asynchrone), et les appels vocaux/vidéo en groupe ou en tête-à-tête. Elle intègre également des fonctionnalités avancées comme les groupes, les conversations en temps réel avec WebSockets (via Socket.IO) et un serveur UDP pour la gestion réseau.

---

## Fonctionnalités

### Gestion des utilisateurs
- **Inscription et connexion sécurisée** avec Flask-Login.
- **Photo de profil personnalisée** :
  - Téléchargement et mise à jour des photos de profil.
  - Affichage d'une image par défaut si aucune photo n'est définie.

### Gestion des amis
- Ajouter ou supprimer des amis.
- Envoyer, accepter ou rejeter des demandes d'amis.
- Afficher la liste d'amis connectés.

### Messagerie privée
- Débuter des conversations individuelles.
- Envoyer et recevoir des messages dans des conversations privées.
- Afficher les messages classés par date.
- Suivi des messages non lus et marquage automatique comme "lus".

### Groupes
- Créer, éditer ou supprimer des groupes.
- Ajouter des amis à un groupe.
- Gérer les messages dans un chat de groupe.
- Quitter ou supprimer un groupe en fonction des permissions (admin ou membre).

### Appels vocaux et vidéo
- Appels directs entre amis.
- Appels de groupe.
- Intégration avec WebRTC pour la gestion des connexions pair-à-pair.

### Recherche et découverte
- Rechercher d'autres utilisateurs par leur nom d'utilisateur.
- Voir les profils des utilisateurs.

### Temps réel
- Intégration de WebSockets (via Flask-SocketIO) pour des mises à jour en temps réel dans les conversations et appels.

### Serveur UDP
- Serveur UDP intégré pour la gestion des communications spécifiques (port 12346).

---

## Installation

### Prérequis
1. Python 3.9 ou supérieur.
2. Virtualenv ou un autre outil de gestion d'environnements virtuels.
3. Flask et les bibliothèques associées :
   - Flask-SocketIO
   - Flask-Login
   - SQLAlchemy
   - Werkzeug

### Étapes

1. Clonez ce dépôt sur votre machine locale :
   ```bash
   git clone https://github.com/votre-utilisateur/votre-repo.git
   cd votre-repertoire
   ```

2. Lancez directement l'application :
   ```bash
   python app.py
   ```

3. Accédez à l'application via votre navigateur en entrant l'URL suivante :
   
   [http://localhost:5000] 

4. Si l'application ne fonctionne pas correctement, assurez-vous d'avoir les extensions nécessaires installées. Si le problème persiste, appuyez sur `Ctrl + Shift + P` dans votre éditeur de code, recherchez "Python: Select Interpreter", et sélectionnez la version globale de Python. Cela devrait résoudre le problème.

---

## Utilisation

### Gestion des utilisateurs
- Inscrivez-vous pour créer un compte.
- Connectez-vous pour accéder à vos fonctionnalités personnalisées.
- Téléchargez une photo de profil depuis votre tableau de bord.

### Messagerie
- Commencez une conversation avec un ami en cliquant sur son profil.
- Envoyez et recevez des messages en temps réel grâce à Socket.IO.

### Groupes
- Créez un groupe en donnant un nom et en sélectionnant des participants.
- Chattez dans des groupes pour des discussions collaboratives.
- Gérez les permissions du groupe si vous êtes l'administrateur.

### Appels vocaux/vidéo
- Cliquez sur le bouton d'appel dans une conversation ou un groupe.
- Utilisez la fonctionnalité WebRTC pour des appels sécurisés et rapides.

---

## Licence

Ce projet est sous licence MIT. Consultez le fichier LICENSE pour plus d'informations.

---

## Auteur

- **ABDOUN Wasim** 
- GitHub : (https://github.com/Wasim9319) 
- Contact : wasim.abd@outlook.fr 
- **CELIK Serkan** 
- GitHub : https://github.com/serkan932) 
- Contact : serkanclk2021@gmail.com 
- **BENMOUALLI Ayoub** 
- GitHub : (https://github.com/ayoub-1978) 
- Contact : ayoub.benmoualli19@gmail.com 
- **AMARATUNGA Shanaka** 
- GitHub : (https://github.com/Shan93-3) 
- Contact : amaratunga.shanaka@gmail.com 
