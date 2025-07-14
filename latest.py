import time
import streamlit as st
import streamlit.components.v1 as components
import json
import re
from typing import List, Dict, Any
import requests
from PIL import Image
import base64
import io
import tempfile
import os
from groq import Groq
import pyaudio
import wave

# Behavioral-Based Authentication Class
class BehavioralAuth:
    def __init__(self):
        self.session_start = time.time()
        self.interactions = []
        self.trust_score = 0  # Base trust score
        
    def log_interaction(self, action: str, metadata: Dict = None):
        """Log user interaction for behavioral analysis"""
        interaction = {
            'timestamp': time.time(),
            'action': action,
            'metadata': metadata or {}
        }
        self.interactions.append(interaction)
        self.update_trust_score()
    
    def update_trust_score(self):
        """Calculate trust score based on behavioral patterns"""
        score = 0  # Base score
        
        # Time spent on site (up to 30 points)
        session_time = time.time() - self.session_start
        time_bonus = min(15, int(session_time / 30))  # 1 point per 30 seconds
        score += time_bonus
        
        # Interaction variety (5 points per unique action type)
        unique_actions = len(set(i['action'] for i in self.interactions))
        score += unique_actions * 5
        
        # Search behavior (10 points for natural language search)
        if any(i['action'] == 'search' for i in self.interactions):
            score += 10
        
        # Voice input usage (20 points - hard for bots to fake)
        if any(i['action'].startswith('voice') for i in self.interactions):
            score += 20
        
        # Penalize rapid-fire actions (bot-like behavior)
        if len(self.interactions) > 1:
            recent_interactions = self.interactions[-5:]
            if len(recent_interactions) >= 3:
                time_diffs = [recent_interactions[i]['timestamp'] - recent_interactions[i-1]['timestamp'] 
                             for i in range(1, len(recent_interactions))]
                if all(diff < 0.5 for diff in time_diffs):  # All actions within 0.5 seconds
                    score -= 20
        
        self.trust_score = min(100, max(0, score))
    
    def is_human(self) -> bool:
        """Determine if user is likely human based on trust score"""
        return self.trust_score >= 80
api_key = os.getenv('api_key')
# Initialize Groq client
# Make sure to set your GROQ_API_KEY in Streamlit secrets or environment variable
groq_client = Groq(api_key=api_key)

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Mock product database - in a real app, this would be a proper database
MOCK_PRODUCTS = {
    "camping_cot": {
        "name": "Portable Camping Cot",
        "description": "Lightweight foldable sleeping cot for camping",
        "price": "$89.99",
        "rating": 4.3,
        "availability": "In Stock",
        "image_url": "https://via.placeholder.com/300x200?text=Camping+Cot",
        "keywords": ["foldable", "sleep", "camping", "cot", "portable", "bed", "outdoor"]
    },
    "water_purifier": {
        "name": "Portable Water Purifier Bottle",
        "description": "Water filter bottle for hiking and camping",
        "price": "$34.99",
        "rating": 4.7,
        "availability": "In Stock",
        "image_url": "https://via.placeholder.com/300x200?text=Water+Filter",
        "keywords": ["water", "filter", "purifier", "bottle", "hiking", "camping", "portable", "drink"]
    },
    "headlamp": {
        "name": "LED Headlamp",
        "description": "Rechargeable LED headlamp for outdoor activities",
        "price": "$24.99",
        "rating": 4.5,
        "availability": "In Stock",
        "image_url": "https://via.placeholder.com/300x200?text=LED+Headlamp",
        "keywords": ["light", "head", "camping", "hands-free", "led", "flashlight", "outdoor"]
    },
    "camping_chair": {
        "name": "Folding Camping Chair",
        "description": "Lightweight portable chair for outdoor use",
        "price": "$45.99",
        "rating": 4.2,
        "availability": "In Stock",
        "image_url": "https://via.placeholder.com/300x200?text=Camping+Chair",
        "keywords": ["chair", "folding", "portable", "camping", "outdoor", "seat", "lightweight"]
    },
    "tent": {
        "name": "4-Person Camping Tent",
        "description": "Waterproof dome tent for family camping",
        "price": "$129.99",
        "rating": 4.6,
        "availability": "In Stock",
        "image_url": "https://via.placeholder.com/300x200?text=Camping+Tent",
        "keywords": ["tent", "camping", "shelter", "waterproof", "family", "dome", "outdoor"]
    },
    "sleeping_bag": {
        "name": "Mummy Sleeping Bag",
        "description": "Warm sleeping bag for cold weather camping",
        "price": "$79.99",
        "rating": 4.4,
        "availability": "In Stock",
        "image_url": "https://via.placeholder.com/300x200?text=Sleeping+Bag",
        "keywords": ["sleeping", "bag", "warm", "camping", "cold", "weather", "mummy", "outdoor"]
    }
}

