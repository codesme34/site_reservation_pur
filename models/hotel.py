"""Modele de l'hotel (catalogue public)."""
from Database.db import get_connection
from models.base import ModeleBase


class Hotel(ModeleBase):
    table = "hotels"

    def __init__(self, id, nom, ville, tarifs, slug):
        self.id = id
        self.nom = nom
        self.ville = ville
        self.tarifs = tarifs
        self.slug = slug

    @classmethod
    def lister_tous(cls):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, ville, tarifs, slug FROM hotels ORDER BY nom")
        lignes = cursor.fetchall()
        cursor.close()
        conn.close()
        return [cls(*ligne) for ligne in lignes]
