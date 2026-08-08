import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

st.set_page_config(page_title="Language Translator", page_icon="🌍")
st.title("🌍 Language Translation Tool")
st.caption("CodeAlpha AI Internship — Task 1")

languages = GoogleTranslator().get_supported_languages(as_dict=True)
lang_names = [name.title() for name in languages.keys()]

col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("From", ["Auto-Detect"] + lang_names)
with col2:
    target_lang = st.selectbox("To", lang_names, index=lang_names.index("French") if "French" in lang_names else 0)

text_input = st.text_area("Enter text to translate:", height=150)

if st.button("Translate", type="primary"):
    if text_input.strip():
        try:
            src_code = "auto" if source_lang == "Auto-Detect" else languages[source_lang.lower()]
            tgt_code = languages[target_lang.lower()]
            result = GoogleTranslator(source=src_code, target=tgt_code).translate(text_input)

            st.success("Translated Text:")
            st.write(result)
            st.session_state["translated"] = result
            st.session_state["tgt_code"] = tgt_code
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter some text.")

if "translated" in st.session_state:
    if st.button("🔊 Listen"):
        try:
            tts = gTTS(text=st.session_state["translated"], lang=st.session_state["tgt_code"])
            tts.save("output.mp3")
            audio_file = open("output.mp3", "rb")
            st.audio(audio_file.read(), format="audio/mp3")
        except Exception as e:
            st.warning(f"Speech not available for this language: {e}")

    st.button("📋 Copy Text", on_click=lambda: st.write("Use Ctrl+C on the text above"))
