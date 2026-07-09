// Initialize PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

// Application State
const state = {
    settings: {
        apiProvider: 'gemini-api',
        geminiKey: '',
        geminiModel: 'gemini-2.5-flash',
        ollamaHost: 'http://localhost:11434',
        ollamaModel: 'llama3',
        openaiUrl: '',
        openaiKey: '',
        openaiModel: ''
    },
    activeTab: 'resume-tab',
    resumeContent: '',
    coverLetterContent: '',
    isEditing: false
};

// System prompt as a constant to show in Explorer and feed the API
const SYSTEM_PROMPT = `You are a 30-year veteran Canadian HR Director and Executive Recruiter, expert in Applicant Tracking Systems (ATS) and hiring processes. Your task is to customize the candidate's resume and draft a tailored cover letter based on the provided Job Description (JD) and the candidate's current resume.

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
===LETTER_END===`;

// Helper to load settings from LocalStorage
function loadSettings() {
    const saved = localStorage.getItem('truenorth_tailor_settings');
    if (saved) {
        try {
            state.settings = { ...state.settings, ...JSON.parse(saved) };
        } catch (e) {
            console.error('Error parsing settings:', e);
        }
    }
    
    // Update settings DOM inputs
    document.getElementById('api-provider').value = state.settings.apiProvider;
    document.getElementById('gemini-key').value = state.settings.geminiKey || '';
    document.getElementById('gemini-model').value = state.settings.geminiModel;
    document.getElementById('ollama-host').value = state.settings.ollamaHost;
    document.getElementById('ollama-model').value = state.settings.ollamaModel;
    document.getElementById('openai-url').value = state.settings.openaiUrl || '';
    document.getElementById('openai-key').value = state.settings.openaiKey || '';
    document.getElementById('openai-model').value = state.settings.openaiModel || '';
    
    toggleProviderFields(state.settings.apiProvider);
}

// Helper to save settings to LocalStorage
function saveSettings() {
    state.settings.apiProvider = document.getElementById('api-provider').value;
    state.settings.geminiKey = document.getElementById('gemini-key').value.trim();
    state.settings.geminiModel = document.getElementById('gemini-model').value;
    state.settings.ollamaHost = document.getElementById('ollama-host').value.trim();
    state.settings.ollamaModel = document.getElementById('ollama-model').value.trim();
    state.settings.openaiUrl = document.getElementById('openai-url').value.trim();
    state.settings.openaiKey = document.getElementById('openai-key').value.trim();
    state.settings.openaiModel = document.getElementById('openai-model').value.trim();
    
    localStorage.setItem('truenorth_tailor_settings', JSON.stringify(state.settings));
}

