"""
Minimal Gemini API test: List available models for your API key.
Run: python test_gemini_models.py
"""
import os
try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai package not found. Please install with: pip install google-generativeai")
    exit(1)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not set in environment.")
    exit(1)

genai.configure(api_key=api_key)
try:
    models = genai.list_models()
    print("Available Gemini models:")
    for m in models:
        print("-", m.name)
except Exception as e:
    print("Error listing models:", e)
