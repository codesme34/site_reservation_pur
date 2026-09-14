"""Vues de l'espace d'administration (gestion des comptes clients)."""
from views.helpers import echapper


def vue_admin_dashboard(comptes):
    lignes_html = ""
    for compte in comptes:
        role = "Admin" if compte.is_admin else "Client"
        lignes_html += f"""<tr>
            <td>{compte.id}</td><td>{echapper(compte.nom)}</td><td>{echapper(compte.prenom)}</td><td>{echapper(compte.email)}</td><td>{role}</td>
            <td>
                <a href="/admin/modifier?id={compte.id}">Modifier</a>
                <form action="/admin/supprimer" method="post" style="display:inline">
                    <input type="hidden" name="id" value="{compte.id}">
                    <button type="submit">Supprimer</button>
                </form>
            </td>
        </tr>"""

    return f"""
    <h1>Gestion des comptes</h1>
    <a href="/logout">Déconnexion</a>
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


def vue_modifier_compte(compte):
    coche = "checked" if compte.is_admin else ""
    return f"""
    <h1>Modifier le compte</h1>
    <form action="/admin/modifier" method="post">
        <input type="hidden" name="id" value="{compte.id}">
        <input type="text" name="nom" value="{echapper(compte.nom)}" required>
        <input type="text" name="prenom" value="{echapper(compte.prenom)}" required>
        <input type="email" name="email" value="{echapper(compte.email)}" required>
        <label><input type="checkbox" name="is_admin" {coche}> Admin</label>
        <button type="submit">Enregistrer</button>
    </form>
    """