// Toggle provider-specific fields in settings
function toggleProviderFields(provider) {
    document.querySelectorAll('.provider-fields').forEach(el => el.style.display = 'none');
    
    if (provider === 'gemini-api') {
        document.getElementById('provider-gemini-fields').style.display = 'block';
    } else if (provider === 'ollama-local') {
        document.getElementById('provider-ollama-fields').style.display = 'block';
    } else if (provider === 'openai-compatible') {
        document.getElementById('provider-openai-fields').style.display = 'block';
    }
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    
    // Inject prompt code into the Prompt Explorer tab
    document.getElementById('prompt-code').innerText = SYSTEM_PROMPT;
    
    // Event listeners
    document.getElementById('api-provider').addEventListener('change', (e) => {
        toggleProviderFields(e.target.value);
    });
    
    // Settings modal triggers
    const settingsModal = document.getElementById('settings-modal');
    document.getElementById('settings-btn').addEventListener('click', () => {
        settingsModal.style.display = 'flex';
    });
    
    document.getElementById('close-settings').addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });
    
    document.getElementById('cancel-settings').addEventListener('click', () => {
        loadSettings(); // revert changes
        settingsModal.style.display = 'none';
    });
    
    document.getElementById('save-settings').addEventListener('click', () => {
        saveSettings();
        settingsModal.style.display = 'none';
    });
    
    // Password toggles
    document.querySelectorAll('.toggle-password-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const inputId = this.getAttribute('data-input');
            const input = document.getElementById(inputId);
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fa-solid fa-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'fa-solid fa-eye';
            }
        });
    });

    // Close modal on background click
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    // Tab switcher
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active').style.display = 'none');
            
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            const pane = document.getElementById(tabId);
            pane.classList.add('active');
            pane.style.display = 'flex';
            
            state.activeTab = tabId;
        });
    });

    // File drag & drop + uploading
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileStatus = document.getElementById('file-status');
    const resumeTextarea = document.getElementById('resume-text');

    // Make drop zone clickable to select file
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A' && e.target.id !== 'file-input') {
            fileInput.click();
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleUploadedFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleUploadedFile(e.target.files[0]);
        }
    });

    async function handleUploadedFile(file) {
        fileStatus.textContent = `Reading ${file.name}...`;
        fileStatus.style.color = 'var(--text-secondary)';
        
        try {
            if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
                const text = await readFileAsText(file);
                resumeTextarea.value = text;
                fileStatus.textContent = `✓ Uploaded ${file.name} successfully`;
                fileStatus.style.color = 'var(--success)';
            } else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
                const result = await parsePDF(file);
                resumeTextarea.value = result.text;
                fileStatus.textContent = `✓ Uploaded and parsed ${file.name} (${result.numPages} pages)`;
                fileStatus.style.color = 'var(--success)';
            } else {
                fileStatus.textContent = '❌ Unsupported file type. Please upload a PDF or TXT file.';
                fileStatus.style.color = 'var(--accent)';
            }
        } catch (error) {
            console.error(error);
            fileStatus.textContent = `❌ Error: ${error.message}`;
            fileStatus.style.color = 'var(--accent)';
        }
    }

    function readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read text file.'));
            reader.readAsText(file);
        });
    }

    function parsePDF(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async function() {
                try {
                    const typedarray = new Uint8Array(this.result);
                    const loadingTask = pdfjsLib.getDocument(typedarray);
                    const pdf = await loadingTask.promise;
                    let fullText = '';
                    
                    for (let i = 1; i <= pdf.numPages; i++) {
                        const page = await pdf.getPage(i);
                        const textContent = await page.getTextContent();
                        const pageText = textContent.items.map(item => item.str).join(' ');
                        fullText += pageText + '\n\n';
                    }
                    resolve({ text: fullText, numPages: pdf.numPages });
                } catch (err) {
                    reject(new Error('Failed to parse PDF. The file might be scanned or corrupted.'));
                }
            };
            reader.onerror = (e) => reject(new Error('Failed to read PDF file binary.'));
            reader.readAsArrayBuffer(file);
        });
    }

    // Generate Button Click
    document.getElementById('generate-btn').addEventListener('click', startGeneration);
    
    // Action Buttons
    document.getElementById('edit-toggle-btn').addEventListener('click', toggleEditMode);
    document.getElementById('copy-btn').addEventListener('click', copyActiveDocument);
    document.getElementById('download-html-btn').addEventListener('click', downloadActiveAsHTML);
    document.getElementById('print-btn').addEventListener('click', printActiveDocument);
});

// Show/Hide Loading Overlay with status
function updateLoadingState(show, step = '') {
    const overlay = document.getElementById('loading-overlay');
    const stepText = document.getElementById('loading-step');
    const progressBar = document.getElementById('progress-bar');
    
    if (show) {
        overlay.style.display = 'flex';
        stepText.textContent = step;
        
        // Progress bar simulation steps
        if (step.includes('Analyzing')) progressBar.style.width = '20%';
        else if (step.includes('Connecting')) progressBar.style.width = '45%';
        else if (step.includes('Generating')) progressBar.style.width = '75%';
        else if (step.includes('Rendering')) progressBar.style.width = '95%';
    } else {
        overlay.style.display = 'none';
        progressBar.style.width = '0%';
    }
}

