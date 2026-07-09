import streamlit as st
import requests
import json
import os
import re
import markdown
from pypdf import PdfReader

# Page Configuration
st.set_page_config(
    page_title="TrueNorth Tailor 🍁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants & Paths
SETTINGS_FILE = "local_settings.json"

# Master System Prompt
SYSTEM_PROMPT = """You are a 30-year veteran Canadian HR Director and Executive Recruiter, expert in Applicant Tracking Systems (ATS) and hiring processes. Your task is to customize the candidate's resume and draft a tailored cover letter based on the provided Job Description (JD) and the candidate's current resume.

### RULES FOR CUSTOMIZING THE RESUME:
1. STRICT TRUTH (NO HALLUCINATIONS): 
   - Do NOT invent any companies, degrees, dates, certifications, or achievements.
   - If the candidate does not have a skill or has not worked in a specific role/industry, do not add it.
   - If you need to write an achievement but the candidate's resume lacks a numeric metric, do NOT invent numbers (like "increased sales by 45%"). Instead, use a placeholder in brackets like "[X]%" or "[Number]" so the candidate knows to insert their actual data, or focus on a strong qualitative achievement (e.g., "Spearheaded the migration of the core platform, resulting in improved system stability and reduced loading times").
2. CANADIAN FORMATTING STANDARDS:
   - Header: Include Name, Phone, Email, LinkedIn Profile URL, and City & Province/Territory (e.g., "Toronto, ON" or "Calgary, AB"). NEVER include full street addresses, photos, age, gender, marital status, nationality, or visa statuses (for privacy and human rights compliance).
   - Professional Summary: Write a punchy, value-driven paragraph (3-4 sentences) highlighting the candidate's years of relevant experience, core expertise, and key value proposition for this specific role. Do NOT use an Objective statement.
   - Core Competencies / Key Skills: A bulleted list of exactly 6 to 9 key skills matched to keywords in the JD. Group them if necessary, but keep it clean.
   - Professional Experience: Reverse-chronological order.
     - Company Name, Location (City, Province/Country), Job Title, Dates (formatted as "Month Year - Month Year" or "Present").
     - Under each role, bullet points starting with strong action verbs. Ensure past tense for past roles, and present tense for current roles.
     - Use the CAR framework (Challenge, Action, Result) for bullet points where possible to show impact, not just a list of daily responsibilities.
   - Education: List degree/diploma, major, school name, and city/province.
   - No References: Do not include "References available upon request" (it is outdated and assumed in Canada).
3. ATS OPTIMIZATION:
   - Identify critical keywords, technical skills, and tools in the Job Description and integrate them naturally into the Professional Summary, Core Competencies, and Professional Experience sections.
   - Keep the structure clean and simple. Avoid tables, columns, text boxes, headers/footers, and graphics which confuse ATS scanners.

### RULES FOR WRITING THE COVER LETTER:
1. CANADIAN BUSINESS LETTER FORMAT:
   - Include Candidate's contact info, Date, and Recipient Info (if name is missing, use "Hiring Manager" or "Recruiting Team" at "[Company]").
   - Include a clear Subject line: "RE: [Job Title] - Reference/Job ID [if any]".
2. STRUCTURE & CONTENT:
   - Opening: Hook the reader by mentioning the job title, company, and why you are excited to apply. Mention why their mission/culture aligns with you.
   - Body Paragraph 1 (Why You): Connect your core background directly to the top 2-3 key challenges or requirements outlined in the JD.
   - Body Paragraph 2 (Evidence of Success): Highlight 1-2 major achievements from your resume that prove your capacity to solve the company's pain points. Keep achievements true to the resume content.
   - Closing: Reiterate your enthusiasm, state your desire for an interview to discuss how your skills match their needs, and sign off professionally ("Sincerely," followed by the candidate's name).
3. LENGTH: Keep the cover letter concise, fitting comfortably on a single page (under 400 words).

### OUTPUT FORMAT:
You MUST output the customized resume and the cover letter in a single response, separated by the exact tags below so the application can split and display them correctly.

Format the output exactly as follows:

===RESUME_START===
# [CANDIDATE NAME]
[City, Province] | [Phone] | [Email] | [LinkedIn]

## PROFESSIONAL SUMMARY
[Summary Text...]

## CORE COMPETENCIES
- [Skill 1] | [Skill 2] | [Skill 3]
- [Skill 4] | [Skill 5] | [Skill 6]
- [Skill 7] | [Skill 8] | [Skill 9]

## PROFESSIONAL EXPERIENCE
**[Company Name]** - [City, Province/Country]
*[Job Title]* | [Month Year] - [Month Year or Present]
- [Achievement bullet 1 starting with active verb]
- [Achievement bullet 2 starting with active verb]

## EDUCATION
**[Degree Name] in [Major]**
[University/Institution Name], [City, Province/Country] | [Graduation Year]
===RESUME_END===

===LETTER_START===
[Candidate Name]
[City, Province] | [Phone] | [Email] | [LinkedIn]

[Current Date]

Hiring Committee
[Company Name]
[Company Address or City, Province]

**RE: Application for [Job Title]**

Dear Hiring Committee,

[Cover Letter Body...]

Sincerely,

[Candidate Name]
===LETTER_END=== """

# Settings management (storing credentials locally on disk)
def load_local_settings():
    default_settings = {
        "api_provider": "gemini-api",
        "gemini_key": "",
        "gemini_model": "gemini-2.5-flash",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3",
        "openai_url": "",
        "openai_key": "",
        "openai_model": ""
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
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
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        .stTabs,
        .print-btn-wrapper,
        button,
        header,
        .main > div:first-child {
            display: none !important;
        }
        
        .print-only-container {
            display: block !important;
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            background: white !important;
            color: black !important;
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
        <h1>TrueNorth Tailor</h1>
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
        st.selectbox("Model", options=["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-pro"], key="gemini_model")
        
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

# Trigger Generation API Flow
resume_content = st.session_state.get("resume_text", "")

if generate_btn:
    if not target_title or not target_company or not job_desc or not resume_content:
        st.error("Please fill out all required fields: Target Job Title, Company Name, Job Description, and upload a Candidate Resume.")
    else:
        try:
            with st.spinner("TrueNorth Tailor is optimizing your resume for ATS & formatting the cover letter..."):
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
    
    tab1, tab2, tab3 = st.tabs(["📄 Tailored Resume", "✉️ Cover Letter", "⚙️ Prompt Explorer"])
    
    with tab1:
        resume_md = st.session_state["tailored_resume"]
        
        # Download and copy actions
        act_col1, act_col2, act_col3 = st.columns([1, 1, 3])
        with act_col1:
            st.download_button(
                label="📥 Download Markdown",
                data=resume_md,
                file_name="tailored_resume.md",
                mime="text/markdown",
                use_container_width=True
            )
        with act_col2:
            html_doc = f"<html><body style='font-family: Arial; padding: 40px;'>{markdown.markdown(resume_md)}</body></html>"
            st.download_button(
                label="📥 Download HTML",
                data=html_doc,
                file_name="tailored_resume.html",
                mime="text/html",
                use_container_width=True
            )
        with act_col3:
            # Inline JS trick for a browser native print trigger
            st.markdown("""
            <div class="print-btn-wrapper">
                <button onclick="window.print()" class="stButton" style="width: 100%; height: 35px; border-radius: 8px; border: 1px solid #0ea5e9; background-color: transparent; color: #0ea5e9; font-weight: 600; cursor: pointer;">
                    🖨️ Print / Save as PDF
                </button>
            </div>
            """, unsafe_allow_html=True)

        # White paper render preview
        st.markdown("<br>", unsafe_allow_html=True)
        processed_resume_md = format_resume_markdown(resume_md)
        resume_html = markdown.markdown(processed_resume_md)
        
        st.markdown(f"""
        <div class="paper-wrapper">
            <div class="document-paper resume-style">
                {resume_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Render a hidden print-only block that window.print() will display
        st.markdown(f"""
        <div class="print-only-container">
            <div class="document-paper resume-style" style="box-shadow: none !important; padding: 0 !important;">
                {resume_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        letter_md = st.session_state["tailored_letter"]
        
        act_col1, act_col2, act_col3 = st.columns([1, 1, 3])
        with act_col1:
            st.download_button(
                label="📥 Download Markdown",
                data=letter_md,
                file_name="tailored_cover_letter.md",
                mime="text/markdown",
                use_container_width=True
            )
        with act_col2:
            html_letter = f"<html><body style='font-family: Georgia; padding: 40px; line-height: 1.5;'>{markdown.markdown(letter_md)}</body></html>"
            st.download_button(
                label="📥 Download HTML",
                data=html_letter,
                file_name="tailored_cover_letter.html",
                mime="text/html",
                use_container_width=True
            )
        with act_col3:
            st.markdown("""
            <div class="print-btn-wrapper">
                <button onclick="window.print()" class="stButton" style="width: 100%; height: 35px; border-radius: 8px; border: 1px solid #0ea5e9; background-color: transparent; color: #0ea5e9; font-weight: 600; cursor: pointer;">
                    🖨️ Print / Save as PDF
                </button>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        letter_html = markdown.markdown(letter_md)
        
        st.markdown(f"""
        <div class="paper-wrapper">
            <div class="document-paper letter-paper">
                {letter_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Render a hidden print-only block that window.print() will display
        st.markdown(f"""
        <div class="print-only-container">
            <div class="document-paper letter-paper" style="box-shadow: none !important; padding: 0 !important;">
                {letter_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.info("💡 Below is the exact prompt running behind the scenes. It sets the rules for ATS optimization, Canadian formatting, and strict truth preservation.")
        st.code(SYSTEM_PROMPT, language="markdown")
else:
    st.markdown("---")
    st.info("💡 Fill out the details in sections 1 and 2, then click Generate. Your tailored documents will appear here in clean print-ready white sheets.")
