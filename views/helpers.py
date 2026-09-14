"""Utilitaires partages par les vues."""
import html


def echapper(texte):
    """Neutralise les caracteres HTML dangereux (protection XSS)."""
    return html.escape(str(texte))
