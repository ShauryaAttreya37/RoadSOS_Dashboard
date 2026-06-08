from __future__ import annotations

import json
import os
import urllib.parse
import requests
import streamlit as st

LANGUAGES: dict[str, str] = {
    "English": "en",
    "Hindi (हिन्दी)": "hi",
    "Bengali (বাংলা)": "bn",
    "Marathi (मराठी)": "mr",
    "Telugu (తెలుగు)": "te",
    "Tamil (தமிழ்)": "ta",
    "Gujarati (ગુજરાતી)": "gu",
    "Urdu (اردو)": "ur",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Odia (ଓଡ଼ିଆ)": "or",
    "Malayalam (മലയാളം)": "ml",
    "Punjabi (ਪੰਜਾਬੀ)": "pa",
    "Assamese (অসমীয়া)": "as",
    "Maithili (मैथिली)": "mai",
    "Santali (संताली)": "sat",
    "Kashmiri (कश्मीरी)": "ks",
    "Nepali (नेपाली)": "ne",
    "Konkani (कोंकणी)": "kok",
    "Sindhi (سنڌي)": "sd",
    "Dogri (डोगरी)": "doi",
    "Manipuri (মৈতৈলোন)": "mni",
    "Sanskrit (संस्कृतम्)": "sa",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Portuguese (Português)": "pt",
    "Italian (Italiano)": "it",
    "Russian (Русский)": "ru",
    "Japanese (日本語)": "ja",
    "Korean (한국어)": "ko",
    "Chinese Simplified (简体中文)": "zh-CN",
    "Chinese Traditional (繁體中文)": "zh-TW",
    "Arabic (العربية)": "ar",
    "Turkish (Türkçe)": "tr",
    "Vietnamese (Tiếng Việt)": "vi",
    "Polish (Polski)": "pl",
    "Ukrainian (Українська)": "uk",
    "Dutch (Nederlands)": "nl",
    "Thai (ไทย)": "th",
    "Swedish (Svenska)": "sv",
    "Indonesian (Bahasa Indonesia)": "id",
    "Malay (Bahasa Melayu)": "ms",
    "Persian (فارسی)": "fa",
    "Hebrew (עברית)": "he",
    "Greek (Ελληνικά)": "el",
    "Czech (Čeština)": "cs",
    "Romanian (Română)": "ro",
    "Hungarian (Magyar)": "hu",
    "Finnish (Suomi)": "fi",
    "Norwegian (Norsk)": "no",
    "Danish (Dansk)": "da",
    "Slovak (Slovenčina)": "sk",
    "Croatian (Hrvatski)": "hr",
    "Serbian (Српски)": "sr",
    "Bulgarian (Български)": "bg",
    "Lithuanian (Lietuvių)": "lt",
    "Latvian (Latviešu)": "lv",
    "Estonian (Eesti)": "et",
    "Slovenian (Slovenščina)": "sl",
    "Irish (Gaeilge)": "ga",
    "Welsh (Cymraeg)": "cy",
    "Icelandic (Íslenska)": "is",
    "Maltese (Malti)": "mt",
    "Albanian (Shqip)": "sq",
    "Macedonian (Македонски)": "mk",
    "Bosnian (Bosanski)": "bs",
    "Georgian (ქართული)": "ka",
    "Armenian (Հայերեն)": "hy",
    "Azerbaijani (Azərbaycan)": "az",
    "Kazakh (Қазақша)": "kk",
    "Uzbek (Oʻzbekcha)": "uz",
    "Turkmen (Türkmençe)": "tk",
    "Kyrgyz (Кыргызча)": "ky",
    "Tajik (Тоҷикӣ)": "tg",
    "Mongolian (Монгол)": "mn",
    "Sinhala (සිංහල)": "si",
    "Burmese (မြန်မာဘာသာ)": "my",
    "Khmer (ខ្មែរ)": "km",
    "Lao (ລາວ)": "lo",
    "Tagalog (Filipino)": "tl",
    "Javanese (Basa Jawa)": "jv",
    "Sundanese (Basa Sunda)": "su",
    "Swahili (Kiswahili)": "sw",
    "Amharic (አማርኛ)": "am",
    "Yoruba (Yorùbá)": "yo",
    "Igbo (Asụsụ Igbo)": "ig",
    "Zulu (isiZulu)": "zu",
    "Xhosa (isiXhosa)": "xh",
    "Afrikaans (Afrikaans)": "af",
    "Somali (Soomaali)": "so",
    "Malagasy (Fiteny Malagasy)": "mg",
    "Esperanto (Esperanto)": "eo",
    "Latin (Latina)": "la",
    "Maori (Māori)": "mi",
    "Hawaiian (ʻŌlelo Hawaiʻi)": "haw",
    "Samoan (Gagana Sāmoa)": "sm",
    "Yiddish (ייִדיש)": "yi",
    "Galician (Galego)": "gl",
    "Basque (Euskara)": "eu",
    "Catalan (Català)": "ca",
}

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "translations_cache.json")


def load_cache() -> dict[str, str]:
    if not os.path.exists(CACHE_FILE):
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
        except Exception:
            pass
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache: dict[str, str]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def translate_text(text: str, target_lang: str) -> str:
    if not text or not target_lang or target_lang == "en":
        return text

    # Remove trailing newlines and escape queries
    query = text.strip()
    if not query:
        return text

    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(query)}"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            result = response.json()
            translated_parts = [part[0] for part in result[0] if part and part[0]]
            translated_text = "".join(translated_parts)
            if translated_text:
                # Retain original formatting context if needed
                if text.endswith("\n"):
                    translated_text += "\n"
                if text.startswith("\n"):
                    translated_text = "\n" + translated_text
                return translated_text
    except Exception:
        pass

    return text


def tr(text: str) -> str:
    """Translate string using selected language name in session state."""
    if "translations_cache" not in st.session_state:
        st.session_state.translations_cache = load_cache()

    selected_lang_name = st.session_state.get("selected_language", "English")
    target_code = LANGUAGES.get(selected_lang_name, "en")
    
    if target_code == "en" or not text or not isinstance(text, str):
        return text

    cache_key = f"{target_code}:{text}"
    if cache_key in st.session_state.translations_cache:
        return st.session_state.translations_cache[cache_key]

    translated = translate_text(text, target_code)
    st.session_state.translations_cache[cache_key] = translated
    
    # Save back to persistent storage
    file_cache = load_cache()
    file_cache[cache_key] = translated
    save_cache(file_cache)
    
    return translated
