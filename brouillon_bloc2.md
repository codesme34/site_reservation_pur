# BLOC 2 - BACK-END
Développement Back-End d'applications web

Ce que le jury attendait sur chaque compétence, et ce que j'ai fait pour y répondre.

*Langage utilisé : Python natif (aucun framework, aucun Flask)*
*Projet Airlines Reservation - Python pur + PostgreSQL*
*Document de préparation orale au jury*

---

## Retour du premier passage

**CE QUI ETAIT ATTENDU**

"Un seul projet est présenté et celui-ci utilise un framework, alors qu'un projet réalisé en code natif/pur était attendu. Aucun rôle utilisateur n'est défini et les fonctionnalités de modification (UPDATE) et de suppression (DELETE) ne sont pas implémentées."

**CE QUE J'AI FAIT**

J'ai réécrit la partie back-end sans aucun framework, avec une base de données existante que j'ai formalisée et enrichie, un système de rôles (client/admin), et un vrai CRUD complet (ajout, modification, suppression).

---

## C3 - Données

### C3.a : Synthétiser les données utiles à l'application en analysant le cahier des charges afin de formaliser le modèle de données

**CE QUI ETAIT ATTENDU**

- Cr 3.a.4 : Les données nécessaires à l'application sont correctement identifiées
- Cr 3.a.2 : Les données sont retranscrites sur un schéma décrivant les différentes tables et les relations entre elles
- Cr 3.a.3 : Le candidat exploite dans son modèle de données des informations externes provenant d'une API

**CE QUE J'AI FAIT**

J'ai identifié 4 grandes familles de données nécessaires au site, réparties sur 8 tables PostgreSQL :

1. **Comptes et rôles** (`compte_client`) : identité du client, mot de passe (jamais stocké en clair, uniquement son empreinte bcrypt), et un champ `is_admin` qui distingue un client d'un administrateur - c'est ce champ qui manquait au premier passage.

2. **Catalogue** (`hotels`, `vols`, `destinations`) : j'ai séparé `vols` et `destinations` en deux tables distinctes plutôt qu'une seule, parce qu'une même destination (ville, pays, aéroport) peut avoir plusieurs vols différents (dates, compagnies). Les regrouper aurait dupliqué la ville/le pays/l'aéroport à chaque ligne de vol pour rien - c'est une règle de base pour éviter les données redondantes.

3. **Réservations** (`reservations_hotel`, `reservations_vol`) : chaque réservation est reliée à un client et à un hôtel (ou un vol) par une clé étrangère (`client_id`, `hotel_id`/`vol_id`). Cette contrainte empêche techniquement de créer une réservation pour un client ou un hôtel qui n'existe pas en base. En revanche, j'ai volontairement dupliqué les coordonnées de facturation (nom, adresse, téléphone, email) directement dans la réservation au moment du paiement, plutôt que d'aller les chercher dans le profil du client à chaque fois : si le client modifie son profil après coup, la facture déjà émise ne doit pas changer rétroactivement.

4. **Support** (`formulaire_contact`, `paiements`) : données annexes, sans lien direct avec les autres tables.

Le schéma complet (tables + relations) est documenté dans `Database/schema_rapide.pdf`.

**Donnée externe (Cr 3.a.3)** : la ville de l'hôtel (`hotels.ville`) sert de clé vers l'API publique gratuite **Open-Meteo** (geocoding + prévisions météo). La météo actuelle de la destination est récupérée en direct au moment de l'affichage plutôt que stockée en base - une donnée météo stockée serait obsolète en quelques heures, alors que l'appel API garantit une information toujours à jour. Implémenté en Python natif avec `urllib` (bibliothèque standard, sans librairie tierce comme `requests`), voir `Database/weather_api.py`. En cas d'échec de l'API (service indisponible, ville introuvable), la fonction renvoie `None` proprement plutôt que de faire planter la page.

-> `Database/schema.sql` : définition des 8 tables
-> `Database/schema_rapide.pdf` : schéma relationnel et dictionnaire de données
-> `Database/weather_api.py` : appel à l'API externe Open-Meteo

