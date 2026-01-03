# 🌐 Instant Translator

**Capture any text on your screen and translate it instantly!**

Perfect for:
- 🎮 **Gaming** - Translate Japanese/Korean/Chinese games in real-time
- 📺 **Streaming** - Understand foreign content without subtitles  
- 📖 **Reading** - Translate documents, websites, or images
- 💬 **Chat** - Translate messages from any app

---

## ✨ What It Does

1. **📸 Capture** - Take a screenshot of any window or region
2. **🔍 Extract** - AI reads all the text from the image
3. **🌍 Translate** - Instantly translates to English (or any language)

**Global Hotkey:** Press `Shift + C` from anywhere to capture instantly!

---

## 🖼️ How It Looks

The app shows two panels:
- **Left Panel** - Your captured screenshot
- **Right Panel** - Extracted text + Translation

---

## 🚀 Quick Start

### Step 1: Get Your API Key

You need a **ZenMux API key** for translations:
1. Visit [ZenMux.ai](https://zenmux.ai)
2. Create an account and get your API key
3. The key looks like: `sk-ai-v1-xxxxxxxxxxxx`

### Step 2: Install Python

If you don't have Python installed:
1. Download from [python.org](https://www.python.org/downloads/)
2. **Important:** Check ✅ "Add Python to PATH" during installation
3. Restart your computer after installing

### Step 3: Download & Setup

1. **Download** this project (or clone it)
2. **Open Terminal** in the project folder:
   - Right-click inside the folder → "Open in Terminal" (Windows 11)
   - Or press `Win + R`, type `cmd`, navigate to folder

3. **Run these commands one by one:**

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install required packages (this takes a few minutes)
pip install -r requirements.txt
```

### Step 4: Configure API Key

1. Open the `.env` file in the project folder (use Notepad)
2. Replace `your_api_key_here` with your actual ZenMux API key:

```
ZENMUX_API_KEY=sk-ai-v1-your-actual-key-here
```

3. Save the file

### Step 5: Run the App!

```bash
# Make sure venv is activated (you should see "(venv)" at the start)
venv\Scripts\activate

# Run the app
python -m src.main
```

🎉 **That's it!** The app should open.

---

## 📖 How to Use

1. **Select a window** from the dropdown (top-left)
2. **Click "Capture"** or press `Shift + C`
3. **Wait** a few seconds for OCR and translation
4. **View results** in the right panel
5. **Copy** the translation with the Copy button

### 💡 Tips

- **First capture is slower** - The app downloads language models (~100MB)
- **Subsequent captures are faster** - Models are cached
- **Edit OCR errors** - You can fix text in the "Extracted Text" tab and click "Retranslate"

---

## 🌏 Supported Languages

Currently set up for:
- 🇬🇧 English
- 🇰🇷 Korean

Want more languages? Open `src/gui/main_window.py` and find line ~125:
```python
languages=['en', 'ko'],  # Add 'ja' for Japanese, 'ch_sim' for Chinese
```

---

## ⚙️ Optional: Install Tesseract (Better OCR)

For **improved accuracy**, you can install Tesseract OCR:

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer, check "Additional language data" for your languages
3. Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

The app works fine without it (uses EasyOCR), but having both gives better results.

---

## ❓ Troubleshooting

### "No text found in image"
- Try capturing a clearer image with larger text
- Some stylized fonts are hard to read

### "API error" or "Connection error"
- Check your internet connection
- Verify your API key in `.env` is correct

### "Tesseract not installed" warning
- This is just a warning, not an error
- The app still works using EasyOCR

### App freezes during first capture
- Normal! It's downloading OCR models (~100MB)
- Wait 1-2 minutes, it only happens once

---

## 📁 Project Structure

```
Instant-Translator/
├── src/              # Main application code
├── tests/            # Automated tests
├── venv/             # Python packages (created after setup)
├── .env              # Your API key goes here
├── requirements.txt  # Package list
└── README.md         # This file
```

---

## 🔧 For Developers

### Running Tests
```bash
python -m pytest tests/ -v
```

### Technology Stack
- **GUI**: PyQt6
- **OCR**: EasyOCR + Tesseract (optional)
- **Translation**: ZenMux API (DeepSeek V3.2)
- **Hotkeys**: keyboard library

---

Made by ClaRity Group
