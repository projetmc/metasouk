Metasouk est une application de e-commerce innovante dédiée à l’achat et la vente de NFTs. 
Elle propose un écosystème complet avec gestion des utilisateurs (visiteur, client, vendeur, administrateur), panier d'achat, évaluations et signalements de produits, ainsi qu’une interface d’administration performante.

Fonctionnement Général
1.Visiteur
-Le visiteur accède au site Metasouk sans authentification.
-Il peut parcourir la liste des NFTs disponibles.
-Il peut ajouter des produits à son panier temporaire.
-Lorsqu’il souhaite passer au paiement, il est redirigé vers la page d’inscription.

2.Client(après inscription)
-L'utilisateur s’inscrit pour devenir client.
Il peut désormais :
-Gérer son panier (ajout/retrait de NFTs).
-Passer une commande et suivre son historique.
-Commenter, évaluer et signaler des produits.
-Modifier ses informations personnelles (nom, email, age, etc.).
-Supprimer son compte définitivement : Un email de confirmation de suppression est automatiquement envoyé.
-Il peut cliquer sur le bouton "Became seller" : Une demande est envoyée à l’administrateur pour validation.

3.Vendeur(après validation par l'administrateur)
-Si le client est accepté en tant que vendeur :
Un email de confirmation est envoyé et son statut est mis à jour à vendeur.
Le bouton "Devenir vendeur" est remplacé par "Seller's sapce".

-Le vendeur peut :
-Ajouter des produits NFTs à vendre.
-Modifier ou supprimer ses propres produits.
-Accéder à son tableau de bord personnel de ventes.
-Continuer d'utiliser les fonctionnalités client (panier, commentaires, etc.).

4.Administrateur
-L’administrateur se connecte avec :
Username: admin
Mot de passe : admin123

-Il a accès au tableau de bord administratif :
-Visualisation de toutes les commandes effectuées.
-Gestion des comptes utilisateurs (clients et vendeurs).
-Ajout, modification ou suppression de produits NFT sur la plateforme.
-Il traite les demandes de passage en vendeur :
*Si la demande est acceptée :Le statut du client passe à vendeur et un email de confirmation est envoyé.
*Si la demande est refusée : Un email explicatif est envoyé au client.

----Déroulement du projet Django en local (si l’hébergement échoue)---
Si l’hébergement de l’application Metasouk ne fonctionne pas, 
voici les etapes afin de l'executer localement :

1.Prérequis:
Python 3.8
pip
Git
Virtualenv (optionnel mais recommandé)
MySQL (ou le moteur de base de données que vous avez utilisé)

2.Cloner le projet: 
git clone https://github.com/votre-utilisateur/metasouk.git
cd metasouk

3.Créer et activer un environnement virtuel: 
python -m venv env
source env\Scripts\activate

4.Installer les dépendances:
pip install -r requirements.txt

5.Configurer la base de données : charger le script .sql dans la base de données MYSQL 

6.Appliquer les migrations:
python manage.py makemigrations
python manage.py migrate

7.Lancer le serveur de développement : 
python manage.py runserver
