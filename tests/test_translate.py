"""Tests for scripts/translate.py."""

from scripts import translate


def test_translate_word_returns_all_languages(fake_translator):
    mapping = {"es": "hola", "fr": "bonjour", "de": "hallo"}
    translator = fake_translator(mapping)
    results = translate.translate_word(
        word="hello", languages=["es", "fr", "de"], translator=translator
    )
    assert results == {"es": "hola", "fr": "bonjour", "de": "hallo"}


def test_translate_word_default_word(fake_translator):
    translator = fake_translator({})
    results = translate.translate_word(
        languages=["en"], translator=translator
    )
    assert results == {"en": "[en]sampilin"}


def test_translate_word_uses_default_languages(fake_translator):
    translator = fake_translator({})
    results = translate.translate_word(translator=translator)
    assert set(results.keys()) == set(translate.LANGUAGES)


def test_translate_word_empty_languages(fake_translator):
    translator = fake_translator({})
    results = translate.translate_word(languages=[], translator=translator)
    assert results == {}
