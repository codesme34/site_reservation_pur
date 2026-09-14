"""Vues liees a la connexion."""


def vue_login(erreur=False):
    message_erreur = "<p style='color:red'>Email ou mot de passe incorrect.</p>" if erreur else ""
    return f"""
    <h1>Connexion</h1>
    {message_erreur}
    <form action="/login" method="post">
        <input type="text" name="email" placeholder="Email">
        <input type="password" name="password" placeholder="Mot de passe">
        <button type="submit">Se connecter</button>
    </form>
    """
