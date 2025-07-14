
# Installation Guide for Describo

This guide will walk you through setting up the Describo application on your local machine.

---

## 1. Clone the Repository

First, clone the repository from GitHub:

```bash
git clone https://github.com/your-username/describo.git
cd describo
```

Replace `your-username` with your actual GitHub username if you've uploaded the project there.

---

## 2. Set Up a Virtual Environment (Optional but Recommended)

Using a virtual environment ensures dependencies don’t conflict with other projects:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## 3. Install Python Dependencies

Install all the required libraries using pip:

```bash
pip install -r requirements.txt
```

Make sure you have `pip` and Python 3.8+ installed.

---

## 4. Set Up API Key for Groq

Describo uses the Groq API for voice transcription. You need to set your API key either via environment variable or secrets file.

### Option 1: Using Environment Variable

```bash
export api_key="your_groq_api_key"  # On Windows: set api_key=your_groq_api_key
```

### Option 2: Using Streamlit Secrets

Create a `.streamlit/secrets.toml` file with the following content:

```toml
api_key = "your_groq_api_key"
```

---

## 5. Run the Application

Once everything is set up, launch the Streamlit app:

```bash
streamlit run new.py
```

---

## 6. Troubleshooting

- **PyAudio not installing?** Try installing system dependencies first:
  - On Debian/Ubuntu: `sudo apt-get install portaudio19-dev`
  - On Windows: download the correct PyAudio `.whl` file from [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- **Microphone access denied?** Ensure your browser has microphone permissions enabled when using voice input.

---

## Need Help?

If you run into issues, feel free to open a GitHub issue in the repository.
