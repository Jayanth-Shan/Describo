# Describo - Product Discovery Assistant

Describo is a simple, AI-powered product discovery tool built with Streamlit. It helps users find what they’re looking for—even if they don’t know the exact name of the product. Just describe it in plain English or speak it out loud, and Describo will do the rest.

What makes it unique is how it verifies you're human. Instead of using annoying CAPTCHAs, it quietly analyzes how you interact with the site and builds a trust score. If your behavior looks natural, you skip the CAPTCHA altogether.

---

## What You Can Do With Describo

### Describe Products in Your Own Words
No need to remember product names. You can type something like:  
*“That foldable thing people sleep on when camping”*  
Describo uses natural language processing (NLP) to extract useful keywords and show you the best matches.

### Speak Instead of Typing
Don’t want to type? Use your voice. The app includes voice input support powered by the Groq API and Whisper model. You record your description, and it gets transcribed on the fly.

### No More CAPTCHAs
Describo comes with a behavioral-based authentication (BBA) system that:
- Tracks natural user behavior like searching, time spent, voice usage, etc.
- Calculates a trust score
- Skips CAPTCHA if you’re likely human

### Browse a Mock Product Catalog
The app currently includes a small demo catalog of outdoor gear like:
- Camping cots  
- Water purifiers  
- Headlamps  
- Sleeping bags  
- Tents  
- Camping chairs  

### View Your Trust Score (Admin Mode)
There’s also a built-in dashboard that shows your session’s interaction history and the logic behind your current trust score.

---

## How It Works

1. You describe what you’re looking for using text or voice.
2. The app pulls out important keywords.
3. Products are matched based on relevance.
4. Behind the scenes, it tracks how you interact.
5. If your behavior seems human, you skip any verification hassle.

---

## Tech Stack

| Purpose                  | Technology                          |
|--------------------------|--------------------------------------|
| Web Interface            | Streamlit                            |
| Speech Recognition       | Groq API (Whisper-large-v3)          |
| Audio Recording          | PyAudio, Wave                        |
| Image Handling           | Pillow (PIL)                         |
| Behavior Tracking        | Custom Python logic                  |
| Product Matching         | Basic NLP (regex + keywords)         |

---
