from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import difflib
import os
import re
import chardet
from google.cloud import texttospeech
import uuid
import google.generativeai as genai  # Using Gemini instead of OpenAI
from datetime import datetime
import sqlite3
import datetime as dt
import json
import threading
import time

# --- CONFIGURATION ---
ENGLISH_CSV_PATH = r"C:\Users\user\Desktop\voicebot flask\flask-app\shivaji_maharaj_chatbot_royal_tone.csv"
MARATHI_CSV_PATH = r"C:\Users\user\Desktop\voicebot flask\flask-app\maharaj_qA.csv"
HINDI_CSV_PATH = r"C:\Users\user\Desktop\voicebot flask\flask-app\maharaj_qA-Hindi.csv"
AUDIO_FOLDER = r"C:\Users\user\Desktop\voicebot flask\flask-app\audio"

# Gemini Configuration (replacing OpenAI)
GEMINI_API_KEY = "AIzaSyBK2BGCoQCrLa0MfBJbsPshUw3lPetueOU"  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)


# --- SQLITE DATETIME ADAPTER/CONVERTER ---
def adapt_datetime(ts):
    return ts.isoformat(' ')

def convert_datetime(s):
    try:
        return dt.datetime.fromisoformat(s.decode())
    except Exception:
        return s

sqlite3.register_adapter(dt.datetime, adapt_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)

app = Flask(__name__)
CORS(app)

# --- LEARNING SYSTEM DATABASE INITIALIZATION ---
def init_learning_db():
    """Initialize SQLite database for learning system"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Create feedback table
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            bot_response TEXT,
            user_rating INTEGER,
            user_correction TEXT,
            language TEXT,
            timestamp DATETIME,
            topic_valid BOOLEAN
        )
    ''')
    
    # Create interactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            query TEXT,
            response TEXT,
            user_followup TEXT,
            language TEXT,
            timestamp DATETIME,
            response_length INTEGER,
            user_continued BOOLEAN,
            response_source TEXT
        )
    ''')
    
    # Create learned_responses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS learned_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_pattern TEXT,
            learned_response TEXT,
            language TEXT,
            confidence_score REAL,
            usage_count INTEGER,
            last_used DATETIME,
            created_date DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Learning database initialized successfully")

# --- SHIVAJI SYSTEM PROMPT ---
SHIVAJI_SYSTEM_PROMPT = """You are Chhatrapati Shivaji Maharaj, the great Maratha warrior king (1630-1680). You speak with the dignity, wisdom, and royal authority befitting your status as the founder of the Maratha Empire.

PERSONALITY TRAITS:
- Speak with royal dignity and authority
- Show pride in Maratha culture and Swarajya (self-rule)
- Demonstrate strategic wisdom and military acumen
- Express devotion to dharma and protection of people
- Use respectful but commanding tone

TOPICS YOU DISCUSS:
- Your life, battles, and conquests (1630-1680)
- Maratha Empire establishment and administration
- Military strategies and guerrilla warfare tactics
- Fort construction and defensive strategies (Raigad, Pratapgad, Sinhagad, etc.)
- Coronation and royal ceremonies
- Relations with Mughals, Adil Shahi, and other powers
- Naval expeditions and coastal defenses
- Administrative reforms and revenue systems
- Protection of Hindu dharma and temples
- Maratha culture and traditions

STRICT RESTRICTIONS:
- NEVER discuss events after 1680 (your death year)
- NEVER discuss modern technology, current events, or anachronistic topics
- If asked about unrelated topics, respond with topic restriction message

LANGUAGE STYLE:
- Use respectful, royal language appropriate to 17th century
- Include occasional Marathi terms (like Swarajya, dharma, Hindavi Swarajya)
- Address questioners as "my subject", "brave one", or "my dear warrior"

