-- ============================================================
-- C3.c : Requetes SQL demontrant le CRUD complet, le tri/filtre,
-- et les jointures via les cles etrangeres.
-- ============================================================


-- 1. LISTER (SELECT) avec JOINTURE + FILTRE + TRI
-- Liste les reservations d'hotel payees d'un client, avec le nom
-- de l'hotel recupere via la jointure sur hotel_id (cle etrangere),
-- triees des plus recentes aux plus anciennes.
SELECT
    reservations_hotel.id,
    hotels.nom AS hotel_nom,
    reservations_hotel.date_arrivee,
    reservations_hotel.date_depart,
    reservations_hotel.tarif_total
FROM reservations_hotel
JOIN hotels ON reservations_hotel.hotel_id = hotels.id
WHERE reservations_hotel.client_id = 2
  AND reservations_hotel.statut = 'Payé'
ORDER BY reservations_hotel.date_arrivee DESC;


-- 2. LISTER avec FILTRE sur une plage de prix + TRI croissant
-- Exemple : un visiteur cherche un hotel a moins de 300E/nuit
SELECT nom, ville, tarifs
FROM hotels
WHERE tarifs <= 300
ORDER BY tarifs ASC;


-- 3. AJOUTER (INSERT)
-- Creation d'un nouveau compte client (mdp deja hache cote Python
-- avec bcrypt avant d'arriver ici - jamais de mot de passe en clair)
INSERT INTO compte_client (nom, prenom, email, mdp)
VALUES ('Durand', 'Marie', 'marie.durand@example.com', '$2b$12$exemple_de_hash_bcrypt')
RETURNING id;


-- 4. MODIFIER (UPDATE)
-- Un administrateur change le role d'un compte client en admin
UPDATE compte_client
SET is_admin = TRUE
WHERE id = 4;

-- Modifier plusieurs champs a la fois : le prix d'un hotel change
UPDATE hotels
SET tarifs = 165.00
WHERE slug = 'radisson-blu-hotel-nantes';


-- 5. SUPPRIMER (DELETE)
-- Supprimer un compte client. On supprime d'abord ses reservations
-- (pas de ON DELETE CASCADE dans notre schema, donc l'ordre compte :
-- sinon la contrainte de cle etrangere refuse la suppression).
DELETE FROM reservations_hotel WHERE client_id = 6;
DELETE FROM reservations_vol WHERE client_id = 6;
DELETE FROM compte_client WHERE id = 6;


-- 6. JOINTURE SUR 3 TABLES
-- Le cas le plus complexe du site : afficher un vol avec les infos
-- de sa destination (jointure 1) et sa reservation si elle existe (jointure 2)
SELECT
    vols.id,
    destinations.ville,
    destinations.pays,
    vols.date,
    vols.prix,
    reservations_vol.statut
FROM vols
JOIN destinations ON vols.destination_id = destinations.id
LEFT JOIN reservations_vol ON reservations_vol.vol_id = vols.id
ORDER BY vols.date ASC;


-- 7. FILTRE + GROUP BY (agregation)
-- Combien de reservations payees par hotel (utile pour un futur
-- tableau de bord admin)
SELECT
    hotels.nom,
    COUNT(reservations_hotel.id) AS nombre_reservations
FROM hotels
LEFT JOIN reservations_hotel
    ON reservations_hotel.hotel_id = hotels.id
    AND reservations_hotel.statut = 'Payé'
GROUP BY hotels.nom
ORDER BY nombre_reservations DESC;
