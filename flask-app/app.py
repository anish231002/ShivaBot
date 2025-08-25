from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import difflib
import os
import re
import chardet
from google.cloud import texttospeech
import uuid

# --- CONFIGURATION ---
ENGLISH_CSV_PATH = r"C:\Users\user\Desktop\voicebot flask\flask-app\shivaji_maharaj_chatbot_royal_tone.csv"
MARATHI_CSV_PATH = r"C:\Users\user\Desktop\voicebot flask\flask-app\maharaj_qA.csv"
HINDI_CSV_PATH = r"C:\Users\user\Desktop\voicebot flask\flask-app\maharaj_qA-Hindi.csv"
AUDIO_FOLDER = r"C:\Users\user\Desktop\voicebot flask\flask-app\audio"

app = Flask(__name__)
CORS(app)

# --- LOAD CSV DATA ---
def load_data():
    try:
        # Load Marathi CSV
        marathi_qa_dict = {}
        with open(MARATHI_CSV_PATH, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding'] or 'utf-8'
            print(f"Reading Marathi CSV with encoding: {encoding}")
            marathi_df = pd.read_csv(MARATHI_CSV_PATH, encoding=encoding).fillna('')
            
            for _, row in marathi_df.iterrows():
                keyword = str(row["Keyword"]).strip().lower()
                marathi_qa_dict[keyword] = {
                    "answer": str(row["Answer"]).strip(),
                    "tone": str(row.get("Tone", "")).strip(),
                    "followup": str(row.get("Follow-up", "")).strip(),
                    "Answer_if_Yes": str(row.get("Answer_if_Yes", "")).strip(),
                    "audio_file": str(row.get("AudioFile", "")).strip(),
                    "language": "marathi"
                }
        
        # Load English CSV
        english_qa_dict = {}
        with open(ENGLISH_CSV_PATH, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding'] or 'utf-8'
            print(f"Reading English CSV with encoding: {encoding}")
            english_df = pd.read_csv(ENGLISH_CSV_PATH, encoding=encoding).fillna('')
            
            for _, row in english_df.iterrows():
                keyword = str(row["Keyword"]).strip().lower()
                english_qa_dict[keyword] = {
                    "answer": str(row["Answer"]).strip(),
                    "tone": str(row.get("Tone", "")).strip(),
                    "followup": str(row.get("Follow-up", "")).strip(),
                    "Answer_if_Yes": str(row.get("Answer_if_Yes", "")).strip(),
                    "audio_file": str(row.get("AudioFile", "")).strip(),
                    "language": "english"
                }
        
        # Load Hindi CSV
        hindi_qa_dict = {}
        with open(HINDI_CSV_PATH, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding'] or 'utf-8'
            print(f"Reading Hindi CSV with encoding: {encoding}")
            hindi_df = pd.read_csv(HINDI_CSV_PATH, encoding=encoding).fillna('')
            
            for _, row in hindi_df.iterrows():
                keyword = str(row["Keyword"]).strip().lower()
                hindi_qa_dict[keyword] = {
                    "answer": str(row["Answer"]).strip(),
                    "tone": str(row.get("Tone", "")).strip(),
                    "followup": str(row.get("Follow-up", "")).strip(),
                    "Answer_if_Yes": str(row.get("Answer_if_Yes", "")).strip(),
                    "audio_file": str(row.get("AudioFile", "")).strip(),
                    "language": "hindi"
                }
        
        print(f"Loaded {len(marathi_qa_dict)} Marathi entries, {len(english_qa_dict)} English entries, and {len(hindi_qa_dict)} Hindi entries")
        
        # Fallback responses for all three languages
        marathi_fallback = {
            "answer": "कृपया फक्त माझ्याबद्दल आणि मराठा साम्राज्याबद्दल विचारा..",
            "tone": "royal",
            "followup": "",
            "Answer_if_Yes": "",
            "audio_file": "",
            "language": "marathi"
        }
        
        english_fallback = {
            "answer": "Please ask me about Maratha Empire and myself only.",
            "tone": "royal",
            "followup": "",
            "Answer_if_Yes": "",
            "audio_file": "",
            "language": "english"
        }
        
        hindi_fallback = {
            "answer": "कृपया केवल मेरे बारे में और मराठा साम्राज्य के बारे में पूछें।",
            "tone": "royal",
            "followup": "",
            "Answer_if_Yes": "",
            "audio_file": "",
            "language": "hindi"
        }
        
        return marathi_qa_dict, english_qa_dict, hindi_qa_dict, marathi_fallback, english_fallback, hindi_fallback
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        fallback = {"answer": "Data file missing.", "tone": "", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": "english"}
        return {}, {}, {}, fallback, fallback, fallback

marathi_qa_dict, english_qa_dict, hindi_qa_dict, marathi_fallback, english_fallback, hindi_fallback = load_data()
last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": "english"}

def detect_language(query):
    """Enhanced language detection with phonetic pattern matching for all 3 languages"""
    query_lower = query.lower().strip()
    
    # First check for Devanagari script (Marathi/Hindi)
    devanagari_chars = re.findall(r'[\u0900-\u097F]', query)
    if devanagari_chars and len(devanagari_chars) > len(query) * 0.3:
        # Need to differentiate between Marathi and Hindi Devanagari
        # Check for specific Marathi words/patterns
        marathi_specific = [
            r'\b(तुम्ही|तू|आहात|आहेस|काय|कसा|कुठे)\b',
            r'\b(मराठा|स्वराज्य|छत्रपती|मावळे)\b'
        ]
        
        for pattern in marathi_specific:
            if re.search(pattern, query):
                return "marathi"
        
        # Check for Hindi specific words
        hindi_specific = [
            r'\b(आप|तुम|हैं|है|क्या|कैसे|कहाँ|हो)\b',
            r'\b(मराठा|स्वराज्य|छत्रपति|मावले)\b'
        ]
        
        for pattern in hindi_specific:
            if re.search(pattern, query):
                return "hindi"
        
        # Default to Marathi if unclear
        return "marathi"
    
    # Phonetic patterns for Hindi (speech-to-text conversions) - CHECK HINDI FIRST
    hindi_phonetic_patterns = [
        r'\b(aap|aapka|aapki)\s+(kaun|kon)\s*(ho|hain|hai)\b',  # आप कौन हो/हैं - FIXED
        r'\b(tum|tumko|tumka)\s+(kaun|kon)\s*(ho|hain|hai)\b',  # तुम कौन हो/हैं
        r'\b(aap|aapka|aapki)\s+(naam|nam)\s*(kya|kyaa)\b',  # आपका नाम क्या
        r'\b(kya|kyaa)\s+(hai|hain|ho)\b',  # क्या है/हो
        r'\b(kaise|kaisse)\s+(hain|hai|ho)\b',  # कैसे हैं/हो
        r'\b(kahan|kaha)\s+(hain|hai|ho)\b',  # कहाँ हैं/हो
        r'\b(mera|meraa)\s+(naam|nam)\b',  # मेरा नाम
        r'\b(shivaji|sivaji|chivaji)\s*(maharaj|maharaja)\b',  # शिवाजी महाराज
        r'\b(abe|abey)\s+.*\s+(bhok|bol)\s+.*\s+(badtameez|badtamiz)\b',  # Inappropriate language
    ]
    
    # Phonetic patterns for Marathi (speech-to-text conversions)
    marathi_phonetic_patterns = [
        r'\b(tumi|tumhi|tyoumi|tumhee)\s+(kon|kona|kaun)\s*(hai|aahat|ahat|ahaat|aahet)\b',
        r'\b(tu|tuu)\s+(kon|kona|kaun)\s*(aahes|ahes|ahai)\b',
        r'\b(kay|kaay|kya)\s+(aahe|ahe|hai)\b',
        r'\b(kasa|kasha|kaisa)\s*(aahat|ahat|ahaat)\b',
        r'\b(kuthe|kutha|kaha)\s*(aahat|ahat|ahaat)\b',
        r'\bmaza\s*(naam|naav|nav)\b',
        r'\b(shivaji|sivaji|chivaji|shivaaji)\b',
        r'\b(maharaj|maharaja|maharaaj|mahaaraaj)\b',
    ]
    
    # Check Hindi patterns FIRST
    for pattern in hindi_phonetic_patterns:
        if re.search(pattern, query_lower):
            print(f"Detected Hindi phonetic pattern: {pattern}")
            return "hindi"
    
    # Then check Marathi patterns
    for pattern in marathi_phonetic_patterns:
        if re.search(pattern, query_lower):
            print(f"Detected Marathi phonetic pattern: {pattern}")
            return "marathi"
    
    # Common English patterns that should remain English
    english_patterns = [
        r'\b(who\s+are\s+you|what\s+is|how\s+are|where\s+are)\b',
        r'\b(tell\s+me|show\s+me|explain|describe)\b',
        r'\b(history|empire|battle|fort|king)\b'
    ]
    
    for pattern in english_patterns:
        if re.search(pattern, query_lower):
            return "english"
    
    return "english"  # Default to English

def preprocess_input(text, language="english"):
    """Language-specific text preprocessing"""
    if language == "english":
        COMMON_CORRECTIONS = {
            "hu r u": "who are you",
            "wht": "what",
            "r u": "are you",
            "ur": "your",
            "u": "you",
            "thx": "thanks",
            "pls": "please",
            "plz": "please",
        }
        
        text = text.strip().lower()
        for wrong, correct in COMMON_CORRECTIONS.items():
            if wrong in text:
                text = text.replace(wrong, correct)
    else:
        # For Marathi and Hindi, just clean whitespace and convert to lowercase
        text = text.strip().lower()
    
    return text

def check_inappropriate_language(query):
    """Check for inappropriate language and return appropriate response"""
    query_lower = query.lower().strip()
    
    # Pattern for the specific inappropriate phrase
    inappropriate_patterns = [
        r'\b(abe|abey)\s+.*\s+(kaun|kon)\s+.*\s+(bhok|bol)\s+.*\s+(badtameez|badtamiz)\b',
        r'\b(abe|abey)\s+(kaun|kon)\s+(bhok|bol)\s+.*\s+(badtameez|badtamiz)\b',
    ]
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, query_lower):
            return {
                "answer": "तुझा बाप बोलतोय",
                "tone": "",
                "followup": "",
                "Answer_if_Yes": "",
                "audio_file": "",
                "language": "marathi"
            }
    
    return None

def get_response(query, language=None):
    original_query = query
    query = query.strip().lower()
    print(f"Processing query: {query}")
    
    # First check for inappropriate language
    inappropriate_response = check_inappropriate_language(query)
    if inappropriate_response:
        print("Detected inappropriate language, returning special response")
        return inappropriate_response
    
    # Auto-detect language if not specified
    if language is None:
        language = detect_language(query)
    
    # Select appropriate dataset and fallback
    if language == "marathi":
        qa_dict = marathi_qa_dict
        fallback_response = marathi_fallback
    elif language == "hindi":
        qa_dict = hindi_qa_dict
        fallback_response = hindi_fallback
    else:
        qa_dict = english_qa_dict
        fallback_response = english_fallback
    
    print(f"Using {language} dataset")
    
    # Create phonetic mappings for better matching
    if language == "marathi":
        phonetic_mappings = {
            r'\b(tumi|tumhi|tyoumi|tumhee)\s+(kon|kona|kaun)\s*(hai|aahat|ahat|ahaat|aahet)\b': 'तुम्ही कोण आहात',
            r'\b(tu|tuu)\s+(kon|kona|kaun)\s*(aahes|ahes|ahai)\b': 'तू कोण आहेस',
            r'\b(kay|kaay|kya)\s+(aahe|ahe|hai)\b': 'काय आहे',
            r'\bmaza\s*(naam|naav|nav)\b': 'माझं नाव',
            r'\b(shivaji|sivaji|chivaji|shivaaji)\s*(maharaj|maharaja|maharaaj)?\b': 'शिवाजी महाराज',
        }
    elif language == "hindi":
        phonetic_mappings = {
            # FIXED: removed the \ho typo
            r'\b(aap|aapka|aapki)\s+(kaun|kon)\s*(ho|hain|hai)\b': 'आप कौन हैं',
            r'\b(tum|tumko|tumka)\s+(kaun|kon)\s*(ho|hain|hai)\b': 'तुम कौन हो',
            r'\b(aap|aapka|aapki)\s+(naam|nam)\s*(kya|kyaa)\b': 'आपका नाम क्या',
            r'\b(kya|kyaa)\s+(hai|hain|ho)\b': 'क्या है',
            r'\bmera\s*(naam|nam)\b': 'मेरा नाम',
            r'\b(shivaji|sivaji|chivaji)\s*(maharaj|maharaja)\b': 'शिवाजी महाराज',
        }
    else:
        phonetic_mappings = {}
    
    # Try phonetic matching first
    if phonetic_mappings:
        converted_query = query
        for phonetic_pattern, equivalent in phonetic_mappings.items():
            if re.search(phonetic_pattern, query):
                converted_query = equivalent.lower()
                print(f"Converted phonetic query '{query}' to '{converted_query}'")
                break
        
        # Try matching with converted query first
        for keyword in qa_dict:
            if keyword in converted_query or converted_query in keyword:
                print(f"Found phonetic match: {keyword}")
                return qa_dict[keyword]
    
    # Enhanced fuzzy matching for similar phrases
    if language == "hindi":
        # Create variations for "who are you" type questions
        who_variations = [
            'आप कौन हैं', 'आप कौन हो', 'तुम कौन हो', 'तुम कौन हैं'
        ]
        
        # Check if query matches any "who are you" pattern
        who_patterns = [
            r'\b(aap|aapka|aapki)\s+(kaun|kon)',
            r'\b(tum|tumko|tumka)\s+(kaun|kon)',
            r'आप कौन', r'तुम कौन'
        ]
        
        for pattern in who_patterns:
            if re.search(pattern, query):
                print("Found Hindi 'who are you' type question")
                # Look for any variation in the CSV
                for variation in who_variations:
                    for keyword in qa_dict:
                        if variation.lower() in keyword or keyword in variation.lower():
                            print(f"Found matching variation: {keyword}")
                            return qa_dict[keyword]
                break
    
    # Direct match
    if query in qa_dict:
        print(f"Found direct match for: {query}")
        return qa_dict[query]
    
    # Special case for "who are you" in all languages
    if language == "marathi":
        who_patterns = [
            r'\b(tumi|tumhi|tyoumi|tumhee)\s+(kon|kona|kaun)',
            r'\b(tu|tuu)\s+(kon|kona|kaun)',
            r'तुम्ही कोण', r'तू कोण'
        ]
    elif language == "hindi":
        who_patterns = [
            r'\b(aap|aapko)\s+(kon|kaun)',
            r'\b(tum|tumko)\s+(kon|kaun)',
            r'आप कौन', r'तुम कौन'
        ]
    else:
        who_patterns = [r'who\s+are\s+you']
    
    for pattern in who_patterns:
        if re.search(pattern, query):
            print(f"Found '{language}' who are you type question")
            for key, value in qa_dict.items():
                if any(phrase in key.lower() for phrase in ["who are you", "तू कोण आहेस", "तुम्ही कोण आहात", "आप कौन हैं", "तुम कौन हो"]):
                    print(f"Found matching key: {key}")
                    return value
            break
    
    # Partial match
    for keyword in qa_dict:
        if keyword in query:
            print(f"Found partial match: {keyword}")
            return qa_dict[keyword]
    
    # Fuzzy match
    close_matches = difflib.get_close_matches(query, qa_dict.keys(), n=1, cutoff=0.7)
    if close_matches:
        print(f"Found fuzzy match: {close_matches[0]}")
        return qa_dict[close_matches[0]]
    
    # Word-by-word fuzzy match
    for word in query.split():
        close_matches = difflib.get_close_matches(word, qa_dict.keys(), n=1, cutoff=0.8)
        if close_matches:
            print(f"Found word match: {close_matches[0]}")
            return qa_dict[close_matches[0]]
    
    print("No match found, returning fallback")
    return fallback_response

def apply_tone(answer, tone, language="english"):
    tone = (tone or "").strip().lower()
    if language == "marathi":
        if tone == "royal":
            return f"माझ्या मावळ्या, {answer}"
        elif tone == "friendly":
            return f"माझ्या मित्रा, हे जाणून घे. {answer}"
        elif tone == "serious":
            return f"खबरदार: {answer}"
    elif language == "hindi":
        if tone == "royal":
            return f"मेरे प्रिय प्रजाजन, {answer}"
        elif tone == "friendly":
            return f"मेरे मित्र, जानिए। {answer}"
        elif tone == "serious":
            return f"सावधान: {answer}"
    else:  # English
        if tone == "royal":
            return f"My dear subject, {answer}"
        elif tone == "friendly":
            return f"My friend, {answer}"
        elif tone == "serious":
            return f"Listen carefully: {answer}"
    
    return answer

def generate_tts_audio(text, language="english"):
    """Generate audio using Google Cloud TTS based on language"""
    try:
        if not text.strip():
            return None
        
        client = texttospeech.TextToSpeechClient()
        
        # Configure voice based on language - FIXED Hindi voice
        if language == "marathi":
            language_code = "mr-IN"
            voice_name = "mr-IN-Chirp3-HD-Schedar"
        elif language == "hindi":
            language_code = "hi-IN"
            voice_name = "hi-IN-Chirp3-HD-Charon"  # FIXED: Correct Hindi voice name
        else:
            language_code = "en-IN"
            voice_name = "en-IN-Chirp3-HD-Charon"  # Male English voice
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
            name=voice_name
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )
        
        os.makedirs(AUDIO_FOLDER, exist_ok=True)
        filename = f"tts_{language}_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_FOLDER, filename)
        
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
        
        print(f"Generated TTS audio for {language}: {voice_name}")
        return f"/audio/{filename}"
        
    except Exception as e:
        print(f"TTS generation failed: {e}")
        return None

def contains_phrase(phrases, text):
    for phrase in phrases:
        if len(phrase.split()) == 1:
            if re.search(r'\b' + re.escape(phrase) + r'\b', text):
                return True
        else:
            if phrase in text:
                return True
    return False

yes_responses = [
    "yes", "yeah", "yep", "sure", "of course", "certainly", "yup", "please do", "go ahead",
    "होय", "हो",  # Marathi
    "हाँ", "जी", "हाँ जी", "बिल्कुल"  # Hindi
]

no_responses = [
    "no", "nope", "nah", "not now", "don't", "do not", "never", "stop",
    "नाही", "नको",  # Marathi
    "नहीं", "न", "मत", "रोको"  # Hindi
]

@app.route('/chat', methods=['POST'])
def chat():
    global last_followup_context
    
    data = request.get_json()
    original_input = data.get('message', '').strip()
    
    # First detect language on the raw input (BEFORE preprocessing)
    detected_language = detect_language(original_input)
    print(f"Original user input: {original_input}")
    print(f"Detected language: {detected_language}")
    
    # Then preprocess based on detected language
    user_input = preprocess_input(original_input, detected_language)
    print(f"Preprocessed input: {user_input}")
    
    answer_text = ""
    audio_url = ""
    
    if last_followup_context["has_followup"]:
        if contains_phrase(yes_responses, user_input.lower()):
            answer_text = last_followup_context["Answer_if_Yes"]
            detected_language = last_followup_context.get("language", detected_language)
            last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": detected_language}
        elif contains_phrase(no_responses, user_input.lower()):
            if detected_language == "marathi":
                answer_text = "जसं तुम्हाला वाटतं. आणखी प्रश्न असतील तर विचारा."
            elif detected_language == "hindi":
                answer_text = "जैसा आप चाहते हैं। यदि आपके और प्रश्न हैं तो पूछिए।"
            else:
                answer_text = "As you wish. If you have more questions, feel free to ask."
            last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": detected_language}
        else:
            # Continue with normal processing
            response = get_response(user_input, detected_language)
            answer = response["answer"]
            tone = response.get("tone", "")
            followup = response.get("followup", "")
            answer_if_yes = response.get("Answer_if_Yes", "")
            response_language = response.get("language", detected_language)
            
            if not answer.strip():
                if response_language == "marathi":
                    answer = "माफ करा, मला त्याचे उत्तर सापडले नाही."
                elif response_language == "hindi":
                    answer = "क्षमा करें, मुझे इसका उत्तर नहीं मिला।"
                else:
                    answer = "Sorry, I couldn't find an answer for that."
            
            answer_text = apply_tone(answer, tone, response_language)
            
            if followup:
                answer_text += f" {followup}"
                last_followup_context = {"has_followup": True, "Answer_if_Yes": answer_if_yes, "language": response_language}
            else:
                last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": response_language}
    else:
        # Normal processing
        response = get_response(user_input, detected_language)
        print(f"Got response from CSV: {response}")
        
        answer = response["answer"]
        tone = response.get("tone", "")
        followup = response.get("followup", "")
        answer_if_yes = response.get("Answer_if_Yes", "")
        response_language = response.get("language", detected_language)
        
        if not answer.strip():
            if response_language == "marathi":
                answer = "माफ करा, मला त्याचे उत्तर सापडले नाही."
            elif response_language == "hindi":
                answer = "क्षमा करें, मुझे इसका उत्तर नहीं मिला।"
            else:
                answer = "Sorry, I couldn't find an answer for that."
        
        answer_text = apply_tone(answer, tone, response_language)
        
        if followup:
            answer_text += f" {followup}"
            last_followup_context = {"has_followup": True, "Answer_if_Yes": answer_if_yes, "language": response_language}
        else:
            last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": response_language}
    
    # Generate TTS audio based on the response language
    final_language = last_followup_context.get("language", detected_language)
    audio_url = generate_tts_audio(answer_text, final_language)
    
    return jsonify({
        "response": answer_text, 
        "audio_url": audio_url or "", 
        "language": final_language
    })

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route('/tts', methods=['POST'])
def tts():
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or "").strip()
        
        if not text:
            return jsonify({"error": "Missing 'text' in request body."}), 400
        
        # Detect language or use provided language
        language = data.get("language", detect_language(text))
        
        audio_url = generate_tts_audio(text, language)
        
        if audio_url:
            return jsonify({
                "audio_url": audio_url,
                "message": f"TTS generated successfully for {language}.",
                "language": language
            }), 200
        else:
            return jsonify({"error": "TTS generation failed"}), 500
            
    except Exception as e:
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

if __name__ == "__main__":
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    app.run(debug=True)
