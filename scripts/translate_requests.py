"""Translate 'Hello, world!' into 15 languages via the Google Translate web API."""

import requests

TEXT = "Hello, world!"

LANGUAGES = [
    "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh-CN",
    "ar", "hi", "bn", "tr", "nl", "sv",
]

BASE_URL = "https://translate.googleapis.com/translate_a/single"


def build_url(text, target_lang):
    """Build the Google Translate web-API URL for *text* -> *target_lang*."""
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": text,
    }
    return BASE_URL, params


def translate_text(text=TEXT, languages=LANGUAGES, fetcher=None):
    """Translate *text* into every language in *languages*.

    *fetcher* is an optional callable ``(url, params)`` -> requests.Response
    used for testing.  Returns dict lang -> translated text (or "Error {code}").
    """
    if fetcher is None:
        def fetcher(url, params): return requests.get(url, params=params)  # noqa: E731

    results = {}
    for lang in languages:
        url, params = build_url(text, lang)
        response = fetcher(url, params)
        if response.status_code == 200:
            results[lang] = response.json()[0][0][0]
        else:
            results[lang] = f"Error {response.status_code}"
    return results


def main():
    translations = translate_text()
    for lang, text in translations.items():
        print(f"{lang}: {text}")


if __name__ == "__main__":
    main()