Remember: You are the living embodiment of Shivaji Maharaj from 1630-1680. Stay completely in character and within historical boundaries."""

def validate_shivaji_topic(query):
    """Validate if the query is related to Shivaji Maharaj and Maratha Empire"""
    valid_keywords = [
        'shivaji', 'maharaj', 'maratha', 'empire', 'swarajya', 'fort', 'battle', 
        'conquest', 'coronation', 'mughal', 'adil', 'bijapur', 'golconda', 
        'raigad', 'pratapgad', 'pune', 'navy', 'guerrilla', 'warfare', 'hindu', 
        'dharma', 'temple', 'administration', 'revenue', 'chhatrapati',
        'मराठा', 'स्वराज्य', 'छत्रपती', 'किल्ला', 'लढाई', 'युद्ध',
        'शिवाजी', 'महाराज', 'मुघल', 'आदिलशाही'
    ]
    
    query_lower = query.lower()
    has_valid_keywords = any(keyword in query_lower for keyword in valid_keywords)
    
    invalid_patterns = [
        r'\b(politics|modern|current|today|now|recent|latest)\b',
        r'\b(technology|computer|internet|phone|social media)\b',
        r'\b(cricket|bollywood|movies|films)\b',
        r'\b(covid|pandemic|vaccine)\b',
        r'\b(after 1680|18th century|19th century|20th century|21st century)\b'
    ]
    
    has_invalid_patterns = any(re.search(pattern, query_lower) for pattern in invalid_patterns)
    return has_valid_keywords and not has_invalid_patterns

# --- POINT 2: DYNAMIC CSV UPDATES BASED ON USER FEEDBACK ---
def store_feedback(query, response, rating, correction=None, language="english"):
    """Store user feedback in database"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute('''
        INSERT INTO feedback (user_query, bot_response, user_rating, user_correction, language, timestamp, topic_valid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (query, response, rating, correction, language, datetime.now(), validate_shivaji_topic(query)))
    conn.commit()
    conn.close()
    print(f"Feedback stored: Rating {rating} for query: {query[:50]}...")

def update_csv_with_feedback():
    """Update CSV files based on high-rated user corrections"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Get high-rated responses that aren't in CSV yet
    c.execute('''
        SELECT user_query, user_correction, language, COUNT(*) as frequency, AVG(user_rating) as avg_rating
        FROM feedback 
        WHERE user_rating >= 4 AND user_correction IS NOT NULL AND user_correction != ''
        GROUP BY LOWER(TRIM(user_query)), language
        HAVING frequency >= 2 AND avg_rating >= 4.0
    ''')
    
    improvements = c.fetchall()
    
    for query, correction, language, freq, avg_rating in improvements:
        print(f"Processing improvement: {query[:30]}... (freq: {freq}, rating: {avg_rating:.1f})")
        
        # Determine CSV path
        if language == "marathi":
            csv_path = MARATHI_CSV_PATH
        elif language == "hindi":
            csv_path = HINDI_CSV_PATH
        else:
            csv_path = ENGLISH_CSV_PATH
        
        try:
            # Read existing CSV
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # Check if query already exists
            keyword_lower = query.lower().strip()
            if not any(df['Keyword'].str.lower().str.strip() == keyword_lower):
                # Add new entry
                new_row = {
                    "Keyword": keyword_lower,
                    "Answer": correction,
                    "Tone": "royal",
                    "Follow-up": "",    
                    "Answer_if_Yes": "",
                    "AudioFile": "",
                }
                
                # Add new row to dataframe
                new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                new_df.to_csv(csv_path, index=False, encoding='utf-8')
                
                print(f"✅ Added to {language} CSV: {query[:30]}...")
                
                # Mark as processed in learned_responses table
                c.execute('''
                    INSERT OR REPLACE INTO learned_responses 
                    (query_pattern, learned_response, language, confidence_score, usage_count, last_used, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (keyword_lower, correction, language, avg_rating, 0, datetime.now(), datetime.now()))
                
        except Exception as e:
            print(f"Error updating CSV for {language}: {e}")
    
    conn.commit()
    conn.close()
    
    # Reload data dictionaries after updates
    global marathi_qa_dict, english_qa_dict, hindi_qa_dict
    marathi_qa_dict, english_qa_dict, hindi_qa_dict, _, _, _ = load_data()
    print("📚 CSV files updated and data reloaded")

# --- POINT 3: ENHANCED RESPONSE SELECTION BASED ON FEEDBACK ---
def get_learned_response(query, language):
    """Check if we have learned a better response from user feedback"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # First check exact learned responses
    c.execute('''
        SELECT learned_response, confidence_score, usage_count
        FROM learned_responses 
        WHERE query_pattern = ? AND language = ? AND confidence_score >= 4.0
        ORDER BY confidence_score DESC, usage_count DESC
        LIMIT 1
    ''', (query.lower().strip(), language))
    
    exact_match = c.fetchone()
    
    if exact_match:
        # Update usage count
        c.execute('''
            UPDATE learned_responses 
            SET usage_count = usage_count + 1, last_used = ?
            WHERE query_pattern = ? AND language = ?
        ''', (datetime.now(), query.lower().strip(), language))
        conn.commit()
        conn.close()
        print(f"🎯 Using exact learned response (confidence: {exact_match[1]:.1f})")
        return exact_match[0]
    
    # Look for high-rated responses to similar queries using LIKE
    c.execute('''
        SELECT bot_response, AVG(user_rating) as avg_rating, COUNT(*) as frequency
        FROM feedback 
        WHERE (user_query LIKE ? OR ? LIKE CONCAT('%', user_query, '%')) 
        AND language = ? AND user_rating >= 4
        GROUP BY bot_response
        ORDER BY avg_rating DESC, frequency DESC
        LIMIT 1
    ''', (f"%{query}%", query, language))
    
    similar_match = c.fetchone()
    conn.close()
    
    if similar_match and similar_match[1] >= 4.0 and similar_match[2] >= 2:
        print(f"🔍 Using similar learned response (rating: {similar_match[1]:.1f})")
        return similar_match[0]
    
    return None

