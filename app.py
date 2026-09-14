"""
Point d'entree : serveur HTTP natif (aucun framework) + controleurs (couche C
du MVC). Les controleurs ci-dessous ne font que lire la requete, appeler les
modeles (models.py) pour parler a la base, et rendre une vue (views.py).
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import bcrypt
import secrets
import time

from models import CompteClient
from views import vue_login, vue_admin_dashboard, vue_modifier_compte


DUREE_SESSION = 30 * 60  # 30 minutes

SESSIONS = {}  # token de session -> {"id": ..., "is_admin": ..., "expire_a": ...}


def get_session(handler):
    """Lit le cookie 'session' de la requete et renvoie les infos utilisateur, ou None."""
    cookie_header = handler.headers.get("Cookie")
    if not cookie_header:
        return None

    cookies = {}
    for morceau in cookie_header.split(";"):
        if "=" in morceau:
            cle, valeur = morceau.strip().split("=", 1)
            cookies[cle] = valeur

    token = cookies.get("session")
    session = SESSIONS.get(token)

    if session is None:
        return None

    if time.time() > session["expire_a"]:
        del SESSIONS[token]  # session perimee, on la nettoie
        return None

    return session


def admin_requis(handler):
    """Renvoie la session si elle existe et est admin, sinon None."""
    session = get_session(handler)
    if session is None or not session["is_admin"]:
        return None
    return session


RATE_LIMITS = {}  # (ip, cle) -> liste des horodatages des requetes recentes


def trop_de_requetes(handler, cle, max_requetes=5, par_secondes=60):
    """Renvoie True si l'IP a depasse la limite pour cette route."""
    ip = handler.client_address[0]
    identifiant = (ip, cle)
    maintenant = time.time()

    horodatages = RATE_LIMITS.get(identifiant, [])
    horodatages = [t for t in horodatages if maintenant - t < par_secondes]

    if len(horodatages) >= max_requetes:
        RATE_LIMITS[identifiant] = horodatages
        return True

    horodatages.append(maintenant)
    RATE_LIMITS[identifiant] = horodatages
    return False


def repondre_429(handler):
    handler.send_response(429)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(b"Trop de tentatives, reessayez dans une minute.")


# Chaque route est associee a une fonction (le controleur) qui gere la requete.
ROUTES_GET = {}
ROUTES_POST = {}


def route(path, methods=("GET",)):
    """Decorateur maison pour enregistrer un controleur sur un chemin et une methode donnes."""
    def decorator(func):
        if "GET" in methods:
            ROUTES_GET[path] = func
        if "POST" in methods:
            ROUTES_POST[path] = func
        return func
    return decorator


@route("/")
def home(handler):
    return "Ça marche !"


@route("/login")
def login_page(handler):
    return vue_login()


@route("/login", methods=("POST",))
def login_submit(handler, body):
    if trop_de_requetes(handler, "login", max_requetes=5, par_secondes=60):
        return repondre_429(handler)

    data = parse_qs(body)
    email = data.get("email", [""])[0]
    password = data.get("password", [""])[0]

    compte = CompteClient.trouver_par_email(email)

    if compte is None or not compte.verifier_mot_de_passe(password):
        handler.send_response(401)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(vue_login(erreur=True).encode("utf-8"))
        return

    token = secrets.token_hex(32)
    SESSIONS[token] = {
        "id": compte.id,
        "is_admin": compte.is_admin,
        "expire_a": time.time() + DUREE_SESSION,
    }

    destination = "/admin" if compte.is_admin else "/"

    handler.send_response(302)
    handler.send_header("Set-Cookie", f"session={token}; HttpOnly; Path=/")
    handler.send_header("Location", destination)
    handler.end_headers()


@route("/admin")
def admin_dashboard(handler):
    session = admin_requis(handler)
    if session is None:
        handler.send_response(403)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(b"403 - Acces reserve aux administrateurs")
        return

    comptes = CompteClient.lister_tous()
    return vue_admin_dashboard(comptes)


@route("/admin/ajouter", methods=("POST",))
def admin_ajouter(handler, body):
    session = admin_requis(handler)
    if session is None:
        handler.send_response(403)
        handler.end_headers()
        return

    if trop_de_requetes(handler, "admin_ecriture", max_requetes=20, par_secondes=60):
        return repondre_429(handler)

    data = parse_qs(body)
    nom = data.get("nom", [""])[0]
    prenom = data.get("prenom", [""])[0]
    email = data.get("email", [""])[0]
    password = data.get("password", [""])[0]
    is_admin = "is_admin" in data

    hash_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    CompteClient.creer(nom, prenom, email, hash_pwd, is_admin)

    handler.send_response(302)
    handler.send_header("Location", "/admin")
    handler.end_headers()


@route("/admin/modifier")
def admin_modifier_page(handler):
    session = admin_requis(handler)
    if session is None:
        handler.send_response(403)
        handler.end_headers()
        return None

    query = parse_qs(urlparse(handler.path).query)
    compte_id = query.get("id", [None])[0]
    compte = CompteClient.trouver_par_id(compte_id)

    if compte is None:
        return "Compte introuvable"

    return vue_modifier_compte(compte)


@route("/admin/modifier", methods=("POST",))
def admin_modifier_submit(handler, body):
    session = admin_requis(handler)
    if session is None:
        handler.send_response(403)
        handler.end_headers()
        return

    if trop_de_requetes(handler, "admin_ecriture", max_requetes=20, par_secondes=60):
        return repondre_429(handler)

    data = parse_qs(body)
    compte_id = data.get("id", [""])[0]
    nom = data.get("nom", [""])[0]
    prenom = data.get("prenom", [""])[0]
    email = data.get("email", [""])[0]
    is_admin = "is_admin" in data

    compte = CompteClient.trouver_par_id(compte_id)
    if compte is not None:
        compte.modifier(nom, prenom, email, is_admin)

    handler.send_response(302)
    handler.send_header("Location", "/admin")
    handler.end_headers()


@route("/admin/supprimer", methods=("POST",))
def admin_supprimer(handler, body):
    session = admin_requis(handler)
    if session is None:
        handler.send_response(403)
        handler.end_headers()
        return

    if trop_de_requetes(handler, "admin_ecriture", max_requetes=20, par_secondes=60):
        return repondre_429(handler)

    data = parse_qs(body)
    compte_id = data.get("id", [""])[0]

    compte = CompteClient.trouver_par_id(compte_id)
    if compte is not None:
        compte.supprimer()

    handler.send_response(302)
    handler.send_header("Location", "/admin")
    handler.end_headers()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        chemin = self.path.split("?")[0]
        func = ROUTES_GET.get(chemin)

        if func is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 - Page non trouvee")
            return

        contenu = func(self)
        if contenu is None:
            return  # le controleur a deja envoye sa propre reponse (ex: 403)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(contenu.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        func = ROUTES_POST.get(self.path)
        if func is None:
            self.send_response(404)
            self.end_headers()
            return

        func(self, body)


if __name__ == "__main__":
    serveur = ThreadingHTTPServer(("0.0.0.0", 5000), Handler)
    print("Serveur demarre sur http://localhost:5000")
    serveur.serve_forever()