---

### C3.b : Construire la base de données à l'aide d'un outil d'administration de base de données afin de permettre la bonne circulation des données nécessaires au fonctionnement de l'application

**CE QUI ETAIT ATTENDU**

- Cr 3.b.1 : Le nommage des tables et des champs est cohérent avec la typologie des données
- Cr 3.b.2 : Le type des champs est choisi en adéquation avec la nature des données (varchar, boolean, integer...)
- Cr 3.b.3 : La mise en relation des tables est correctement effectuée

**CE QUE J'AI FAIT**

J'ai construit la base avec **PostgreSQL**, en ligne de commande via `psql` (outil d'administration officiel de PostgreSQL).

**Nommage** : toutes les tables et colonnes sont en français, en minuscules avec underscore (`compte_client`, `date_arrivee`, `nombre_adultes`) - cohérent avec le vocabulaire métier du site (un client, une réservation, un tarif) plutôt que des noms techniques génériques.

**Typage** : chaque colonne a un type choisi selon la nature réelle de la donnée, pas par défaut :
- `SERIAL` pour les identifiants (auto-incrémenté, jamais choisi à la main)
- `VARCHAR(n)` avec une longueur adaptée pour du texte court borné (`email VARCHAR(255)`, `code_iata VARCHAR(10)`), `TEXT` pour du texte long ou de taille imprévisible (`descriptions`, `mdp` qui contient un hash bcrypt de longueur fixe mais je le garde en TEXT par sécurité si l'algorithme de hash change un jour)
- `BOOLEAN` pour `is_admin` (une question oui/non, pas un entier 0/1)
- `NUMERIC(10,2)` pour tout ce qui touche à l'argent (`tarifs`, `tarif_total`, `prix`) - jamais de `FLOAT`, qui peut introduire des erreurs d'arrondi sur des montants
- `DATE` / `TIME` / `TIMESTAMP` selon qu'on a besoin d'une date seule (`date_arrivee`), d'une heure seule (`heure_depart`) ou des deux (`date_inscription`)

**Mise en relation** : les tables sont reliées par des clés étrangères (`REFERENCES`) - par exemple `reservations_hotel.client_id REFERENCES compte_client(id)`. Une contrainte `UNIQUE` protège aussi les champs qui ne doivent jamais être dupliqués (`email`, `slug`).

-> `Database/schema.sql` : on y voit les contraintes `REFERENCES`, `UNIQUE`, `NOT NULL` et les types de chaque colonne

---

### C3.c : Interroger la base de données par l'intermédiaire d'un langage de requêtes (SQL) pour permettre la manipulation et l'exploitation des données par l'application

**CE QUI ETAIT ATTENDU**

- Cr 3.c.1 : Le candidat effectue les principales opérations de manipulation des données (lister, ajouter, modifier, supprimer)
- Cr 3.c.2 : Le candidat affine ses requêtes en utilisant des systèmes de tri et de filtres
- Cr 3.c.3 : Les requêtes sont optimisées par l'utilisation de clés étrangères et de liaisons de tables

**CE QUE J'AI FAIT**

C'est exactement le point reproché au premier passage (pas de UPDATE/DELETE). J'ai écrit et testé en base les 4 opérations de base plus des cas plus avancés :

- **Lister** : `SELECT` avec `JOIN` (ex : réservations d'hôtel avec le nom de l'hôtel récupéré via `hotel_id`), combiné à un `WHERE` (filtre sur le statut, sur une fourchette de prix) et un `ORDER BY` (tri par date ou par prix)
- **Ajouter** : `INSERT INTO ... RETURNING id` pour récupérer l'identifiant généré juste après la création
- **Modifier** : `UPDATE ... WHERE` - par exemple changer le rôle d'un compte (`is_admin`) ou le tarif d'un hôtel
- **Supprimer** : `DELETE FROM ... WHERE`, avec un point d'attention : mes tables n'ont pas de `ON DELETE CASCADE`, donc pour supprimer un client il faut d'abord supprimer ses réservations, sinon la contrainte de clé étrangère bloque la suppression (c'est volontaire : ça m'évite de supprimer des données par erreur en cascade sans m'en rendre compte)
- **Jointures sur plusieurs tables** : un vol affiché avec sa destination (`JOIN`) et sa réservation si elle existe (`LEFT JOIN`, pour ne pas exclure les vols jamais réservés)
- **Agrégation** : `GROUP BY` + `COUNT` pour compter les réservations par hôtel, utile pour un futur tableau de bord

