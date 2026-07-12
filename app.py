import streamlit as st
import requests
import json
import os
import re
import io
import unicodedata
import markdown
from pypdf import PdfReader
from fpdf import FPDF, FontFace
 
# Try to import WeasyPrint defensively
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    pass

# Page Configuration
st.set_page_config(
    page_title="Resumey 🍁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants & Paths
SETTINGS_FILE = "local_settings.json"

# Master System Prompt
SYSTEM_PROMPT = """You are a 30-year veteran Canadian HR Director and Executive Recruiter, expert in Applicant Tracking Systems (ATS) and hiring processes. Your task is to customize the candidate's resume and draft a tailored cover letter based on the provided Job Description (JD) and the candidate's current resume, formatting them as raw, compileable LaTeX documents.

### RULES FOR ESCAPING LATEX SPECIAL CHARACTERS (CRITICAL):
- You MUST escape all LaTeX special characters in the text (like &, %, _, $, #, {, }):
  - Replace '&' with '\\&' (e.g. 'A \\& B')
  - Replace '%' with '\\%' (e.g. '95\\%')
  - Replace '_' with '\\_' (e.g. 'first\\_name')
  - Replace '$' with '\\$' (e.g. '\\$100k')
  - Replace '#' with '\\#' (e.g. 'C\\#')
  - Replace '{' with '\\{'
  - Replace '}' with '\\}'
- Do NOT output any markdown tags (like **, *, #) inside the LaTeX blocks.
- Ensure all text quotes are formatted correctly for LaTeX (e.g. ``double quotes'' and `single quotes').

### RULES FOR CUSTOMIZING THE RESUME:
1. STRICT TRUTH (NO HALLUCINATIONS):
   - Do NOT invent any companies, degrees, dates, certifications, or achievements.
   - If the candidate does not have a skill or has not worked in a specific role/industry, do not add it.
   - If you need to write an achievement but the candidate's resume lacks a numeric metric, do NOT invent numbers (like "increased sales by 45%"). Instead, use a placeholder in brackets like "[X]%" or "[Number]" so the candidate knows to insert their actual data, or focus on a strong qualitative achievement.
2. EYE-CATCHING & ACTION-ORIENTED BULLETS (RECRUITER STAMP OF EXCELLENCE):
   - Every bullet point under 'Professional Experience' must start with a powerful, distinct action verb (e.g., Orchestrated, Spearheaded, Architected, Optimized). Avoid weak verbs like Managed, Assisted.
   - Use the CAR (Challenge, Action, Result) structure. Clearly define the technical challenge, the specific action taken, and the quantified or qualitative result.
   - Keep bullet points punchy and highly scannable; each bullet point must be concise and should never exceed 2 lines.
3. VALUE-DRIVEN PROFESSIONAL SUMMARY:
   - The Professional Summary must be a highly tailored 3-4 sentence paragraph. Start by establishing the candidate's core title and years of relevant experience, follow with 1-2 major technical or leadership specialties, and end with a compelling value proposition. Do NOT use an Objective statement.
4. CANADIAN FORMATTING STANDARDS:
   - Header: Include Name, Phone, Email, LinkedIn Profile URL, and City & Province/Territory (e.g., "Toronto, ON" or "Calgary, AB"). NEVER include full street addresses, photos, age, gender, marital status, nationality, or visa statuses.
   - Core Competencies / Key Skills: Exactly 6 to 9 key skills matched to keywords in the JD.
   - Professional Experience: Reverse-chronological order.
   - Education: List degree/diploma, major, school name, and city/province.
   - No References: Do not include "References available upon request".
5. ATS OPTIMIZATION:
   - Identify critical keywords, technical skills, and tools in the Job Description and integrate them naturally into the Professional Summary, Core Competencies, and Professional Experience sections.

### RULES FOR WRITING THE COVER LETTER:
1. CANADIAN BUSINESS LETTER FORMAT:
   - Include Candidate's contact info, Date, and Recipient Info.
   - Include a clear Subject line: "RE: Application for [Job Title] - Reference/Job ID [if any]".
2. RECRUITER-HOOKING STRUCTURE (HIGH IMPACT & PUNCHY):
   - Open with a powerful value-hook highlighting the candidate's core title, years of experience, and why they want to bring their expertise to the company.
   - Body Paragraph 1 (Alignment / Why You): Connect the candidate's background directly to the top 2-3 key challenges or priorities listed in the Job Description.
   - Body Paragraph 2 (Evidence of Impact / CAR Context): Highlight 1-2 of the candidate's most impressive, verified achievements from their resume.
   - Closing & Call to Action: Reiterate excitement, request an interview/discussion, and sign off professionally ("Sincerely," followed by name).
3. SCANNABILITY & BREVITY: Keep the letter under 300-350 words, split into distinct, readable paragraphs.

### OUTPUT FORMAT:
You MUST output the customized resume and the cover letter in a single response, separated by the exact tags below so the application can split and display them correctly.

Format the output exactly as follows:

===RESUME_START===
\\documentclass[10pt,letterpaper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{xcolor}
\\usepackage{hyperref}

% Sans-serif font
\\renewcommand{\\familydefault}{\\sfdefault}

% Color definitions
\\definecolor{primary}{HTML}{0F172A} % slate-900
\\definecolor{secondary}{HTML}{1E293B} % slate-800
\\definecolor{muted}{HTML}{64748b} % slate-500
\\definecolor{rulecolor}{HTML}{E2E8F0} % slate-200

% Custom Section command without titlesec dependency
\\renewcommand{\\section}[1]{%
  \\vspace{12pt}%
  \\noindent{\\color{primary}\\large\\bfseries\\uppercase{#1}}\\\\%
  \\vspace{-6pt}%
  {\\color{rulecolor}\\rule{\\linewidth}{0.8pt}}\\\\%
  \\vspace{6pt}%
}

\\hypersetup{
    colorlinks=true,
    linkcolor=secondary,
    urlcolor=secondary
}

\\begin{document}
\\pagestyle{empty}

\\begin{center}
    {\\color{primary}\\Huge\\bfseries [CANDIDATE NAME]} \\\\ [0.5em]
    {\\color{muted}\\small [City, Province] \\textbullet{} [Phone] \\textbullet{} [Email] \\textbullet{} \\href{[LinkedIn URL]}{[LinkedIn]}}
\\end{center}

\\section{Professional Summary}
[Professional summary text here...]

\\section{Core Competencies}
\\noindent [Skill 1] \\textbullet{} [Skill 2] \\textbullet{} [Skill 3] \\textbullet{} [Skill 4] \\textbullet{} [Skill 5] \\textbullet{} [Skill 6] \\textbullet{} [Skill 7] \\textbullet{} [Skill 8] \\textbullet{} [Skill 9]

\\section{Professional Experience}
\\noindent \\textbf{[Company Name]} \\hfill {\\color{muted}\\textit{[City, Province/Country]}} \\\\
\\textit{[Job Title]} \\hfill {\\color{muted}[Month Year] -- [Month Year or Present]}
\\begin{itemize}
    \\item [Achievement bullet 1 starting with active verb]
    \\item [Achievement bullet 2 starting with active verb]
\\end{itemize}

\\section{Education}
\\noindent \\textbf{[Degree Name] in [Major]} \\hfill {\\color{muted}[Graduation Year]} \\\\
[University/Institution Name], [City, Province/Country]

\\end{document}
===RESUME_END===

===LETTER_START===
\\documentclass[10pt,letterpaper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{xcolor}
\\usepackage{hyperref}

% Sans-serif font
\\renewcommand{\\familydefault}{\\sfdefault}

% Color definitions
\\definecolor{primary}{HTML}{0F172A}
\\definecolor{secondary}{HTML}{1E293B}
\\definecolor{muted}{HTML}{64748b}

\\hypersetup{
    colorlinks=true,
    linkcolor=secondary,
    urlcolor=secondary
}

\\begin{document}
\\pagestyle{empty}

\\begin{center}
    {\\color{primary}\\Huge\\bfseries [CANDIDATE NAME]} \\\\ [0.5em]
    {\\color{muted}\\small [City, Province] \\textbullet{} [Phone] \\textbullet{} [Email] \\textbullet{} \\href{[LinkedIn URL]}{[LinkedIn]}}
\\end{center}

\\vspace{12pt}

\\noindent [Current Date] \\\\

\\noindent \\textbf{Hiring Committee} \\\\
[Company Name] \\\\
[Company Address or City, Province] \\\\

\\vspace{12pt}
\\noindent \\textbf{RE: Application for [Job Title]}
\\vspace{12pt}

\\noindent Dear Hiring Committee,

\\vspace{10pt}
[Cover Letter Body Paragraph 1...]

\\vspace{10pt}
[Cover Letter Body Paragraph 2...]

\\vspace{10pt}
[Cover Letter Body Paragraph 3...]

\\vspace{15pt}
\\noindent Sincerely, \\\\
\\\\
\\noindent [Candidate Name]

\\end{document}
===LETTER_END=== """

# Settings management (storing credentials locally on disk)
def load_local_settings():
    # Safely query st.secrets if it exists
    def get_secret(key):
        try:
            return st.secrets.get(key, "")
        except Exception:
            return ""

    default_settings = {
        "api_provider": os.environ.get("API_PROVIDER", get_secret("api_provider") or "gemini-api"),
        "gemini_key": os.environ.get("GEMINI_KEY", get_secret("gemini_key") or ""),
        "gemini_model": os.environ.get("GEMINI_MODEL", get_secret("gemini_model") or "gemini-3-flash-preview"),
        "ollama_host": os.environ.get("OLLAMA_HOST", get_secret("ollama_host") or "http://localhost:11434"),
        "ollama_model": os.environ.get("OLLAMA_MODEL", get_secret("ollama_model") or "llama3"),
        "openai_url": os.environ.get("OPENAI_URL", get_secret("openai_url") or ""),
        "openai_key": os.environ.get("OPENAI_KEY", get_secret("openai_key") or ""),
        "openai_model": os.environ.get("OPENAI_MODEL", get_secret("openai_model") or "")
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                # Merge loaded file settings, prioritising file settings
                return {**default_settings, **json.load(f)}
        except Exception:
            pass
    return default_settings

def save_local_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        st.error(f"Error saving settings file: {e}")

# Load initial state
initial_settings = load_local_settings()
for key, val in initial_settings.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Premium CSS Injection
st.markdown("""
<style>
    /* Global style overrides */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
    
    .main {
        background-color: #0b0f19 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(239, 68, 68, 0.04) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
    }
    
    /* Header Area styling */
    .header-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .logo-badge {
        background: linear-gradient(135deg, #0ea5e9 0%, #ef4444 100%);
        color: white;
        padding: 0.5rem 1rem;
        font-size: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25);
    }
    
    .title-text h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        background: linear-gradient(to right, #ffffff, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .title-text p {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
    }
    
    /* White Paper sheets for Resume / Cover letter Previews */
    .paper-wrapper {
        padding: 2rem;
        background-color: #1e293b;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
    }
    
    .document-paper {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        padding: 3.5rem 3rem !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35) !important;
        border-radius: 4px !important;
        width: 100% !important;
        max-width: 800px !important;
        min-height: 1056px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 10.5pt !important;
        line-height: 1.45 !important;
        overflow-wrap: break-word !important;
    }
    
    .letter-paper {
        font-family: 'Lora', Georgia, serif !important;
        font-size: 11pt !important;
        line-height: 1.5 !important;
    }
    
    /* Document Elements spacing */
    .document-paper h1, 
    .document-paper h2, 
    .document-paper h3 {
        color: #111827 !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .document-paper h1 {
        font-size: 18pt !important;
        font-weight: 700 !important;
        text-align: center !important;
        margin-bottom: 0.25rem !important;
    }
    
    .document-paper h2 {
        font-size: 12pt !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border-bottom: 1.5px solid #222 !important;
        padding-bottom: 2px !important;
        margin-top: 1.25rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    .document-paper h3 {
        font-size: 11pt !important;
        font-weight: 700 !important;
    }
    
    .document-paper p {
        margin-bottom: 0.75rem !important;
    }
    
    .document-paper ul {
        margin-bottom: 1rem !important;
        padding-left: 1.25rem !important;
    }
    
    .document-paper li {
        margin-bottom: 0.35rem !important;
    }
    
    .document-paper a {
        color: #1d4ed8 !important;
        text-decoration: none !important;
    }
    
    /* Header layouts */
    .resume-header-info {
        text-align: center;
        font-size: 9.5pt;
        color: #4b5563;
        margin-bottom: 1.25rem;
    }
    
    /* Flexible experience headings */
    .exp-row {
        display: flex;
        justify-content: space-between;
        font-weight: 700;
        margin-bottom: 2px;
        color: #111827 !important;
    }
    
    .exp-location {
        font-weight: 400;
        font-style: italic;
        color: #4b5563;
    }
    
    .exp-title-row {
        display: flex;
        justify-content: space-between;
        font-style: italic;
        margin-bottom: 6px;
        color: #374151 !important;
    }
    
    /* Utility alert container overrides */
    .stAlert {
        border-radius: 8px !important;
    }
    
    /* Javascript-free Print media configurations */
    @media print {
        /* Hide all Streamlit framework elements and input controls */
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        header,
        .header-container,
        [data-testid="stHorizontalBlock"],
        .stButton,
        button,
        [data-baseweb="tab-list"],
        .stAlert,
        hr,
        h3,
        .paper-wrapper {
            display: none !important;
        }
        
        /* Show the print-only document container */
        .print-only-container {
            display: block !important;
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            background: white !important;
            color: black !important;
        }
        
        /* Ensure the document paper takes full width and has no shadows */
        .print-only-container .document-paper {
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            min-height: auto !important;
        }
    }
    
    .print-only-container {
        display: none;
    }
    
    /* Mobile responsive media query */
    @media (max-width: 768px) {
        .paper-wrapper {
            padding: 0.5rem !important;
            background-color: transparent !important;
            border: none !important;
        }
        .document-paper {
            padding: 2rem 1.5rem !important;
            font-size: 9.5pt !important;
            min-height: auto !important;
            box-shadow: none !important;
            border-radius: 8px !important;
        }
        .header-container {
            flex-direction: column !important;
            align-items: center !important;
            text-align: center !important;
            gap: 0.5rem !important;
        }
        .logo-badge {
            font-size: 1.5rem !important;
            padding: 0.3rem 0.6rem !important;
        }
        .title-text h1 {
            font-size: 1.6rem !important;
        }
        /* Make experience header block items responsive (stack vertically if too long) */
        .exp-row, .exp-title-row {
            flex-direction: column !important;
            gap: 2px !important;
            margin-bottom: 6px !important;
        }
        .exp-location, .exp-title-row span:last-child {
            font-size: 0.85em !important;
            margin-left: 0 !important;
            color: #6b7280 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Main Application Title
st.markdown("""
<div class="header-container">
    <div class="logo-badge">🍁</div>
    <div class="title-text">
        <h1>Resumey</h1>
        <p>Canadian Resume & Cover Letter Generator (ATS-Optimized)</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Settings Configuration
with st.sidebar:
    st.markdown("### ⚙️ Connection Settings")
    st.write("Select the AI engine for content optimization.")
    
    # Provider selection
    api_provider = st.selectbox(
        "AI Provider",
        options=["gemini-api", "ollama-local", "openai-compatible"],
        format_func=lambda x: {
            "gemini-api": "Google Gemini API (Free Tier)",
            "ollama-local": "Ollama (Local LLM - Free/Private)",
            "openai-compatible": "Custom OpenAI-Compatible API"
        }[x],
        key="api_provider"
    )
    
    # Display settings based on provider
    if api_provider == "gemini-api":
        st.info("💡 You can get a free API Key instantly from [Google AI Studio](https://aistudio.google.com/) without needing a credit card.")
        st.text_input("Gemini API Key", type="password", key="gemini_key", placeholder="AIzaSy...")
        st.text_input("Model Name", key="gemini_model", placeholder="e.g. gemini-3-flash-preview")
        
    elif api_provider == "ollama-local":
        st.info("💡 Ensure Ollama is running on your machine. You may need to run it with CORS enabled (`OLLAMA_ORIGINS=\"*\"`).")
        st.text_input("Ollama Server URL", key="ollama_host")
        st.text_input("Model Name", key="ollama_model", placeholder="e.g. llama3, gemma2, mistral")
        
    elif api_provider == "openai-compatible":
        st.text_input("API Base URL", key="openai_url", placeholder="e.g. https://api.groq.com/openai/v1")
        st.text_input("API Key", type="password", key="openai_key")
        st.text_input("Model Name", key="openai_model", placeholder="e.g. llama3-70b-8192")

    # Save button
    if st.button("Save Settings", type="primary", use_container_width=True):
        # Update settings dict
        current_settings = {
            "api_provider": st.session_state.api_provider,
            "gemini_key": st.session_state.gemini_key,
            "gemini_model": st.session_state.gemini_model,
            "ollama_host": st.session_state.ollama_host,
            "ollama_model": st.session_state.ollama_model,
            "openai_url": st.session_state.openai_url,
            "openai_key": st.session_state.openai_key,
            "openai_model": st.session_state.openai_model
        }
        save_local_settings(current_settings)
        st.success("✓ Settings saved successfully!")

# Split Layout for Main Input Form (Two columns)
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📋 1. Job Description Details")
    target_title = st.text_input("Target Job Title *", placeholder="e.g., Senior Software Engineer")
    target_company = st.text_input("Company Name *", placeholder="e.g., Royal Bank of Canada")
    job_desc = st.text_area("Job Description *", height=200, placeholder="Paste the job description here. Keywords will be extracted to optimize the resume...")

with col2:
    st.markdown("### 📄 2. Upload Candidate Resume")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload PDF or TXT resume", type=["pdf", "txt"])
    
    # PDF Parsing Logic (State-safe to prevent re-runs overwriting inputs)
    if uploaded_file is not None:
        if st.session_state.get("last_uploaded_name") != uploaded_file.name:
            if uploaded_file.name.endswith(".pdf"):
                try:
                    reader = PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                    st.session_state["resume_text"] = text
                    st.session_state["last_uploaded_name"] = uploaded_file.name
                    st.toast(f"✓ Parsed PDF: {uploaded_file.name} ({len(reader.pages)} pages)")
                except Exception as e:
                    st.error(f"Error parsing PDF: {e}")
            else:
                try:
                    text = uploaded_file.read().decode("utf-8")
                    st.session_state["resume_text"] = text
                    st.session_state["last_uploaded_name"] = uploaded_file.name
                    st.toast(f"✓ Uploaded text: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
    else:
        st.session_state["resume_text"] = ""
        st.session_state["last_uploaded_name"] = None

# Generate Action Button
st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("✨ Customize Resume & Cover Letter", type="primary", use_container_width=True)

# Helper function to query the selected AI API
def call_llm_api(provider, job_title, company, jd, resume):
    user_prompt = f"""Job Title: {job_title}
Company: {company}

JOB DESCRIPTION:
{jd}

CANDIDATE CURRENT RESUME:
{resume}"""

    if provider == "gemini-api":
        key = st.session_state.gemini_key
        model = st.session_state.gemini_model
        if not key:
            raise ValueError("Please provide a Gemini API Key in the Settings panel.")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        body = {
            "contents": [
                {"parts": [{"text": user_prompt}]}
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "generationConfig": {
                "temperature": 0.3
            }
        }
        response = requests.post(url, json=body)
        if response.status_code != 200:
            err_msg = response.json().get("error", {}).get("message", "Unknown error")
            raise RuntimeError(f"Gemini API Error: {err_msg}")
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
    elif provider == "ollama-local":
        host = st.session_state.ollama_host.rstrip("/")
        model = st.session_state.ollama_model
        if not model:
            raise ValueError("Please provide a model name for Ollama in the Settings panel.")
            
        url = f"{host}/api/generate"
        body = {
            "model": model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{user_prompt}",
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }
        try:
            response = requests.post(url, json=body)
        except Exception as e:
            raise RuntimeError(f"Could not connect to Ollama. Make sure the server is running. Details: {e}")
            
        if response.status_code != 200:
            raise RuntimeError(f"Ollama returned status {response.status_code}")
        return response.json()["response"]
        
    elif provider == "openai-compatible":
        base_url = st.session_state.openai_url.rstrip("/")
        key = st.session_state.openai_key
        model = st.session_state.openai_model
        if not base_url or not model:
            raise ValueError("Please complete the Custom OpenAI API settings in the Settings panel.")
            
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3
        }
        response = requests.post(url, headers=headers, json=body)
        if response.status_code != 200:
            err_msg = response.json().get("error", {}).get("message", "Unknown error")
            raise RuntimeError(f"Custom API Error: {err_msg}")
        return response.json()["choices"][0]["message"]["content"]

# Delimiter Splitter
def parse_outputs(raw_text):
    resume = ""
    letter = ""
    
    resume_start = raw_text.find("===RESUME_START===")
    resume_end = raw_text.find("===RESUME_END===")
    letter_start = raw_text.find("===LETTER_START===")
    letter_end = raw_text.find("===LETTER_END===")
    
    if resume_start != -1 and resume_end != -1:
        resume = raw_text[resume_start + len("===RESUME_START==="):resume_end].strip()
        
    if letter_start != -1 and letter_end != -1:
        letter = raw_text[letter_start + len("===LETTER_START==="):letter_end].strip()
        
    # Fallback splitting if tags are missing
    if not resume or not letter:
        match = re.search(r'(?:#+|=+)\s*(?:COVER\s*LETTER|LETTER|DEAR\s+HIRING)', raw_text, re.IGNORECASE)
        if match:
            split_idx = match.start()
            resume = raw_text[:split_idx].replace("===RESUME_START===", "").replace("===RESUME_END===", "").strip()
            letter = raw_text[split_idx:].replace("===LETTER_START===", "").replace("===LETTER_END===", "").strip()
        else:
            resume = raw_text
            letter = raw_text
            
    # Clean up markdown code block wrapping (e.g. ```latex ... ```)
    def clean_latex(text):
        text = text.strip()
        text = re.sub(r'^```(?:latex)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()
        
    resume = clean_latex(resume)
    letter = clean_latex(letter)
            
    return resume, letter

# Regex Experience Block Formatter
def format_resume_markdown(markdown_content):
    if not markdown_content:
        return ""
    # Matches: **Company Name** - City, Province
    # *Job Title* | Month Year - Month Year
    exp_pattern = r'\*\*([^\*]+)\*\*\s*-\s*([^\n\r]+)[\r\n]+\*([^\*]+)\*\s*\|\s*([^\n\r]+)'
    
    def replace_exp(match):
        company = match.group(1).strip()
        location = match.group(2).strip()
        title = match.group(3).strip()
        dates = match.group(4).strip()
        return f'<div class="exp-row"><span><strong>{company}</strong></span><span class="exp-location">{location}</span></div><div class="exp-title-row"><span><em>{title}</em></span><span>{dates}</span></div>'
        
    return re.sub(exp_pattern, replace_exp, markdown_content)

# PDF Generation Utilities using fpdf2
def sanitize_text_for_pdf(text):
    if not text:
        return ""
    
    # Map common non-latin-1 unicode characters to ascii equivalents
    replacements = {
        "\u201c": '"',  # Left double quote
        "\u201d": '"',  # Right double quote
        "\u2018": "'",  # Left single quote
        "\u2019": "'",  # Right single quote
        "\u2013": "-",  # En-dash
        "\u2014": "-",  # Em-dash
        "\u2122": "TM", # Trademark
        "\u00ae": "(R)",# Registered Trademark
        "\u00a9": "(C)",# Copyright
        "\u2026": "...",# Ellipsis
        "\u00a0": " ",  # Non-breaking space
    }
    
    for uni_char, ascii_char in replacements.items():
        text = text.replace(uni_char, ascii_char)
        
    # Normalize accented characters and remove remaining non-ascii characters
    normalized = unicodedata.normalize('NFKD', text)
    encoded = normalized.encode('ascii', 'ignore')
    return encoded.decode('ascii')

def markdown_to_fpdf_html(markdown_text, doc_type="resume"):
    # 1. Sanitize text for PDF first (ASCII/Latin-1 conversion)
    sanitized_md = sanitize_text_for_pdf(markdown_text)
    
    # 2. For Resumes: Convert experience blocks in markdown to HTML tables before running the markdown parser!
    if doc_type == "resume":
        # Experience headers pattern:
        # **Company** - Location
        # *Title* | Dates
        exp_pattern = r'\*\*([^\*]+)\*\*\s*-\s*([^\n\r]+)[\r\n]+\*([^\*]+)\*\s*\|\s*([^\n\r]+)'
        
        def replace_exp_with_table(match):
            company = match.group(1).strip()
            location = match.group(2).strip()
            title = match.group(3).strip()
            dates = match.group(4).strip()
            return f'<table width="100%" border="0"><tr><td width="70%" align="left"><b>{company}</b></td><td width="30%" align="right"><font color="#64748b"><i>{location}</i></font></td></tr><tr><td align="left"><i>{title}</i></td><td align="right"><font color="#64748b">{dates}</font></td></tr></table>'
        
        sanitized_md = re.sub(exp_pattern, replace_exp_with_table, sanitized_md)
        
    # 3. Convert markdown to HTML
    html = markdown.markdown(sanitized_md)
    
    # 4. Replace <strong> with <b>, <em> with <i> for FPDF HTML parser safety
    html = html.replace("<strong>", "<b>").replace("</strong>", "</b>")
    html = html.replace("<em>", "<i>").replace("</em>", "</i>")
    
    # 5. Center Candidate Name (h1)
    html = html.replace("<h1>", '<h1 align="center">')
    
    # 6. Center Contact Info (paragraphs containing pipe delimiter '|')
    html = re.sub(r'<p>([^<]*\|[^<]*)</p>', r'<p align="center">\1</p>', html)
    
    return html
 
def download_fonts_if_needed():
    font_dir = "fonts"
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
        
    font_urls = {
        "Roboto-Regular.ttf": "https://cdn.jsdelivr.net/npm/roboto-fontface/fonts/roboto/Roboto-Regular.ttf",
        "Roboto-Bold.ttf": "https://cdn.jsdelivr.net/npm/roboto-fontface/fonts/roboto/Roboto-Bold.ttf",
        "Roboto-RegularItalic.ttf": "https://cdn.jsdelivr.net/npm/roboto-fontface/fonts/roboto/Roboto-RegularItalic.ttf",
        "Roboto-BoldItalic.ttf": "https://cdn.jsdelivr.net/npm/roboto-fontface/fonts/roboto/Roboto-BoldItalic.ttf"
    }
    
    for filename, url in font_urls.items():
        filepath = os.path.join(font_dir, filename)
        if not os.path.exists(filepath):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                pass

def markdown_to_weasy_html(markdown_text, doc_type="resume"):
    # Convert experience headers in markdown to HTML tables before running the markdown parser
    if doc_type == "resume":
        exp_pattern = r'\*\*([^\*]+)\*\*\s*-\s*([^\n\r]+)[\r\n]+\*([^\*]+)\*\s*\|\s*([^\n\r]+)'
        
        def replace_exp_with_table(match):
            company = match.group(1).strip()
            location = match.group(2).strip()
            title = match.group(3).strip()
            dates = match.group(4).strip()
            return f'<table class="exp-table"><tr><td class="left-col"><span class="company">{company}</span></td><td class="right-col"><span class="location">{location}</span></td></tr><tr><td class="left-col"><span class="title">{title}</span></td><td class="right-col"><span class="dates">{dates}</span></td></tr></table>'
            
        sanitized_md = re.sub(exp_pattern, replace_exp_with_table, markdown_text)
    else:
        sanitized_md = markdown_text
        
    # Convert markdown to HTML
    body_html = markdown.markdown(sanitized_md)
    
    # Center Contact Info (paragraphs containing pipe delimiter '|')
    body_html = re.sub(r'<p>([^<]*\|[^<]*)</p>', r'<p class="contact">\1</p>', body_html)
    
    # Build full HTML page with embedded styling (using Inter font for premium visual consistency)
    font_family = "'Inter', sans-serif"
    
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Document</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            @page {{
                size: letter;
                margin: 18mm;
                @bottom-right {{
                    content: counter(page) " / " counter(pages);
                    font-family: 'Inter', sans-serif;
                    font-size: 8pt;
                    color: #94a3b8;
                }}
            }}
            body {{
                font-family: {font_family};
                color: #1e293b;
                line-height: 1.45;
                font-size: 10pt;
                margin: 0;
                padding: 0;
            }}
            h1 {{
                font-size: 22pt;
                font-weight: 700;
                color: #0f172a;
                text-align: center;
                margin-top: 0;
                margin-bottom: 4px;
                letter-spacing: -0.5px;
            }}
            h2 {{
                font-size: 11pt;
                font-weight: 600;
                color: #0f172a;
                text-transform: uppercase;
                border-bottom: 0.75pt solid #e2e8f0;
                padding-bottom: 3px;
                margin-top: 16px;
                margin-bottom: 8px;
                letter-spacing: 0.5px;
            }}
            p {{
                margin-top: 0;
                margin-bottom: 8px;
                text-align: justify;
            }}
            p.contact {{
                text-align: center;
                font-size: 9pt;
                color: #64748b;
                margin-bottom: 16px;
                font-weight: 400;
            }}
            .exp-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 8px;
                margin-bottom: 4px;
            }}
            .exp-table td {{
                padding: 0;
                vertical-align: top;
            }}
            .exp-table .left-col {{
                width: 70%;
                text-align: left;
            }}
            .exp-table .right-col {{
                width: 30%;
                text-align: right;
            }}
            .exp-table .company {{
                font-weight: 700;
                font-size: 10pt;
                color: #0f172a;
            }}
            .exp-table .location {{
                color: #64748b;
                font-style: italic;
                font-size: 9.5pt;
            }}
            .exp-table .title {{
                font-style: italic;
                font-size: 9.5pt;
                color: #334155;
            }}
            .exp-table .dates {{
                color: #64748b;
                font-size: 9.5pt;
            }}
            ul {{
                margin-top: 4px;
                margin-bottom: 6px;
                padding-left: 18px;
            }}
            li {{
                margin-bottom: 3px;
                text-align: justify;
                font-size: 9.5pt;
                color: #334155;
            }}
            strong {{
                color: #0f172a;
            }}
        </style>
    </head>
    <body>
        {body_html}
    </body>
    </html>
    """
    return html_page

def generate_pdf_from_markdown(latex_code, doc_type="resume"):
    import subprocess
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "document.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
            
        try:
            # Run pdflatex twice to resolve references and page layouts
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "document.tex"],
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=15
                )
        except Exception as e:
            st.error(f"LaTeX compiler execution failed: {e}. Please ensure texlive-latex-base is installed on the host.")
            return None
            
        pdf_path = os.path.join(temp_dir, "document.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
        else:
            log_path = os.path.join(temp_dir, "document.log")
            log_content = ""
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                    log_content = lf.read()
            st.error("LaTeX compilation failed. See the pdflatex logs below:")
            st.text_area("pdflatex compiler log output", value=log_content[:5000], height=300)
            return None

# Trigger Generation API Flow
resume_content = st.session_state.get("resume_text", "")

if generate_btn:
    if not target_title or not target_company or not job_desc or not resume_content:
        st.error("Please fill out all required fields: Target Job Title, Company Name, Job Description, and upload a Candidate Resume.")
    else:
        try:
            with st.spinner("Resumey is optimizing your resume for ATS & formatting the cover letter..."):
                raw_response = call_llm_api(
                    st.session_state.api_provider,
                    target_title,
                    target_company,
                    job_desc,
                    resume_content
                )
                resume_output, letter_output = parse_outputs(raw_response)
                
                # Save results in state to persist across renders
                st.session_state["tailored_resume"] = resume_output
                st.session_state["tailored_letter"] = letter_output
                st.success("✓ Documents generated successfully! See tabs below.")
        except Exception as e:
            st.error(f"Generation Failed: {e}")

# Display Outputs if generated
if st.session_state.get("tailored_resume"):
    st.markdown("---")
    st.markdown("### 🏆 3. Output Documents")
    
    tab1, tab2, tab3 = st.tabs(["📄 Tailored Resume", "✉️ Tailored Cover Letter", "⚙️ Prompt Explorer"])
    
    with tab1:
        resume_tex = st.session_state["tailored_resume"]
        
        # Interactive Editor and Preview
        st.markdown("#### 📝 LaTeX Code Preview & Editor")
        edited_resume_tex = st.text_area("You can make quick edits directly in the LaTeX code below before exporting:", value=resume_tex, height=450, key="edit_resume_tex")
        
        # Compile and Download actions
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            st.download_button(
                label="📥 Download LaTeX Source (.tex)",
                data=edited_resume_tex,
                file_name="tailored_resume.tex",
                mime="text/x-tex",
                key="download_resume_tex",
                use_container_width=True
            )
        with act_col2:
            resume_pdf_data = generate_pdf_from_markdown(edited_resume_tex, doc_type="resume")
            if resume_pdf_data:
                st.download_button(
                    label="📥 Download PDF Document",
                    data=bytes(resume_pdf_data),
                    file_name="tailored_resume.pdf",
                    mime="application/pdf",
                    key="download_resume_pdf",
                    use_container_width=True
                )
            else:
                st.info("💡 Note: To print to PDF locally, make sure pdflatex is installed on your PATH. In production, Streamlit Cloud handles this automatically.")

    with tab2:
        letter_tex = st.session_state["tailored_letter"]
        
        # Interactive Editor and Preview
        st.markdown("#### 📝 LaTeX Code Preview & Editor")
        edited_letter_tex = st.text_area("You can make quick edits directly in the LaTeX code below before exporting:", value=letter_tex, height=450, key="edit_letter_tex")
        
        # Compile and Download actions
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            st.download_button(
                label="📥 Download LaTeX Source (.tex)",
                data=edited_letter_tex,
                file_name="tailored_cover_letter.tex",
                mime="text/x-tex",
                key="download_letter_tex",
                use_container_width=True
            )
        with act_col2:
            letter_pdf_data = generate_pdf_from_markdown(edited_letter_tex, doc_type="letter")
            if letter_pdf_data:
                st.download_button(
                    label="📥 Download PDF Document",
                    data=bytes(letter_pdf_data),
                    file_name="tailored_cover_letter.pdf",
                    mime="application/pdf",
                    key="download_letter_pdf",
                    use_container_width=True
                )
            else:
                st.info("💡 Note: To print to PDF locally, make sure pdflatex is installed on your PATH. In production, Streamlit Cloud handles this automatically.")

    with tab3:
        st.info("💡 Below is the exact prompt running behind the scenes. It sets the rules for ATS optimization, Canadian formatting, and strict truth preservation.")
        st.code(SYSTEM_PROMPT, language="markdown")
else:
    st.markdown("---")
    st.info("💡 Fill out the details in sections 1 and 2, then click Generate. Your tailored documents will appear here in clean print-ready white sheets.")