// Core Generation Logic
async function startGeneration() {
    const jobTitle = document.getElementById('target-title').value.trim();
    const company = document.getElementById('target-company').value.trim();
    const jdText = document.getElementById('job-desc').value.trim();
    const resumeText = document.getElementById('resume-text').value.trim();
    
    // Validations
    if (!jobTitle || !company || !jdText || !resumeText) {
        alert('Please fill out all required fields: Job Title, Company Name, Job Description, and Candidate Resume.');
        return;
    }
    
    // Check credentials based on provider
    const provider = state.settings.apiProvider;
    if (provider === 'gemini-api' && !state.settings.geminiKey) {
        alert('Please enter your Gemini API Key in the Settings panel (gear icon on the top right) to generate documents.');
        document.getElementById('settings-btn').click();
        return;
    }
    
    if (provider === 'openai-compatible' && (!state.settings.openaiUrl || !state.settings.openaiKey || !state.settings.openaiModel)) {
        alert('Please complete the Custom OpenAI API settings in the Settings panel before generating.');
        document.getElementById('settings-btn').click();
        return;
    }

    try {
        updateLoadingState(true, 'Analyzing job description and extracting ATS keywords...');
        
        // Simulate a slight delay for realistic processing feedback
        await new Promise(r => setTimeout(r, 1000));
        
        updateLoadingState(true, `Connecting to ${getProviderDisplayName(provider)}...`);
        
        const responseText = await callLLMAPI(provider, jobTitle, company, jdText, resumeText);
        
        updateLoadingState(true, 'Rendering customized documents...');
        
        parseAndSetOutputs(responseText);
        
        // Switch view from placeholder to actual outputs
        document.getElementById('placeholder-view').style.display = 'none';
        document.getElementById('resume-tab').style.display = 'flex';
        document.getElementById('cover-letter-tab').style.display = 'none';
        
        // Force reset output tabs UI
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector('[data-tab="resume-tab"]').classList.add('active');
        state.activeTab = 'resume-tab';
        
        // Show actions panel
        document.getElementById('output-actions').style.display = 'flex';
        
        updateLoadingState(false);
    } catch (error) {
        console.error(error);
        updateLoadingState(false);
        alert(`Generation Failed: ${error.message}\n\nCheck console log or settings configuration.`);
    }
}

function getProviderDisplayName(provider) {
    if (provider === 'gemini-api') return 'Google Gemini API';
    if (provider === 'ollama-local') return 'Ollama (Local LLM)';
    if (provider === 'openai-compatible') return 'Custom API';
    return 'LLM';
}

// API Call Routing
async function callLLMAPI(provider, jobTitle, company, jdText, resumeText) {
    const userPrompt = `Job Title: ${jobTitle}
Company: ${company}

JOB DESCRIPTION:
${jdText}

CANDIDATE CURRENT RESUME:
${resumeText}`;

    if (provider === 'gemini-api') {
        const apiKey = state.settings.geminiKey;
        const model = state.settings.geminiModel;
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [
                    {
                        parts: [
                            {
                                text: userPrompt
                            }
                        ]
                    }
                ],
                systemInstruction: {
                    parts: [
                        {
                            text: SYSTEM_PROMPT
                        }
                    ]
                },
                generationConfig: {
                    temperature: 0.3
                }
            })
        });
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error?.message || `Gemini API returned status ${response.status}`);
        }
        
        const data = await response.json();
        return data.candidates[0].content.parts[0].text;
    } 
    
    else if (provider === 'ollama-local') {
        const host = state.settings.ollamaHost.replace(/\/$/, ""); // trim trailing slash
        const model = state.settings.ollamaModel;
        const url = `${host}/api/generate`;
        
        updateLoadingState(true, `Connecting to local Ollama server at ${host}... (Model: ${model})`);
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: model,
                    prompt: SYSTEM_PROMPT + "\n\n" + userPrompt,
                    stream: false,
                    options: {
                        temperature: 0.3
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`Ollama server returned status ${response.status}`);
            }
            
            const data = await response.json();
            return data.response;
        } catch (err) {
            throw new Error(`Could not connect to Ollama. Make sure Ollama is running and OLLAMA_ORIGINS="*" environment variable is set to allow CORS. Details: ${err.message}`);
        }
    } 
    
    else if (provider === 'openai-compatible') {
        const baseUrl = state.settings.openaiUrl.replace(/\/$/, "");
        const apiKey = state.settings.openaiKey;
        const model = state.settings.openaiModel;
        const url = `${baseUrl}/chat/completions`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: model,
                messages: [
                    { role: 'system', content: SYSTEM_PROMPT },
                    { role: 'user', content: userPrompt }
                ],
                temperature: 0.3
            })
        });
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error?.message || `Custom API returned status ${response.status}`);
        }
        
        const data = await response.json();
        return data.choices[0].message.content;
    }
}

