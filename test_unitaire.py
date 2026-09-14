"""
Tests unitaires (module natif unittest, aucune dependance externe type pytest).
Ne teste que la logique pure, isolee de la base de donnees et du reseau,
pour rester de vrais tests UNITAIRES (par opposition aux tests fonctionnels
bout-en-bout deja realises manuellement pendant le developpement).
"""
import time
import unittest

from views.helpers import echapper
from app import trop_de_requetes, get_session, SESSIONS, RATE_LIMITS


class FausseHandler:
    """Simule juste ce dont trop_de_requetes/get_session ont besoin d'une
    requete HTTP, sans avoir a demarrer un vrai serveur."""
    def __init__(self, ip="127.0.0.1", cookie=""):
        self.client_address = (ip, 12345)
        self.headers = {"Cookie": cookie}


class TestEchapper(unittest.TestCase):
    def test_neutralise_les_balises_html(self):
        self.assertEqual(echapper("<script>alert('x')</script>"), "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;")

    def test_laisse_le_texte_normal_inchange(self):
        self.assertEqual(echapper("Jean Dupont"), "Jean Dupont")

    def test_convertit_les_non_chaines(self):
        self.assertEqual(echapper(42), "42")


class TestRateLimit(unittest.TestCase):
    def setUp(self):
        RATE_LIMITS.clear()

    def test_autorise_sous_la_limite(self):
        handler = FausseHandler()
        for _ in range(3):
            self.assertFalse(trop_de_requetes(handler, "test_route", max_requetes=5, par_secondes=60))

    def test_bloque_au_dela_de_la_limite(self):
        handler = FausseHandler()
        for _ in range(5):
            trop_de_requetes(handler, "test_route2", max_requetes=5, par_secondes=60)
        self.assertTrue(trop_de_requetes(handler, "test_route2", max_requetes=5, par_secondes=60))

    def test_deux_ip_differentes_ne_se_gene_pas(self):
        handler1 = FausseHandler(ip="1.1.1.1")
        handler2 = FausseHandler(ip="2.2.2.2")
        for _ in range(5):
            trop_de_requetes(handler1, "test_route3", max_requetes=5, par_secondes=60)
        # handler2 a une IP differente : ne doit pas etre bloque par les
        # tentatives de handler1
        self.assertFalse(trop_de_requetes(handler2, "test_route3", max_requetes=5, par_secondes=60))


class TestSession(unittest.TestCase):
    def setUp(self):
        SESSIONS.clear()

    def test_aucun_cookie_renvoie_none(self):
        handler = FausseHandler(cookie="")
        self.assertIsNone(get_session(handler))

    def test_cookie_inconnu_renvoie_none(self):
        handler = FausseHandler(cookie="session=jeton_qui_nexiste_pas")
        self.assertIsNone(get_session(handler))

    def test_session_valide_est_retrouvee(self):
        SESSIONS["jeton123"] = {"id": 1, "is_admin": False, "expire_a": time.time() + 60}
        handler = FausseHandler(cookie="session=jeton123")
        session = get_session(handler)
        self.assertIsNotNone(session)
        self.assertEqual(session["id"], 1)

    def test_session_expiree_renvoie_none_et_est_nettoyee(self):
        SESSIONS["jeton_expire"] = {"id": 1, "is_admin": False, "expire_a": time.time() - 1}
        handler = FausseHandler(cookie="session=jeton_expire")
        self.assertIsNone(get_session(handler))
        self.assertNotIn("jeton_expire", SESSIONS)  # doit avoir ete nettoyee


if __name__ == "__main__":
    unittest.main()
