"""Vue du tableau de bord client (compte connecte, non-admin)."""
from views.helpers import echapper


def vue_client_dashboard(compte, meteo_paris):
    """meteo_paris : dict {'temperature', 'description'} ou None si l'API
    externe est indisponible (donnee venant d'une API externe, Cr 3.a.3)."""
    if meteo_paris is not None:
        bloc_meteo = f"{meteo_paris['temperature']}°C, {echapper(meteo_paris['description'])}"
    else:
        bloc_meteo = "Météo indisponible pour le moment"

    return f"""
    <h1>Bienvenue {echapper(compte.prenom)}</h1>
    <p>Vous êtes connecté en tant que client.</p>
    <a href="/logout">Déconnexion</a>

    <h2>Mes informations</h2>
    <form action="/client/modifier" method="post">
        <input type="text" name="nom" value="{echapper(compte.nom)}" required>
        <input type="text" name="prenom" value="{echapper(compte.prenom)}" required>
        <input type="email" name="email" value="{echapper(compte.email)}" required>
        <button type="submit">Enregistrer mes informations</button>
    </form>

    <h2>Supprimer mon compte</h2>
    <p><em>Cette action est definitive et supprime toutes vos donnees personnelles.</em></p>
    <form action="/client/supprimer" method="post">
        <input type="password" name="password" placeholder="Confirmez avec votre mot de passe" required>
        <button type="submit">Supprimer definitivement mon compte</button>
    </form>

    <h2>Paris</h2>
    <div id="horloge-paris" style="border:1px solid #ccc; padding:12px; display:inline-block;">
        <p id="heure-paris" style="font-size:1.5em; font-weight:bold;"></p>
        <p>{bloc_meteo}</p>
    </div>

    <script>
        function majHorloge() {{
            const maintenant = new Date();
            const heure = maintenant.toLocaleTimeString('fr-FR', {{ timeZone: 'Europe/Paris' }});
            document.getElementById('heure-paris').textContent = heure;
        }}
        majHorloge();
        setInterval(majHorloge, 1000);
    </script>
    """