Toutes ces requêtes ont été exécutées directement contre la base (dans une transaction annulée pour ne pas modifier les vraies données pendant le test).

-> `Database/requetes_crud.sql` : les 7 requêtes commentées

---

### C3.d : Respecter le cadre légal en utilisant les normes imposées par le RGPD afin de garantir l'intégrité des utilisateurs et la protection des données

**CE QUI ETAIT ATTENDU**

- Cr 3.d.1 : le candidat a identifié les données sensibles et réglementées qui doivent bénéficier d'un traitement spécifique
- Cr 3.d.2 : L'application informe l'utilisateur du stockage, de l'utilisation et du cadre de partage de ses données personnelles
- Cr 3.d.3 : L'utilisateur dispose d'un droit de consultation, modification et de suppression de ses données personnelles
- Cr 3.d.4 : Les données sensibles sont protégées

**CE QUE J'AI FAIT**

C'était noté 0/3 au premier passage - ce point n'avait pas du tout été traité.

**Données identifiées comme sensibles (Cr 3.d.1)** : le mot de passe (la plus sensible), l'email, le téléphone et l'adresse postale (dans le profil et dans chaque réservation au moment du paiement).

**Information de l'utilisateur (Cr 3.d.2)** : le site a une page "Politique de confidentialité" (`confidentialite.html`) accessible depuis le pied de page de chaque page, qui explique quelles données sont collectées et pourquoi.

**Droit de consultation/modification/suppression (Cr 3.d.3)** : c'est directement ce que couvre l'espace admin qu'on construit pour ce bloc - lister, modifier et supprimer n'importe quel compte client. Dans un cas réel, si un client demande la suppression de ses données (droit RGPD), l'administrateur peut l'exécuter immédiatement via cette interface, sur la même base de données que le reste du site.

**Protection des données sensibles (Cr 3.d.4)** :
- Le mot de passe n'est **jamais stocké en clair** : il est haché avec `bcrypt` avant d'être écrit en base (déjà en place, voir la colonne `mdp` de `compte_client`, qui contient un hash du type `$2b$12$...`, jamais le mot de passe original)
- Toutes les requêtes SQL du code natif utilisent des **requêtes paramétrées** (`%s` avec psycopg2, jamais de f-string ou de concaténation directe dans une requête) - ça empêche l'injection SQL, qui est la faille la plus courante pour voler des données sensibles
- Les sessions de connexion seront gérées par cookie sécurisé (voir C4.e), pas par un identifiant en clair dans l'URL

---

## C4 - Développement Back-End

### C4.a : Conceptualiser l'application, formaliser son schéma fonctionnel, à partir du cahier des charges fourni et des échanges avec le client, afin d'optimiser la charge serveur et les temps de réponse

**CE QUI ETAIT ATTENDU**

- Cr 4.a.1 : Le candidat a posé les bonnes questions au client dans sa démarche de compréhension du fonctionnement de l'application à développer
- Cr 4.a.2 : Le candidat est force de proposition lors de ses échanges
- Cr 4.a.3 : Toutes les fonctionnalités nécessaires au bon fonctionnement de l'application sont correctement listées et détaillées
- Cr 4.a.4 : Le schéma fonctionnel décrit en détail l'enchaînement des vues en fonction des différentes actions et interactions

**CE QUE J'AI FAIT**