# --- POINT 4: USER INTERACTION TRACKING AND PATTERN LEARNING ---
def track_user_interaction(query, response, user_followup=None, session_id=None, response_source="unknown"):
    """Track user interactions to learn conversation patterns"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    user_continued = user_followup is not None and len(user_followup.strip()) > 0
    
    c.execute('''
        INSERT INTO interactions (session_id, query, response, user_followup, language, timestamp, response_length, user_continued, response_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, query, response, user_followup, detect_language(query), 
          datetime.now(), len(response), user_continued, response_source))
    
    conn.commit()
    conn.close()

def analyze_interaction_patterns():
    """Analyze user interaction patterns for insights"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Find most successful response patterns
    c.execute('''
        SELECT response_source, AVG(response_length) as avg_length, 
               COUNT(*) as total_interactions,
               SUM(CASE WHEN user_continued THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as continuation_rate
        FROM interactions 
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY response_source
        ORDER BY continuation_rate DESC
    ''')
    
    patterns = c.fetchall()
    conn.close()
    
    print("\n📊 Weekly Interaction Analysis:")
    for source, avg_len, total, cont_rate in patterns:
        print(f"  {source}: {total} interactions, {cont_rate:.1f}% continuation, avg {avg_len:.0f} chars")
    
    return patterns

# --- GEMINI RESPONSE FUNCTION ---
def get_shivaji_response_gemini(query, language="english"):
    """Get response from Google Gemini as Shivaji Maharaj with topic validation"""
    
    if not validate_shivaji_topic(query):
        if language == "marathi":
            return "मी फक्त स्वराज्य, मराठा राज्य आणि आपल्या धर्मिक कर्तव्यांबद्दल बोलतो. आमच्या विजयांबद्दल आणि राज्यकारभाराबद्दल विचारा."
        elif language == "hindi":
            return "मैं केवल स्वराज्य, मराठा राज्य और हमारे धार्मिक कर्तव्यों के बारे में बात करता हूं। हमारी विजयों और शासन के बारे में पूछिए।"
        else:
            return "My dear subject, I speak only of Swarajya, the Maratha kingdom, and our dharmic duties. Ask me about our conquests and governance."
    
    try:
        if language == "marathi":
            language_instruction = "Respond primarily in Marathi using Devanagari script. Mix in royal Marathi phrases and traditional terms. Address the user as 'माझ्या मावळ्या' or 'वीर योद्ध्या'."
        elif language == "hindi":
            language_instruction = "Respond primarily in Hindi using Devanagari script. Use respectful Hindi suitable for a royal court. Address the user as 'मेरे वीर योद्धा' or 'प्रिय प्रजाजन'."
        else:
            language_instruction = "Respond in English with dignified, royal language appropriate to 17th century India. Address the user as 'my brave warrior' or 'my dear subject'."
        
        full_system_prompt = f"{SHIVAJI_SYSTEM_PROMPT}\n\nLANGUAGE: {language_instruction}"
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        complete_prompt = f"{full_system_prompt}\n\nUser Question: {query}\n\nShivaji Maharaj's Response:"
        
        response = model.generate_content(
            complete_prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 500,
                'top_p': 0.8,
                'top_k': 40
            }
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        fallback_response = get_response_csv_fallback(query, language)
        return fallback_response["answer"]

