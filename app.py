from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Chaque route est associee a une fonction qui renvoie le texte/HTML a afficher.
# Cle = chemin de l'URL, valeur = fonction a executer.
ROUTES_GET = {}


def route(path):
    """Decorateur maison pour enregistrer une fonction sur un chemin donne."""
    def decorator(func):
        ROUTES_GET[path] = func
        return func
    return decorator


@route("/")
def home():
    return "Ça marche !"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        func = ROUTES_GET.get(self.path)

        if func is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 - Page non trouvee")
            return

        contenu = func()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(contenu.encode("utf-8"))


if __name__ == "__main__":
    serveur = ThreadingHTTPServer(("0.0.0.0", 5000), Handler)
    print("Serveur demarre sur http://localhost:5000")
    serveur.serve_forever()
