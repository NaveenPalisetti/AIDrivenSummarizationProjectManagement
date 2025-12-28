"""
Task extraction logic (rule-based + spaCy NER) for MCP Streamlit App
"""
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_action_items(text):
    # Stricter keywords and minimum length
    KEYWORDS = [
        'fix', 'complete', 'implement', 'create', 'update', 'assign', 'test', 'review',
        'submit', 'send', 'finalize', 'schedule', 'prepare', 'organize', 'resolve', 'follow up', 
        'investigate', 'analyze', 'plan', 'report', 'document', 'deploy', 'release', 'approve', 
        'check', 'remind', 'contact', 'arrange', 'discuss', 'share', 'provide', 'finish', 
        'deliver', 'coordinate', 'monitor', 'track', 'evaluate', 'confirm', 'notify', 
        'inform', 'respond', 'attend', 'present', 'update', 'assign', 'review', 'test', 
        'implement', 'fix', 'complete', 'create'
    ]
    lines = [l.strip() for l in text.split('.') if l.strip()]
    actions = []
    for l in lines:
        # Must contain a keyword and be at least 6 words
        if any(k in l.lower() for k in KEYWORDS) and len(l.split()) >= 6:
            actions.append(l)
    return actions

def extract_task_details(sentence):
    doc = nlp(sentence)
    owners = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    deadlines = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    return {
        "task": sentence,
        "owners": owners,
        "deadlines": deadlines
    }

def extract_tasks_from_transcript(transcript):
    action_items = extract_action_items(transcript)
    tasks_extracted = []
    for a in action_items:
        details = extract_task_details(a)
        if details:
            tasks_extracted.append(details)
    return tasks_extracted
