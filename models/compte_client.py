"""Modele du compte utilisateur (client ou administrateur)."""
import bcrypt
from Database.db import get_connection
from models.base import ModeleBase


class CompteClient(ModeleBase):
    table = "compte_client"

    def __init__(self, id, nom, prenom, email, is_admin, mdp_hash=None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.is_admin = is_admin
        self._mdp_hash = mdp_hash

    @classmethod
    def lister_tous(cls):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prenom, email, is_admin FROM compte_client ORDER BY id")
        lignes = cursor.fetchall()
        cursor.close()
        conn.close()
        return [cls(*ligne) for ligne in lignes]

    @classmethod
    def trouver_par_id(cls, compte_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nom, prenom, email, is_admin, mdp FROM compte_client WHERE id = %s",
            (compte_id,)
        )
        ligne = cursor.fetchone()
        cursor.close()
        conn.close()
        return cls(*ligne) if ligne else None

    @classmethod
    def trouver_par_email(cls, email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nom, prenom, email, is_admin, mdp FROM compte_client WHERE email = %s",
            (email,)
        )
        ligne = cursor.fetchone()
        cursor.close()
        conn.close()
        if ligne is None:
            return None
        compte_id, nom, prenom, email, is_admin, mdp_hash = ligne
        return cls(compte_id, nom, prenom, email, is_admin, mdp_hash)

    @classmethod
    def creer(cls, nom, prenom, email, mdp_hash, is_admin):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO compte_client (nom, prenom, email, mdp, is_admin) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (nom, prenom, email, mdp_hash, is_admin)
        )
        nouvel_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return cls(nouvel_id, nom, prenom, email, is_admin)

    def modifier(self, nom, prenom, email, is_admin):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE compte_client SET nom = %s, prenom = %s, email = %s, is_admin = %s WHERE id = %s",
            (nom, prenom, email, is_admin, self.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        self.nom, self.prenom, self.email, self.is_admin = nom, prenom, email, is_admin

    def supprimer(self):
        # pas de ON DELETE CASCADE en base : on supprime d'abord les reservations liees
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reservations_hotel WHERE client_id = %s", (self.id,))
        cursor.execute("DELETE FROM reservations_vol WHERE client_id = %s", (self.id,))
        conn.commit()
        cursor.close()
        conn.close()
        super().supprimer_par_id(self.id)  # reutilise la methode heritee de ModeleBase

    def verifier_mot_de_passe(self, mdp_clair):
        if self._mdp_hash is None:
            return False
        return bcrypt.checkpw(mdp_clair.encode("utf-8"), self._mdp_hash.encode("utf-8"))
