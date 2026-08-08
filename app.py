import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
from langdetect import detect, DetectorFactory
import speech_recognition as sr
from PIL import Image
import pytesseract
import io

DetectorFactory.seed = 0  # consistent langdetect results

st.set_page_config(page_title="Language Translator", page_icon="🌍", layout="wide")
st.title("🌍 Language Translation Tool")
st.caption("CodeAlpha AI Internship — Task 1")

languages = GoogleTranslator().get_supported_languages(as_dict=True)
lang_names = [name.title() for name in languages.keys()]
name_to_code = {name.title(): code for name, code in languages.items()}

# Map langdetect's ISO codes to deep_translator names for nicer display
def detect_language_name(text):
    try:
        code = detect(text)
        for name, c in languages.items():
            if c == code:
                return name.title(), code
        return code, code
    except Exception:
        return "Unknown", "auto"

tab1, tab2, tab3, tab4 = st.tabs(["✍️ Text", "📄 File Upload", "🎤 Voice Input", "🖼️ Image (OCR)"])

# ---------------- TAB 1: TEXT + AUTO-DETECT + MULTI-TARGET ----------------
with tab1:
    text_input = st.text_area("Enter text to translate:", height=150, key="text_tab")

    if text_input.strip():
        detected_name, detected_code = detect_language_name(text_input)
        st.info(f"🔍 Detected language: **{detected_name}**")

    target_choices = st.multiselect(
        "Translate into (select up to 4):",
        lang_names,
        default=["French", "Spanish", "German"] if all(l in lang_names for l in ["French","Spanish","German"]) else lang_names[:3],
        max_selections=4
    )

    if st.button("Translate", type="primary", key="translate_text"):
        if not text_input.strip():
            st.warning("Please enter some text.")
        elif not target_choices:
            st.warning("Pick at least one target language.")
        else:
            cols = st.columns(len(target_choices))
            for col, target_name in zip(cols, target_choices):
                with col:
                    st.markdown(f"**{target_name}**")
                    try:
                        tgt_code = name_to_code[target_name]
                        result = GoogleTranslator(source="auto", target=tgt_code).translate(text_input)
                        st.success(result)
                        st.session_state[f"audio_{target_name}"] = (result, tgt_code)
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Listen buttons for last translations
    for target_name in target_choices if 'target_choices' in dir() else []:
        key = f"audio_{target_name}"
        if key in st.session_state:
            if st.button(f"🔊 Listen ({target_name})", key=f"listen_{target_name}"):
                result, tgt_code = st.session_state[key]
                try:
                    tts = gTTS(text=result, lang=tgt_code)
                    tts.save(f"{target_name}.mp3")
                    st.audio(f"{target_name}.mp3", format="audio/mp3")
                except Exception as e:
                    st.warning(f"Speech not available for {target_name}: {e}")

# ---------------- TAB 2: FILE UPLOAD ----------------
with tab2:
    st.write("Upload a `.txt` file to translate its contents.")
    uploaded_file = st.file_uploader("Choose a .txt file", type=["txt"])
    target_file_lang = st.selectbox("Translate to:", lang_names, key="file_target")

    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        st.text_area("Original text:", content, height=150, disabled=True)

        if st.button("Translate File", type="primary"):
            try:
                tgt_code = name_to_code[target_file_lang]
                # Translate in chunks if long (Google has a ~5000 char limit per request)
                chunks = [content[i:i+4500] for i in range(0, len(content), 4500)]
                translated_chunks = [GoogleTranslator(source="auto", target=tgt_code).translate(c) for c in chunks]
                translated_text = " ".join(translated_chunks)

                st.success("Translation complete!")
                st.text_area("Translated text:", translated_text, height=150)

                st.download_button(
                    label="📥 Download translated .txt",
                    data=translated_text,
                    file_name=f"translated_{target_file_lang}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- TAB 3: VOICE INPUT ----------------
with tab3:
    st.write("Upload a short audio file (WAV/AIFF/FLAC) with clear speech to translate it.")
    st.caption("Note: works best with .wav files. Record a voice memo and upload here.")
    audio_file = st.file_uploader("Upload audio", type=["wav", "aiff", "flac"])
    target_voice_lang = st.selectbox("Translate to:", lang_names, key="voice_target")

    if audio_file is not None:
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                spoken_text = recognizer.recognize_google(audio_data)

            st.write("**Recognized speech:**")
            st.info(spoken_text)

            if st.button("Translate Speech", type="primary"):
                tgt_code = name_to_code[target_voice_lang]
                result = GoogleTranslator(source="auto", target=tgt_code).translate(spoken_text)
                st.success(result)

                tts = gTTS(text=result, lang=tgt_code)
                tts.save("voice_output.mp3")
                st.audio("voice_output.mp3", format="audio/mp3")
        except sr.UnknownValueError:
            st.error("Could not understand the audio. Try a clearer recording.")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- TAB 4: OCR (IMAGE) ----------------
with tab4:
    st.write("Upload an image containing text (e.g., a sign, menu, screenshot).")
    image_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    target_ocr_lang = st.selectbox("Translate to:", lang_names, key="ocr_target")

    if image_file is not None:
        image = Image.open(image_file)
        st.image(image, caption="Uploaded image", use_container_width=True)
        # Auto-detect and fix orientation
        try:
            osd = pytesseract.image_to_osd(image)
            rotation_angle = int([line for line in osd.split('\n') if 'Rotate' in line][0].split(':')[-1].strip())
            if rotation_angle != 0:
                image = image.rotate(-rotation_angle, expand=True)
                st.info(f"🔄 Auto-rotated image by {rotation_angle}° for better text recognition")
        except Exception:
            pass  # if orientation detection fails, proceed with original image

        extracted_text = pytesseract.image_to_string(image)
        if extracted_text.strip():
            st.write("**Extracted text:**")
            st.text_area("OCR result:", extracted_text, height=100)

            if st.button("Translate Extracted Text", type="primary"):
                try:
                    tgt_code = name_to_code[target_ocr_lang]
                    result = GoogleTranslator(source="auto", target=tgt_code).translate(extracted_text)
                    st.success(result)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("No text detected in the image. Try a clearer image.")