**Questions posées (Cr 4.a.1)** : avant de coder, je me suis posé trois questions pour cadrer le périmètre exact de cette version native :
- Faut-il reproduire tout le site (recherche, paiement, emails) en natif ? → Non, le jury évalue la maîtrise du langage natif et du CRUD/rôles, pas la richesse fonctionnelle. Un périmètre réduit mais complet sur ces points précis est plus pertinent qu'une réplique partielle de tout le site.
- Quel est le point précis reproché au premier passage ? → L'usage d'un framework, et l'absence de rôles + de CRUD complet.
- La base de données existante peut-elle être réutilisée ? → Oui, elle est déjà construite (C3.b), le travail restant porte sur la couche applicative.

**Force de proposition (Cr 4.a.2)** : au-delà du strict minimum demandé, j'ai ajouté une protection anti-auto-lockout sur l'espace admin (un administrateur ne peut pas se retirer lui-même ses droits ni supprimer son propre compte), et une intégration d'API externe qui apporte une vraie valeur au site (météo de la destination) plutôt qu'une donnée décorative.

**Fonctionnalités listées (Cr 4.a.3)** :
- Public : connexion, consultation de la liste des hôtels, détail d'un hôtel avec météo en direct, déconnexion
- Admin : redirection automatique vers le tableau de bord après connexion, lister/ajouter/modifier/supprimer un compte client, blocage (403) d'un accès non autorisé

**Schéma fonctionnel (Cr 4.a.4)** : le diagramme montre l'enchaînement complet des vues selon le rôle (client ou admin) déterminé au moment de la connexion.

-> `BLOC_2_Schema_Fonctionnel.pdf`

---

### C4.b : Développer une application en utilisant un langage de programmation adapté afin d'en construire l'architecture et les fonctionnalités côté serveur

**CE QUI ETAIT ATTENDU**

- Cr 4.b.1 : Les fonctions natives du langage sont acquises
- Cr 4.b.2 : Le code est indenté, les commentaires aident à la compréhension du code
- Cr 4.b.3 : Les dossiers et fichiers du projet sont organisés
- Cr 4.b.4 : Les conventions de nommage sont respectées pour l'ensemble du code
- Cr 4.b.5 : Les limites du code sont connues
- Cr 4.b.6 : Les erreurs de codage sont traitées

**CE QUE J'AI FAIT**

Le serveur est écrit en Python pur, avec uniquement des modules de la bibliothèque standard : `http.server` (serveur HTTP), `urllib.parse` (lecture des formulaires et de la query string), `bcrypt` (hash des mots de passe), `secrets` (génération de jetons de session imprévisibles), `html` (échappement anti-XSS), `time` (expiration de session et anti-brute-force). Aucun framework web.

**Fonctions natives maîtrisées (Cr 4.b.1)** : décorateurs (`@route`), fermetures (closures) pour le système de routage, gestionnaire de contexte implicite via `cursor.close()`/`conn.close()`, dictionnaires comme structure de routage.

**Organisation (Cr 4.b.3)** : `app.py` (serveur et routes), `Database/db.py` (connexion), `Database/weather_api.py` (appel API externe), `Database/schema.sql` (structure).

**Limites connues (Cr 4.b.5)** : le rate-limiting est en mémoire (pas partagé entre plusieurs processus serveur, remis à zéro à chaque redémarrage) - suffisant pour une démonstration mais pas pour une vraie mise à l'échelle. Idem pour les sessions.

**Gestion des erreurs (Cr 4.b.6)** : à chaque écriture en base, la connexion est fermée systématiquement (`cursor.close()`, `conn.close()`) ; les identifiants de connexion invalides renvoient une 401 propre plutôt qu'une erreur brute ; le dépassement du rate-limit renvoie un 429 explicite ; une session expirée ou invalide est traitée silencieusement (nettoyée puis traitée comme "non connecté") plutôt que de faire planter la page.

-> `app.py`, `Database/db.py`, `Database/weather_api.py`

---

## À venir dans ce document
- [ ] C4.c : Programmation orientée objet
- [ ] C4.d : Architecture MVC
- [ ] C4.e : Identification utilisateur et rôles
- [ ] C4.f : Travail avec Git
- [ ] C4.g : Livraison et conformité