// Split the AI response into Resume and Cover Letter
function parseAndSetOutputs(rawText) {
    let resumeMarkdown = '';
    let letterMarkdown = '';
    
    // Strategy 1: Search for exact block delimiters
    const resumeStartIdx = rawText.indexOf('===RESUME_START===');
    const resumeEndIdx = rawText.indexOf('===RESUME_END===');
    const letterStartIdx = rawText.indexOf('===LETTER_START===');
    const letterEndIdx = rawText.indexOf('===LETTER_END===');
    
    if (resumeStartIdx !== -1 && resumeEndIdx !== -1) {
        resumeMarkdown = rawText.substring(resumeStartIdx + '===RESUME_START==='.length, resumeEndIdx).trim();
    }
    
    if (letterStartIdx !== -1 && letterEndIdx !== -1) {
        letterMarkdown = rawText.substring(letterStartIdx + '===LETTER_START==='.length, letterEndIdx).trim();
    }
    
    // Strategy 2: Fallback split if formatting tags are modified or stripped by LLM
    if (!resumeMarkdown || !letterMarkdown) {
        console.warn("Exact tags not found in response. Attempting regex split fallback.");
        const splitRegex = /(?:#+|=+)\s*(?:COVER\s*LETTER|LETTER|DEAR\s+HIRING)/i;
        const match = rawText.match(splitRegex);
        if (match) {
            const splitIdx = match.index;
            resumeMarkdown = rawText.substring(0, splitIdx).replace(/===RESUME_START===|===RESUME_END===/g, '').trim();
            letterMarkdown = rawText.substring(splitIdx).replace(/===LETTER_START===|===LETTER_END===/g, '').trim();
        } else {
            // Fallback 3: Dump everything in both, or split 50/50
            resumeMarkdown = rawText;
            letterMarkdown = rawText;
        }
    }
    
    // Save clean markdown in state
    state.resumeContent = resumeMarkdown;
    state.coverLetterContent = letterMarkdown;
    
    // Render markdown to preview divs
    renderDocuments();
}

function renderDocuments() {
    const resumePreview = document.getElementById('resume-preview');
    const letterPreview = document.getElementById('cover-letter-preview');
    
    // Setup marked parser configurations
    marked.setOptions({
        breaks: true,
        gfm: true
    });
    
    let renderedResume = marked.parse(state.resumeContent);
    let renderedLetter = marked.parse(state.coverLetterContent);
    
    // Post-process resume structure slightly to format experience rows beautifully in HTML
    renderedResume = formatResumeHTML(renderedResume);
    
    resumePreview.innerHTML = renderedResume;
    letterPreview.innerHTML = renderedLetter;
}

// HTML formatter to style Job Experience dates and locations perfectly in preview (following CSS)
function formatResumeHTML(html) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Let's find experience headings. We expect something like:
    // **Company Name** - City, Province
    // *Job Title* | Date - Date
    // We can search for paragraph nodes that look like dates, or search bold/italics
    // For general robustness, let's look for common patterns or let CSS handle it.
    // If we want to align company and date to the right, let's check for lines with '|' or dates.
    const paragraphs = tempDiv.querySelectorAll('p');
    paragraphs.forEach(p => {
        const text = p.innerText;
        // Check if this line looks like a job header: e.g. "Company - Location"
        if (p.querySelector('strong') && text.includes(' - ')) {
            // Check if next element is job title + date: e.g. "*Job Title* | Month Year"
            const next = p.nextElementSibling;
            if (next && next.tagName === 'P' && next.querySelector('em') && next.innerText.includes('|')) {
                // We can structure them into experience rows
                const companyStr = p.querySelector('strong').innerText;
                const locationMatch = text.split(' - ')[1];
                
                const titleStr = next.querySelector('em').innerText;
                const dateMatch = next.innerText.split('|')[1];
                
                const expHeader = document.createElement('div');
                expHeader.className = 'exp-row';
                expHeader.innerHTML = `<span>${companyStr}</span><span class="exp-location">${locationMatch || ''}</span>`;
                
                const titleHeader = document.createElement('div');
                titleHeader.className = 'exp-title-row';
                titleHeader.innerHTML = `<span>${titleStr}</span><span>${dateMatch ? dateMatch.trim() : ''}</span>`;
                
                p.replaceWith(expHeader);
                next.replaceWith(titleHeader);
            }
        }
    });
    
    return tempDiv.innerHTML;
}