def analyze_text_description(description: str) -> List[str]:
    """Extract keywords from text description using simple NLP"""
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', description.lower())
    
    # Common words to ignore
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'need', 'want', 'looking', 'that', 'thing', 'stuff', 'item'}
    
    # Extract words
    words = [word for word in text.split() if word not in stop_words and len(word) > 2]
    
    # Add some synonym mapping for better matching
    synonyms = {
        'foldable': ['fold', 'collapsible', 'portable'],
        'bottle': ['container', 'flask'],
        'light': ['lamp', 'flashlight', 'torch'],
        'bed': ['cot', 'sleeping'],
        'chair': ['seat'],
        'water': ['drink', 'liquid'],
        'filter': ['purifier', 'clean']
    }
    
    # Expand with synonyms
    expanded_words = words.copy()
    for word in words:
        if word in synonyms:
            expanded_words.extend(synonyms[word])
    
    return expanded_words

def search_products(keywords: List[str]) -> List[Dict[str, Any]]:
    """Search products based on keywords"""
    results = []
    
    for product_id, product in MOCK_PRODUCTS.items():
        score = 0
        
        # Calculate relevance score
        for keyword in keywords:
            if keyword in product['keywords']:
                score += 2
            elif any(keyword in prod_keyword for prod_keyword in product['keywords']):
                score += 1
            elif keyword in product['name'].lower():
                score += 3
            elif keyword in product['description'].lower():
                score += 1
        
        if score > 0:
            product_copy = product.copy()
            product_copy['score'] = score
            results.append(product_copy)
    
    # Sort by relevance score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def record_audio(duration=5):
    """Record audio for specified duration"""
    try:
        audio = pyaudio.PyAudio()
        
        # Start recording
        stream = audio.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
        
        st.info(f"🎤 Recording for {duration} seconds... Speak now!")
        
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        # Stop recording
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        return frames
    except Exception as e:
        st.error(f"Error recording audio: {str(e)}")
        return None

def save_audio_to_file(frames):
    """Save recorded audio frames to a temporary WAV file"""
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        # Save audio to file
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return temp_file.name
    except Exception as e:
        st.error(f"Error saving audio file: {str(e)}")
        return None

def transcribe_with_groq(audio_file_path):
    """Transcribe audio using Groq API"""
    try:
        with open(audio_file_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="whisper-large-v3",
                response_format="json",
                language="en"
            )
        
        return transcription.text
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None


# Streamlit App Configuration (must be first)
st.set_page_config(
    page_title="Describo - Product Discovery Assistant",
    page_icon="🧩",
    layout="wide"
)

