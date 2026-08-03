"""Multi-language translation using the googletrans library."""

WORD = "sampilin"

LANGUAGES = [
    "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs",
    "bg", "ca", "ceb", "ny", "zh-cn", "zh-tw", "co", "hr", "cs",
    "da", "nl", "en", "eo", "et", "fi", "fr", "fy", "gl", "ka",
    "de", "el", "gu", "ht", "ha", "haw", "he", "hi", "hmn", "hu",
    "is", "ig", "id", "ga", "it", "ja", "jw", "kn", "kk", "km",
    "rw", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk",
    "mg", "ms", "ml",
]


def translate_word(word=WORD, languages=LANGUAGES, translator=None):
    """Translate *word* into every language in *languages*.

    Returns a dict mapping language code -> translated text.
    A translator instance may be injected for testing.
    """
    if translator is None:
        from googletrans import Translator  # imported lazily (lib is optional)

        translator = Translator()

    results = {}
    for lang in languages:
        translation = translator.translate(word, dest=lang)
        results[lang] = translation.text
    return results


def main():
    translations = translate_word()
    for lang, text in translations.items():
        print(f"{lang}: {text}")


if __name__ == "__main__":
    main()
