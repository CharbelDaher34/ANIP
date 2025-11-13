"""
Utility functions for ingestion.
"""
from datetime import datetime, timezone
from typing import Dict, Any


# Language name to ISO 639-1 code mapping
LANGUAGE_MAP = {
    'english': 'en',
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'italian': 'it',
    'portuguese': 'pt',
    'russian': 'ru',
    'chinese': 'zh',
    'japanese': 'ja',
    'korean': 'ko',
    'arabic': 'ar',
    'hindi': 'hi',
    'dutch': 'nl',
    'swedish': 'sv',
    'turkish': 'tr',
    'polish': 'pl',
    'vietnamese': 'vi',
    'thai': 'th',
    'indonesian': 'id',
    'hebrew': 'he',
    'greek': 'el',
    'czech': 'cs',
    'danish': 'da',
    'finnish': 'fi',
    'norwegian': 'no',
    'ukrainian': 'uk',
}

# Country name to ISO 3166-1 alpha-2 code mapping
COUNTRY_MAP = {
    'united states': 'US',
    'united kingdom': 'GB',
    'canada': 'CA',
    'australia': 'AU',
    'germany': 'DE',
    'france': 'FR',
    'spain': 'ES',
    'italy': 'IT',
    'china': 'CN',
    'japan': 'JP',
    'korea': 'KR',
    'south korea': 'KR',
    'india': 'IN',
    'brazil': 'BR',
    'mexico': 'MX',
    'russia': 'RU',
    'vietnam': 'VN',
    'thailand': 'TH',
    'indonesia': 'ID',
    'philippines': 'PH',
    'saudi arabia': 'SA',
    'uae': 'AE',
    'united arab emirates': 'AE',
    'egypt': 'EG',
    'south africa': 'ZA',
    'argentina': 'AR',
    'netherlands': 'NL',
    'sweden': 'SE',
    'poland': 'PL',
    'turkey': 'TR',
}


def normalize_language_code(language: str) -> str:
    """
    Normalize language to ISO 639-1 code (2-letter).
    
    Args:
        language: Language name or code (e.g., "English", "en", "english")
        
    Returns:
        2-letter ISO 639-1 code (e.g., "en")
    """
    if not language:
        return "en"
    
    lang = language.strip().lower()
    
    # If already a 2-letter code, return it
    if len(lang) == 2 and lang.isalpha():
        return lang
    
    # Check if it's a full language name
    return LANGUAGE_MAP.get(lang, lang[:2] if len(lang) >= 2 else "en")


def normalize_country_code(country: str) -> str:
    """
    Normalize country to ISO 3166-1 alpha-2 code (2-letter).
    
    Args:
        country: Country name or code (e.g., "United States", "US", "vietnam")
        
    Returns:
        2-letter ISO 3166-1 code (e.g., "US")
    """
    if not country:
        return "WORLD"
    
    country_norm = country.strip().lower()
    
    # If already a 2-letter code in uppercase, return it
    if len(country) == 2 and country.isupper():
        return country
    
    # Check if it's a full country name
    return COUNTRY_MAP.get(country_norm, country.upper()[:2] if country else "WORLD")


def parse_datetime(dt_string: str) -> datetime:
    """Parse datetime string to datetime object."""
    try:
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def clean_article_data(article: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate article data."""
    return {
        'title': article.get('title', 'No Title')[:500],
        'content': article.get('content', '')[:10000],
        'source': article.get('source', 'Unknown')[:200],
        'author': article.get('author', 'Unknown')[:200],
        'url': article.get('url', '')[:1000],
        'published_at': article.get('published_at'),
        'language': normalize_language_code(article.get('language', 'en')),
        'region': normalize_country_code(article.get('region', 'US'))
    }

