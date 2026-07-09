# Resumey 🍁

Resumey is a modern, client-side web application designed to customize resumes and craft cover letters optimized for the Canadian job market. Driven by a system prompt simulating a 30-year veteran HR Executive, it aligns candidate backgrounds with job descriptions while avoiding hallucinations.

## ✨ Features

- **Canadian Formatting Standards**: Formats contact headers cleanly (City, Province) without street addresses, photos, gender, or age for privacy protection.
- **30-Year HR Voice**: Rewrites experience using past/present tense action verbs following the CAR (Challenge-Action-Result) framework.
- **Strict Truth Preservation**: Zero hallucinations. If you omit metrics, the system leaves bracketed placeholders `[X]%` or `[Number]` for you to customize, rather than fabricating numbers.
- **PDF.js Parser**: Drop your PDF resume directly; the text is extracted client-side in the browser.
- **Print & Export**: Prints standard Letter size layouts cleanly (automatically stripping UI components) or exports standalone HTML/Markdown files.
- **Multiple AI Connection Providers**:
  - **Google Gemini API**: Free tier available from Google AI Studio.
  - **Ollama**: 100% offline, local, and private execution.
  - **Custom OpenAI-Compatible API**: Connects to other free/low-cost endpoints (e.g. Groq).

## 🚀 Getting Started

1. Clone or download the repository.
2. Open `index.html` directly in your browser, or serve it using a local HTTP server:
   ```bash
   python -m http.server 8080
   ```
3. Click the gear icon on the top right to set up your preferred AI provider (e.g. Gemini or Ollama).
4. Fill in the job details, drag & drop your resume, and click **Customize Resume & Cover Letter**.

## 🔒 Privacy & Security

All operations occur client-side in your browser. Your API keys are saved locally in the browser's `localStorage` and are never sent to external servers, except the selected API provider endpoint.
