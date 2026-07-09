# Resumey 🍁

Resumey is a modern, Python Streamlit web application designed to customize resumes and craft cover letters optimized for the Canadian job market. Driven by a system prompt simulating a 30-year veteran HR Executive, it aligns candidate backgrounds with job descriptions while avoiding hallucinations.

## ✨ Features

- **Canadian Formatting Standards**: Formats contact headers cleanly (City, Province) without street addresses, photos, gender, or age for privacy protection.
- **30-Year HR Voice**: Rewrites experience using past/present tense action verbs following the CAR (Challenge-Action-Result) framework.
- **Strict Truth Preservation**: Zero hallucinations. If you omit metrics, the system leaves bracketed placeholders `[X]%` or `[Number]` for you to customize, rather than fabricating numbers.
- **PDF Text Parser**: Upload your PDF or TXT resume directly; the text is extracted automatically on the backend using `pypdf`.
- **Print & Export**: Prints standard Letter size layouts cleanly (automatically stripping all Streamlit controls) or exports Markdown/HTML files.
- **Multiple AI Connection Providers**:
  - **Google Gemini API**: Free tier available from Google AI Studio.
  - **Ollama**: 100% offline, local, and private execution.
  - **Custom OpenAI-Compatible API**: Connects to other free/low-cost endpoints (e.g. Groq).

## 🚀 Getting Started

1. Clone or download the repository.
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   python -m streamlit run app.py
   ```
4. Open the application in your browser (defaults to `http://localhost:8501`).
5. Configure your preferred AI connection provider in the sidebar, fill in the job details, upload your resume file, and click **Customize Resume & Cover Letter**.

## 🔒 Privacy & Security

All operations occur locally. Your API keys are saved locally in `local_settings.json` (which is git-ignored) and are never sent to external servers, except the selected API provider endpoint.
