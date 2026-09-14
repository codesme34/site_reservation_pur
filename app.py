from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from Database.db import get_connection
import bcrypt
import secrets
import html
import time


def echapper(texte):
    """Neutralise les caracteres HTML dangereux (protection XSS)."""
    return html.escape(str(texte))


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

def admin_requis(handler):
    """Renvoie la session si elle existe et est admin, sinon None."""
    session = get_session(handler)
    if session is None or not session["is_admin"]:
        return None
    return session




# Chaque route est associee a une fonction qui renvoie le texte/HTML a afficher.
# Cle = chemin de l'URL, valeur = fonction a executer.
ROUTES_GET = {}
ROUTES_POST = {}


def route(path, methods=("GET",)):
    """Decorateur maison pour enregistrer une fonction sur un chemin et une methode donnes."""
    def decorator(func):
        if "GET" in methods:
            ROUTES_GET[path] = func
        if "POST" in methods:
            ROUTES_POST[path] = func
        return func
    return decorator


@route("/")
def home(handler):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotels")
    nombre_hotels = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return f"Ça marche ! Il y a {nombre_hotels} hôtels en base."



@route("/login") #get
def login_page(handler):
    return """
    <h1>Connexion</h1>
    <form action="/login" method="post">
        <input type="text" name="email" placeholder="Email">
        <input type="password" name="password" placeholder="Mot de passe">
        <button type="submit">Se connecter</button>
    </form>
    """

@route("/login", methods=("POST",)) # post
def login_submit(handler, body):
    if trop_de_requetes(handler, "login", max_requetes=5, par_secondes=60):
        return repondre_429(handler)

    data = parse_qs(body)
    email = data.get("email", [""])[0]
    password = data.get("password", [""])[0]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, mdp, is_admin FROM compte_client WHERE email = %s", (email,))
    ligne = cursor.fetchone()
    cursor.close()
    conn.close()

    if ligne is None or not bcrypt.checkpw(password.encode("utf-8"), ligne[1].encode("utf-8")):
        handler.send_response(401)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(b"Email ou mot de passe incorrect. <a href='/login'>Reessayer</a>")
        return

    user_id, _, is_admin = ligne
    token = secrets.token_hex(32)
    SESSIONS[token] = {
        "id": user_id,
        "is_admin": is_admin,
        "expire_a": time.time() + DUREE_SESSION,
    }

    destination = "/admin" if is_admin else "/"

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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, prenom, email, is_admin FROM compte_client ORDER BY id")
    comptes = cursor.fetchall()
    cursor.close()
    conn.close()

    lignes_html = ""
    for compte_id, nom, prenom, email, is_admin in comptes:
        role = "Admin" if is_admin else "Client"
        lignes_html += f"""<tr>
            <td>{compte_id}</td><td>{echapper(nom)}</td><td>{echapper(prenom)}</td><td>{echapper(email)}</td><td>{role}</td>
            <td>
                <a href="/admin/modifier?id={compte_id}">Modifier</a>
                <form action="/admin/supprimer" method="post" style="display:inline">
                    <input type="hidden" name="id" value="{compte_id}">
                    <button type="submit">Supprimer</button>
                </form>
            </td>
        </tr>"""



    return f"""
    <h1>Gestion des comptes</h1>
    <table border="1">
        <tr><th>ID</th><th>Nom</th><th>Prenom</th><th>Email</th><th>Role</th></tr>
        {lignes_html}
    </table>

    <h2>Ajouter un compte</h2>
    <form action="/admin/ajouter" method="post">
        <input type="text" name="nom" placeholder="Nom" required>
        <input type="text" name="prenom" placeholder="Prenom" required>
        <input type="email" name="email" placeholder="Email" required>
        <input type="password" name="password" placeholder="Mot de passe" required>
        <label><input type="checkbox" name="is_admin"> Admin</label>
        <button type="submit">Ajouter</button>
    </form>

    """
    
    


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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO compte_client (nom, prenom, email, mdp, is_admin) VALUES (%s, %s, %s, %s, %s)",
        (nom, prenom, email, hash_pwd, is_admin)
    )
    conn.commit()
    cursor.close()
    conn.close()

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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, prenom, email, is_admin FROM compte_client WHERE id = %s", (compte_id,))
    compte = cursor.fetchone()
    cursor.close()
    conn.close()

    if compte is None:
        return "Compte introuvable"

    _, nom, prenom, email, is_admin = compte
    coche = "checked" if is_admin else ""

    return f"""
    <h1>Modifier le compte</h1>
    <form action="/admin/modifier" method="post">
        <input type="hidden" name="id" value="{compte_id}">
        <input type="text" name="nom" value="{echapper(nom)}" required>
        <input type="text" name="prenom" value="{echapper(prenom)}" required>
        <input type="email" name="email" value="{echapper(email)}" required>
        <label><input type="checkbox" name="is_admin" {coche}> Admin</label>
        <button type="submit">Enregistrer</button>
    </form>
    """


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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE compte_client SET nom = %s, prenom = %s, email = %s, is_admin = %s WHERE id = %s",
        (nom, prenom, email, is_admin, compte_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

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

    conn = get_connection()
    cursor = conn.cursor()
    # pas de ON DELETE CASCADE en base : on supprime d'abord les reservations liees
    cursor.execute("DELETE FROM reservations_hotel WHERE client_id = %s", (compte_id,))
    cursor.execute("DELETE FROM reservations_vol WHERE client_id = %s", (compte_id,))
    cursor.execute("DELETE FROM compte_client WHERE id = %s", (compte_id,))
    conn.commit()
    cursor.close()
    conn.close()

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
            return  # la fonction a deja envoye sa propre reponse (ex: 403)

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
