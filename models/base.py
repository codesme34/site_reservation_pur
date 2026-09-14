"""Classe mere partagee par tous les modeles."""
from Database.db import get_connection


class ModeleBase:
    """Regroupe le comportement commun a tous les modeles.
    Chaque sous-classe doit definir l'attribut de classe `table`."""
    table = None

    @classmethod
    def supprimer_par_id(cls, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {cls.table} WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
