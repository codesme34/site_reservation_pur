"""
Appel a une API externe (Open-Meteo, gratuite, sans cle) pour recuperer
la meteo actuelle d'une ville. Ecrit en Python natif avec urllib
(bibliotheque standard) - aucune librairie tierce (pas de "requests").
"""
import json
import urllib.request
import urllib.parse
import urllib.error

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Codes meteo WMO renvoyes par l'API -> description lisible en francais
CODES_METEO = {
    0: "Ciel dégagé", 1: "Plutôt dégagé", 2: "Partiellement nuageux", 3: "Couvert",
    45: "Brouillard", 48: "Brouillard givrant",
    51: "Bruine légère", 53: "Bruine", 55: "Bruine forte",
    61: "Pluie légère", 63: "Pluie", 65: "Pluie forte",
    71: "Neige légère", 73: "Neige", 75: "Neige forte",
    80: "Averses légères", 81: "Averses", 82: "Averses violentes",
    95: "Orage", 96: "Orage avec grêle", 99: "Orage violent avec grêle",
}


def _get_json(url, params):
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "AirlinesReservation/1.0"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather_for_city(ville):
    """Renvoie {'temperature': float, 'description': str} pour une ville,
    ou None si l'API externe est injoignable ou la ville introuvable."""
    try:
        geo = _get_json(GEOCODING_URL, {"name": ville, "count": 1, "language": "fr"})
        resultats = geo.get("results")
        if not resultats:
            return None

        latitude = resultats[0]["latitude"]
        longitude = resultats[0]["longitude"]

        meteo = _get_json(FORECAST_URL, {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
            "timezone": "auto",
        })
        current = meteo["current"]

        return {
            "temperature": current["temperature_2m"],
            "description": CODES_METEO.get(current["weather_code"], "Météo inconnue"),
        }

    except (urllib.error.URLError, KeyError, ValueError, TimeoutError):
        # l'API externe est indisponible ou repond de facon inattendue :
        # on ne casse jamais l'affichage de la page pour autant
        return None


if __name__ == "__main__":
    print(get_weather_for_city("Paris"))
    print(get_weather_for_city("Nice"))
    print(get_weather_for_city("VilleQuiNexistePas"))