def main():
    # Initialize Behavioral Auth in session state
    if 'behavioral_auth' not in st.session_state:
        st.session_state.behavioral_auth = BehavioralAuth()
    
    # Header
    st.title("🧩 Describo - Product Discovery Assistant")
    st.markdown("*Find products even when you don't know their exact name!*")
    
     # Initialize session state
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'voice_text' not in st.session_state:
        st.session_state.voice_text = ""

    # Sidebar with examples
    with st.sidebar:
        st.header("💡 Try These Examples:")
        example_queries = [
            "foldable thing people sleep on during camping",
            "bottle which filters river water",
            "light that goes on your head for camping",
            "portable chair for outdoor use",
            "waterproof shelter for camping"
        ]
        
        for i, example in enumerate(example_queries):
            if st.button(f"Example {i+1}", key=f"example_{i}"):
                st.session_state.text_input = example
                # Log example usage
                st.session_state.behavioral_auth.log_interaction('example_click', metadata={'example': i})
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 Describe What You're Looking For")
        
        # Text input tab
        tab1, tab2 = st.tabs(["📝 Text Description", "🎤 Voice Input"])
        
        with tab1:
            text_input = st.text_area(
                "Describe the product you're looking for:",
                placeholder="e.g., 'I need that foldable thing people sleep on during camping'",
                height=100,
                key="text_input"
            )
            
            if st.button("🔍 Search", type="primary"):
                if text_input:
                    # Log search interaction
                    st.session_state.behavioral_auth.log_interaction('search', metadata={'query_length': len(text_input), 'input_type': 'text'})
                    
                    with st.spinner("Analyzing your description..."):
                        keywords = analyze_text_description(text_input)
                        results = search_products(keywords)
                        
                        st.session_state.search_results = results
                        st.session_state.search_keywords = keywords
                        st.rerun()
        
        with tab2:
            st.info("🎤 Voice Input - Speak Your Product Description")
            
            # Initialize session state for voice input
            if 'voice_text' not in st.session_state:
                st.session_state.voice_text = ""
            
            # Voice input interface
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Display current voice text
                voice_text_display = st.text_area(
                    "Speech Recognition Output:",
                    value=st.session_state.voice_text,
                    height=100,
                    key="voice_display",
                    help="This will show what you speak"
                )
            
            with col2:
                st.write("**Instructions:**")
                st.write("1. Click 'Start Recording'")
                st.write("2. Speak clearly into your microphone")
                st.write("3. Click 'Stop Recording' when done")
                st.write("4. Review the text and search")
            
            # Voice input HTML component with improved implementation
            voice_html = """
            <div id="voice-container">
                <style>
                    .voice-status {
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                        text-align: center;
                        font-weight: bold;
                    }
                    .recording { background-color: #ffebee; color: #c62828; }
                    .ready { background-color: #e8f5e8; color: #2e7d32; }
                    .error { background-color: #fff3e0; color: #ef6c00; }
                </style>
                <div id="status" class="voice-status ready">Ready to record</div>
                <script>
                    let recognition = null;
                    let isRecording = false;
                    let finalTranscript = '';
                    
                    const statusDiv = document.getElementById('status');
                    
                    // Check if browser supports speech recognition
                    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                        recognition = new SpeechRecognition();
                        
                        recognition.continuous = true;
                        recognition.interimResults = true;
                        recognition.lang = 'en-US';
                        
                        recognition.onstart = function() {
                            isRecording = true;
                            statusDiv.innerHTML = '🔴 Recording... Speak now!';
                            statusDiv.className = 'voice-status recording';
                        };
                        
                        recognition.onresult = function(event) {
                            let interimTranscript = '';
                            
                            for (let i = event.resultIndex; i < event.results.length; i++) {
                                const transcript = event.results[i][0].transcript;
                                if (event.results[i].isFinal) {
                                    finalTranscript += transcript + ' ';
                                } else {
                                    interimTranscript += transcript;
                                }
                            }
                            
                            // Send the transcript to Streamlit
                            const fullTranscript = finalTranscript + interimTranscript;
                            window.parent.postMessage({
                                type: 'voice_transcript',
                                transcript: fullTranscript
                            }, '*');
                        };
                        
                        recognition.onerror = function(event) {
                            console.error('Speech recognition error:', event.error);
                            statusDiv.innerHTML = '❌ Error: ' + event.error;
                            statusDiv.className = 'voice-status error';
                            isRecording = false;
                        };
                        
                        recognition.onend = function() {
                            isRecording = false;
                            statusDiv.innerHTML = '✅ Recording stopped';
                            statusDiv.className = 'voice-status ready';
                        };
                    } else {
                        statusDiv.innerHTML = '❌ Speech recognition not supported in this browser';
                        statusDiv.className = 'voice-status error';
                    }
                    
                    function startRecording() {
                        if (recognition && !isRecording) {
                            finalTranscript = '';
                            recognition.start();
                            return true;
                        }
                        return false;
                    }
                    
                    function stopRecording() {
                        if (recognition && isRecording) {
                            recognition.stop();
                            return true;
                        }
                        return false;
                    }
                    
                    function clearTranscript() {
                        finalTranscript = '';
                        window.parent.postMessage({
                            type: 'voice_transcript',
                            transcript: ''
                        }, '*');
                    }
                    
                    // Make functions available globally
                    window.startRecording = startRecording;
                    window.stopRecording = stopRecording;
                    window.clearTranscript = clearTranscript;
                </script>
            </div>
            """
            
            # Inject the HTML/JavaScript
            components.html(voice_html, height=150)
            
            # Control buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("🎤 Start Recording", key="start_recording", disabled=st.session_state.is_recording):
                    st.session_state.is_recording = True
                    
                    # Record audio
                    frames = record_audio(duration=5)
                    
                    if frames:
                        # Save to temporary file
                        audio_file = save_audio_to_file(frames)
                        
                        if audio_file:
                            # Transcribe using Groq
                            with st.spinner("Transcribing audio..."):
                                transcribed_text = transcribe_with_groq(audio_file)
                                
                                if transcribed_text:
                                    st.session_state.voice_text = transcribed_text
                                    st.success("✅ Transcription completed!")
                                else:
                                    st.error("❌ Transcription failed!")
                            
                            # Clean up temporary file
                            try:
                                os.unlink(audio_file)
                            except:
                                pass
                    
                    st.session_state.is_recording = False
                    st.rerun()
            
            with col2:
                if st.button("⏹️ Stop Recording", key="stop_recording"):
                    st.session_state.behavioral_auth.log_interaction('voice_stop')
                    st.info("Recording stopped. Check the text area above for results.")
            
            with col3:
                if st.button("🗑️ Clear", key="clear_voice"):
                    st.session_state.voice_text = ""
                    st.rerun()
            
            # Manual text input as fallback
            st.markdown("---")
            st.write("**Or type manually:**")
            manual_voice_input = st.text_input(
                "Type your product description here:",
                key="manual_voice_input",
                placeholder="e.g., 'I need that foldable thing people sleep on during camping'"
            )
            
            # Search button for voice input
            if st.button("🔍 Search from Voice/Text", type="primary", key="search_voice"):
                search_text = voice_text_display.strip() or manual_voice_input.strip()
                if search_text:
                    st.session_state.behavioral_auth.log_interaction('voice_search', metadata={'query_length': len(search_text)})
                    with st.spinner("Analyzing your input..."):
                        keywords = analyze_text_description(search_text)
                        results = search_products(keywords)
                        
                        st.session_state.search_results = results
                        st.session_state.search_keywords = keywords
                        st.session_state.voice_text = search_text
                        st.rerun()
                else:
                    st.warning("Please provide voice input or type your description!")
            
            # Browser compatibility and tips
            st.markdown("---")
            st.caption("📱 **Browser Support**: Works best in Chrome, Edge, and Safari. Make sure to allow microphone access when prompted.")
            st.caption("💡 **Tips**: Speak clearly and wait a moment after speaking for the best results.")
    
    with col2:
        st.header("📊 How It Works")
        st.markdown("""
        1. **Describe** what you're looking for
        2. **AI analyzes** your description
        3. **Matches** products from database
        4. **Shows** relevant results with details
        """)
        
        # Show extracted keywords if available
        if hasattr(st.session_state, 'search_keywords') and st.session_state.search_keywords:
            st.subheader("🔑 Extracted Keywords:")
            st.write(", ".join(st.session_state.search_keywords))
    
    # Search results
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.header("🎯 Search Results")
        
        if not st.session_state.search_results:
            st.warning("No products found matching your description. Try different keywords!")
        else:
            for i, product in enumerate(st.session_state.search_results[:5]):  # Show top 5 results
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        st.image(product['image_url'], width=150)
                    
                    with col2:
                        st.subheader(product['name'])
                        st.write(product['description'])
                        
                        # Rating stars
                        stars = "⭐" * int(product['rating'])
                        st.write(f"{stars} {product['rating']}/5")
                        
                        # Relevance score (for demo)
                        st.caption(f"Relevance Score: {product['score']}")
                    
                    with col3:
                        st.metric("Price", product['price'])
                        
                        if product['availability'] == "In Stock":
                            st.success("✅ In Stock")
                        else:
                            st.error("❌ Out of Stock")
                        
                        if st.button(f"View Details", key=f"view_{i}"):
                            st.session_state.behavioral_auth.log_interaction('product_view', metadata={'product_rank': i+1})
                
                st.divider()
    
    # Checkout simulation with BBA
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.header("🛒 Checkout Demo - No CAPTCHA Required!")
        
        # Simulate checkout process
        checkout_col1, checkout_col2 = st.columns([1, 1])
        
        with checkout_col1:
            st.subheader("Traditional E-commerce")
            st.error("❌ CAPTCHA Required")
            st.image("https://via.placeholder.com/400x200?text=Select+all+traffic+lights", caption="Frustrating CAPTCHA")
            st.button("😤 Struggle with CAPTCHA", disabled=True)
        
        with checkout_col2:
            st.subheader("Describo with BBA")
            
            if st.session_state.behavioral_auth.is_human():
                st.success("✅ Human Verified - No CAPTCHA needed!")
                st.write("**Verification based on:**")
                st.write("• Natural browsing patterns")
                st.write("• Voice interaction usage")
                st.write("• Time spent on site")
                st.write("• Search behavior analysis")
                
                if st.button("🛒 Checkout Seamlessly", type="primary"):
                    st.session_state.behavioral_auth.log_interaction('checkout_attempt')
                    st.balloons()
                    st.success("🎉 Order placed successfully! No CAPTCHA needed.")
            else:
                st.warning("🔐 Building trust... Continue browsing to verify.")
                st.write(f"**Current Trust Score: {st.session_state.behavioral_auth.trust_score}/100**")
                st.write("**To improve trust score:**")
                st.write("• Try searching for products")
                st.write("• Use voice input feature")
                st.write("• Browse for a bit longer")
                st.write("• Click on example queries")
                
                progress_bar = st.progress(st.session_state.behavioral_auth.trust_score / 100)
                
                if st.button("🔒 Attempt Checkout", disabled=True):
                    st.info("Continue browsing to build trust and avoid CAPTCHA!")
    
    # Behavioral Analytics Dashboard
    with st.expander("📊 Behavioral Analytics Dashboard (Admin View)"):
        st.write("**User Interaction Timeline:**")
        
        if st.session_state.behavioral_auth.interactions:
            for i, interaction in enumerate(st.session_state.behavioral_auth.interactions[-10:]):  # Show last 10
                time_elapsed = interaction['timestamp'] - st.session_state.behavioral_auth.session_start
                st.write(f"• {interaction['action']} at {time_elapsed:.1f}s")
        
        st.write("**Trust Score Breakdown:**")
        st.write(f"• Base Score: 0")
        st.write(f"• Session Time Bonus: +{min(15, int((time.time() - st.session_state.behavioral_auth.session_start) / 4))}")
        st.write(f"• Interaction Variety: +{len(set(i['action'] for i in st.session_state.behavioral_auth.interactions)) * 5}")
        st.write(f"• Search Behavior: +{15 if any(i['action'] == 'search' for i in st.session_state.behavioral_auth.interactions) else 0}")
        st.write(f"• Voice Input: +{20 if any(i['action'].startswith('voice') for i in st.session_state.behavioral_auth.interactions) else 0}")
        
        st.metric("Final Trust Score", f"{st.session_state.behavioral_auth.trust_score}/100")
    
    # Footer
    st.markdown("---")
    st.markdown("*Describo Prototype - Built with Streamlit | Featuring Behavioral-Based Authentication*")
    st.caption("🔒 **Privacy Note**: All behavioral data is processed locally and not stored permanently.")

if __name__ == "__main__":
    main()