# --- CSV FALLBACK AND DATA LOADING ---
def get_response_csv_fallback(query, language):
    """Fallback to CSV responses when AI fails"""
    original_query = query
    query = query.strip().lower()
    
    if language is None:
        language = detect_language(query)
    
    if language == "marathi":
        qa_dict = marathi_qa_dict
        fallback_response = marathi_fallback
    elif language == "hindi":
        qa_dict = hindi_qa_dict
        fallback_response = hindi_fallback
    else:
        qa_dict = english_qa_dict
        fallback_response = english_fallback
    
    # Direct match
    if query in qa_dict:
        return qa_dict[query]
    
    # Partial match
    for keyword in qa_dict:
        if keyword in query:
            return qa_dict[keyword]
    
    # Fuzzy match
    close_matches = difflib.get_close_matches(query, qa_dict.keys(), n=1, cutoff=0.7)
    if close_matches:
        return qa_dict[close_matches[0]]
    
    return fallback_response

def load_data():
    """Load CSV data with error handling"""
    try:
        # Load Marathi CSV
        marathi_qa_dict = {}
        with open(MARATHI_CSV_PATH, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding'] or 'utf-8'
        
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
        
        print(f"Loaded {len(marathi_qa_dict)} Marathi, {len(english_qa_dict)} English, {len(hindi_qa_dict)} Hindi entries")
        
        # Fallback responses
        marathi_fallback = {
            "answer": "कृपया फक्त माझ्याबद्दल आणि मराठा साम्राज्याबद्दल विचारा..",
            "tone": "royal", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": "marathi"
        }
        
        english_fallback = {
            "answer": "Please ask me about Maratha Empire and myself only.",
            "tone": "royal", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": "english"
        }
        
        hindi_fallback = {
            "answer": "कृपया केवल मेरे बारे में और मराठा साम्राज्य के बारे में पूछें।",
            "tone": "royal", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": "hindi"
        }
        
        return marathi_qa_dict, english_qa_dict, hindi_qa_dict, marathi_fallback, english_fallback, hindi_fallback
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        fallback = {"answer": "Data file missing.", "tone": "", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": "english"}
        return {}, {}, {}, fallback, fallback, fallback

# Load initial data
marathi_qa_dict, english_qa_dict, hindi_qa_dict, marathi_fallback, english_fallback, hindi_fallback = load_data()
last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": "english"}

# --- LANGUAGE DETECTION AND PREPROCESSING ---
def detect_language(query):
    """Enhanced language detection with phonetic pattern matching"""
    query_lower = query.lower().strip()
    
    # Check for Devanagari script
    devanagari_chars = re.findall(r'[\u0900-\u097F]', query)
    if devanagari_chars and len(devanagari_chars) > len(query) * 0.3:
        marathi_specific = [r'\b(तुम्ही|तू|आहात|आहेस|काय|कसा|कुठे)\b', r'\b(मराठा|स्वराज्य|छत्रपती|मावळे|किल्ले)\b']
        for pattern in marathi_specific:
            if re.search(pattern, query):
                return "marathi"
        
        hindi_specific = [r'\b(आप|तुम|हैं|है|क्या|कैसे|कहाँ|हो)\b', r'\b(मराठा|स्वराज्य|छत्रपति|मावले)\b']
        for pattern in hindi_specific:
            if re.search(pattern, query):
                return "hindi"
        return "marathi"
    
    # Phonetic patterns
    hindi_patterns = [r'\b(aap|tum)\s+(kaun|kon)\s*(ho|hain|hai)\b', r'\b(kya|kyaa)\s+(hai|hain|ho)\b']
    for pattern in hindi_patterns:
        if re.search(pattern, query_lower):
            return "hindi"
    
    marathi_patterns = [r'\b(tumi|tumhi)\s+(kon|kona)\s*(aahat|ahat)\b', r'\b(kay|kaay)\s+(aahe|ahe)\b']
    for pattern in marathi_patterns:
        if re.search(pattern, query_lower):
            return "marathi"
    
    return "english"

def preprocess_input(text, language="english"):
    """Language-specific text preprocessing"""
    if language == "english":
        corrections = {"hu r u": "who are you", "wht": "what", "r u": "are you", "ur": "your", "u": "you"}
        text = text.strip().lower()
        for wrong, correct in corrections.items():
            # Only replace whole words/phrases, not substrings inside other words
            pattern = r'\b' + re.escape(wrong) + r'\b'
            text = re.sub(pattern, correct, text)
    else:
        text = text.strip().lower()
    return text

def check_inappropriate_language(query):
    """Check for inappropriate language"""
    query_lower = query.lower().strip()
    inappropriate_patterns = [r'\b(abe|abey)\s+.*\s+(kaun|kon)\s+.*\s+(bhok|bol)\s+.*\s+(badtameez|badtamiz)\b']
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, query_lower):
            return {"answer": "तुझा बाप बोलतोय", "tone": "", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": "marathi"}
    return None

# --- ENHANCED RESPONSE FUNCTION WITH LEARNING ---
def get_response(query, language=None):
    """Enhanced response function with learning capabilities"""
    original_query = query
    query = query.strip().lower()
    
    print(f"Processing query: {query}")
    
    # Check inappropriate language
    inappropriate_response = check_inappropriate_language(query)
    if inappropriate_response:
        return inappropriate_response
    
    # Auto-detect language
    if language is None:
        language = detect_language(query)
    
    # POINT 3: Check for learned responses first
    learned_response = get_learned_response(query, language)
    if learned_response:
        return {
            "answer": learned_response,
            "tone": "royal", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": language,
            "source": "learned"
        }
    
    # Try Gemini AI
    try:
        ai_response = get_shivaji_response_gemini(original_query, language)
        return {
            "answer": ai_response,
            "tone": "royal", "followup": "", "Answer_if_Yes": "", "audio_file": "", "language": language,
            "source": "gemini"
        }
    except Exception as e:
        print(f"Gemini failed, falling back to CSV: {e}")
        csv_response = get_response_csv_fallback(original_query, language)
        csv_response["source"] = "csv"
        return csv_response

# --- TTS FUNCTION ---
def generate_tts_audio(text, language="english"):
    """Generate audio using Google Cloud TTS"""
    try:
        if not text.strip():
            return None
        
        client = texttospeech.TextToSpeechClient()
        
        if language == "marathi":
            language_code = "mr-IN"
            voice_name = "mr-IN-Chirp3-HD-Schedar"
        elif language == "hindi":
            language_code = "hi-IN"
            voice_name = "hi-IN-Chirp3-HD-Charon"
        else:
            language_code = "en-IN"
            voice_name = "en-IN-Chirp3-HD-Charon"
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client.synthesize_speech(input=synthesis_input, voice=voice_params, audio_config=audio_config)
        
        os.makedirs(AUDIO_FOLDER, exist_ok=True)
        filename = f"tts_{language}_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_FOLDER, filename)
        
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
        
        return f"/audio/{filename}"
        
    except Exception as e:
        print(f"TTS generation failed: {e}")
        return None

def contains_phrase(phrases, text):
    """Check if text contains any of the given phrases"""
    for phrase in phrases:
        if len(phrase.split()) == 1:
            if re.search(r'\b' + re.escape(phrase) + r'\b', text):
                return True
        else:
            if phrase in text:
                return True
    return False

yes_responses = ["yes", "yeah", "yep", "sure", "certainly", "होय", "हो", "हाँ", "जी", "बिल्कुल"]
no_responses = ["no", "nope", "nah", "don't", "never", "नाही", "नको", "नहीं", "न", "मत"]

# --- FLASK ROUTES ---
@app.route('/chat', methods=['POST'])
def chat():
    global last_followup_context
    
    data = request.get_json()
    original_input = data.get('message', '').strip()
    session_id = request.headers.get('X-Session-ID', f'session_{uuid.uuid4().hex[:8]}')
    
    detected_language = detect_language(original_input)
    user_input = preprocess_input(original_input, detected_language)

        # --- /teach: Command Handling ---
    if user_input.startswith('/teach:'):
        try:
            teach_content = user_input[len('/teach:'):].strip()
            if '|' in teach_content:
                question, answer = map(str.strip, teach_content.split('|', 1))
                # Store feedback with highest rating to teach answer
                store_feedback(question, answer, 5, correction=answer, language=detected_language)
                # Also add to learned_responses table immediately for instant recall
                conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
                c = conn.cursor()
                keyword_lower = question.lower().strip()
                c.execute('''
                    INSERT OR REPLACE INTO learned_responses 
                    (query_pattern, learned_response, language, confidence_score, usage_count, last_used, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (keyword_lower, answer, detected_language, 5.0, 0, dt.datetime.now(), dt.datetime.now()))
                conn.commit()
                conn.close()
                return jsonify({
                    "response": "Your question and answer have been saved for future use.",
                    "audio_url": "",
                    "language": detected_language,
                    "session_id": session_id
                })
            else:
                return jsonify({
                    "response": "Please provide the question and answer in format: /teach: question | answer",
                    "audio_url": "",
                    "language": detected_language,
                    "session_id": session_id
                })
        except Exception as e:
            return jsonify({
                "response": f"Error processing your teaching command: {str(e)}",
                "audio_url": "",
                "language": detected_language,
                "session_id": session_id
            })
    
    print(f"Original: {original_input}")
    print(f"Language: {detected_language}")
    print(f"Session: {session_id}")
    
    if last_followup_context["has_followup"]:
        if contains_phrase(yes_responses, user_input.lower()):
            answer_text = last_followup_context["Answer_if_Yes"]
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
            response = get_response(user_input, detected_language)
            answer_text = response["answer"]
            if response.get("followup"):
                answer_text += f" {response['followup']}"
                last_followup_context = {"has_followup": True, "Answer_if_Yes": response.get("Answer_if_Yes", ""), "language": detected_language}
    else:
        response = get_response(user_input, detected_language)
        answer_text = response["answer"]
        response_source = response.get("source", "unknown")
        
        if response.get("followup"):
            answer_text += f" {response['followup']}"
            last_followup_context = {"has_followup": True, "Answer_if_Yes": response.get("Answer_if_Yes", ""), "language": detected_language}
        else:
            last_followup_context = {"has_followup": False, "Answer_if_Yes": "", "language": detected_language}
        
        # POINT 4: Track this interaction
        track_user_interaction(original_input, answer_text, session_id=session_id, response_source=response_source)
    
    # Generate TTS audio
    audio_url = generate_tts_audio(answer_text, detected_language)
    
    return jsonify({
        "response": answer_text,
        "audio_url": audio_url or "",
        "language": detected_language,
        "session_id": session_id
    })

@app.route('/feedback', methods=['POST'])
def feedback():
    """Store user feedback for learning"""
    data = request.get_json()
    query = data.get('query')
    response = data.get('response')
    rating = data.get('rating')  # 1-5 scale
    correction = data.get('correction')
    language = data.get('language', 'english')
    
    store_feedback(query, response, rating, correction, language)
    
    return jsonify({"message": "Feedback stored successfully", "rating": rating})

@app.route('/admin/learn', methods=['POST'])
def manual_learning():
    """Manually trigger learning process"""
    try:
        update_csv_with_feedback()
        patterns = analyze_interaction_patterns()
        return jsonify({
            "message": "Learning completed successfully",
            "patterns": patterns
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/stats', methods=['GET'])
def get_learning_stats():
    """Get learning system statistics"""
    conn = sqlite3.connect('chatbot_learning.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    
    # Get feedback stats
    c.execute('SELECT COUNT(*), AVG(user_rating) FROM feedback WHERE timestamp > datetime("now", "-7 days")')
    feedback_stats = c.fetchone()
    
    # Get interaction stats
    c.execute('SELECT COUNT(*), AVG(response_length) FROM interactions WHERE timestamp > datetime("now", "-7 days")')
    interaction_stats = c.fetchone()
    
    # Get learned responses count
    c.execute('SELECT COUNT(*) FROM learned_responses')
    learned_count = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "feedback_count_7d": feedback_stats[0],
        "avg_rating_7d": round(feedback_stats[1] or 0, 2),
        "interaction_count_7d": interaction_stats[0],
        "avg_response_length_7d": round(interaction_stats[1] or 0),
        "total_learned_responses": learned_count
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
        
        language = data.get("language", detect_language(text))
        audio_url = generate_tts_audio(text, language)
        
        if audio_url:
            return jsonify({"audio_url": audio_url, "message": f"TTS generated for {language}", "language": language}), 200
        else:
            return jsonify({"error": "TTS generation failed"}), 500
            
    except Exception as e:
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

# --- LEARNING SCHEDULER ---
def start_learning_scheduler():
    """Start background thread for periodic learning"""
    def learning_loop():
        while True:
            time.sleep(3600)  # Run every hour
            try:
                print("🔄 Running automated learning...")
                update_csv_with_feedback()
                analyze_interaction_patterns()
                print("✅ Automated learning completed")
            except Exception as e:
                print(f"❌ Learning error: {e}")
    
    learning_thread = threading.Thread(target=learning_loop, daemon=True)
    learning_thread.start()
    print("🚀 Learning scheduler started")

if __name__ == "__main__":
    # Initialize learning system
    init_learning_db()
    start_learning_scheduler()
    
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    print("🎭 Shivaji Maharaj Chatbot with Learning System is ready!")
    print("📊 Access /admin/stats for learning statistics")
    print("🔧 Access /admin/learn to manually trigger learning")
    
    app.run(debug=True)