// Action: Toggle Editable Mode
function toggleEditMode() {
    state.isEditing = !state.isEditing;
    const resumePreview = document.getElementById('resume-preview');
    const letterPreview = document.getElementById('cover-letter-preview');
    const btn = document.getElementById('edit-toggle-btn');
    const span = btn.querySelector('span');
    const icon = btn.querySelector('i');
    
    resumePreview.contentEditable = state.isEditing;
    letterPreview.contentEditable = state.isEditing;
    
    if (state.isEditing) {
        btn.classList.add('btn-accent');
        btn.classList.remove('btn-outline');
        span.textContent = 'Save Edits';
        icon.className = 'fa-solid fa-floppy-disk';
        // Add a border cue to the active preview
        document.getElementById(state.activeTab === 'resume-tab' ? 'resume-preview' : 'cover-letter-preview').focus();
    } else {
        btn.classList.remove('btn-accent');
        btn.classList.add('btn-outline');
        span.textContent = 'Edit';
        icon.className = 'fa-solid fa-pen-to-square';
        
        // Save current HTML edits back to state as markdown equivalents (or just keep the edited HTML)
        state.resumeContent = convertHtmlBackToMarkdown(resumePreview.innerHTML);
        state.coverLetterContent = convertHtmlBackToMarkdown(letterPreview.innerHTML);
        
        // Re-render to ensure clean formatting
        renderDocuments();
    }
}

// Rough HTML-to-markdown back-converter to update local state content
function convertHtmlBackToMarkdown(html) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Standard elements conversions
    // This is a simple parser. If editing in contenteditable, keeping the state sync isn't strictly necessary 
    // unless copying markdown, but it's good to keep it clean.
    let text = html;
    
    // For printing and copying, we can just extract direct outerText or content.
    // In our case, saving is simple: we let the DOM hold the edited text.
    return text;
}

// Action: Copy to Clipboard
function copyActiveDocument() {
    const isResume = state.activeTab === 'resume-tab';
    const previewEl = document.getElementById(isResume ? 'resume-preview' : 'cover-letter-preview');
    
    // Copy plain text content (without HTML tags)
    const textToCopy = previewEl.innerText;
    
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            alert(`${isResume ? 'Resume' : 'Cover Letter'} copied to clipboard!`);
        })
        .catch(err => {
            console.error('Copy failed:', err);
            alert('Failed to copy. Please select the text manually and press Ctrl+C.');
        });
}

// Action: Download HTML File
function downloadActiveAsHTML() {
    const isResume = state.activeTab === 'resume-tab';
    const previewEl = document.getElementById(isResume ? 'resume-preview' : 'cover-letter-preview');
    const title = document.getElementById('target-title').value || 'Document';
    const name = previewEl.querySelector('h1')?.innerText || 'Candidate';
    const filename = `${name.replace(/\s+/g, '_')}_Tailored_${isResume ? 'Resume' : 'Cover_Letter'}.html`;
    
    // HTML Wrapper with simple inline styling for standalone download
    const fullHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>${isResume ? 'Tailored Resume' : 'Tailored Cover Letter'} - ${name}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 40px;
            display: flex;
            justify-content: center;
        }
        .page {
            background-color: #ffffff;
            width: 100%;
            max-width: 800px;
            padding: 50px 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: #111;
            font-size: 11pt;
            line-height: 1.5;
        }
        h1 { text-align: center; font-size: 18pt; margin-bottom: 5px; }
        h2 { font-size: 12pt; text-transform: uppercase; border-bottom: 1.5px solid #222; padding-bottom: 2px; margin-top: 20px; margin-bottom: 10px; }
        h3 { font-size: 11pt; margin-top: 10px; margin-bottom: 5px; }
        p { margin-bottom: 10px; }
        ul { margin-bottom: 15px; padding-left: 20px; }
        li { margin-bottom: 5px; }
        .exp-row { display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 2px; }
        .exp-location { font-weight: normal; font-style: italic; color: #4b5563; }
        .exp-title-row { display: flex; justify-content: space-between; font-style: italic; margin-bottom: 8px; color: #374151; }
        .resume-header-info { text-align: center; font-size: 9.5pt; color: #4b5563; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="page">
        ${previewEl.innerHTML}
    </div>
</body>
</html>`;

    const blob = new Blob([fullHtml], { type: 'text/html' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Action: Print / PDF Export
function printActiveDocument() {
    const isResume = state.activeTab === 'resume-tab';
    const previewEl = document.getElementById(isResume ? 'resume-preview' : 'cover-letter-preview');
    const printContainer = document.getElementById('print-container');
    
    // Inject the inner content of the active tab preview
    printContainer.innerHTML = previewEl.innerHTML;
    
    // Trigger standard browser print which is configured to show ONLY the #print-container via CSS media-query
    window.print();
}
