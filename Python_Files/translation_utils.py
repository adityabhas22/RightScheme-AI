from deep_translator import GoogleTranslator
import streamlit as st
import time
from langdetect import detect

# Supported Languages with their native names
LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "bn": "বাংলা",
    "te": "తెలుగు"
}

@st.cache_resource(show_spinner=False)
def get_translator(target_lang):
    """Get a cached translator instance for the target language"""
    try:
        return GoogleTranslator(source='en', target=target_lang)
    except Exception as e:
        print(f"Error initializing translator: {e}")
        return None

def initialize_translation_settings():
    """Initialize translation settings in session state"""
    if "language" not in st.session_state:
        st.session_state.language = "en"
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = LANGUAGES["en"]

def translate_text(text, target_lang=None):
    """Translate text to target language"""
    if not text or not isinstance(text, str):
        return text
        
    if not target_lang:
        target_lang = st.session_state.get('language', 'en')
    
    if target_lang == 'en':
        return text
    
    try:
        # Get cached translator for target language
        translator = get_translator(target_lang)
        if translator:
            # Split text into smaller chunks if it's too long
            if len(text) > 5000:
                chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
                translated_chunks = [translator.translate(chunk) for chunk in chunks]
                return ' '.join(translated_chunks)
            else:
                return translator.translate(text)
        return text
            
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Fallback to original text if translation fails

def translate_to_english(text: str) -> str:
    """Translate text from any language to English."""
    try:
        # Detect language
        source_lang = detect(text)
        if source_lang == 'en':
            return text
            
        # Translate to English using your translation service
        translator = GoogleTranslator(source=source_lang, target='en')
        translated = translator.translate(text)
        return translated.text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails