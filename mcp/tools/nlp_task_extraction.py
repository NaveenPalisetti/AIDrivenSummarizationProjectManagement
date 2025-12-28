import spacy
from typing import List, Dict
import re
import datetime

# Load spaCy English model (make sure to install: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

def extract_tasks_nlp(transcript: str) -> List[Dict]:
    """
    Extract action items from a transcript using classical NLP (spaCy).
    Returns a list of dicts in Jira-style format: {title, owner, due, description}
    """
    tasks = []
    doc = nlp(transcript)
    for sent in doc.sents:
        # Heuristic: look for imperative verbs or sentences with action keywords
        sent_text = sent.text.strip()
        if not sent_text:
            continue
        # Simple action keyword/verb check
        action_keywords = ["action", "todo", "task", "assign", "complete", "finish", "follow up", "review", "update", "send", "schedule", "prepare", "submit", "finalize", "share", "remind"]
        if any(kw in sent_text.lower() for kw in action_keywords) or sent.root.tag_ == "VB":
            # Try to extract owner (named entity or pronoun)
            owner = None
            for ent in sent.ents:
                if ent.label_ in ["PERSON"]:
                    owner = ent.text
                    break
            # Fallback: look for pronouns (e.g., "You", "John")
            if not owner:
                for token in sent:
                    if token.pos_ == "PRON" and token.text.lower() != "i":
                        owner = token.text
                        break
            # Try to extract due date with context
            due = None
            deadline_keywords = ["by", "before", "due", "deadline", "on", "until"]
            for ent in sent.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    # Check if the date/time is near a deadline keyword
                    ent_start = ent.start_char
                    ent_end = ent.end_char
                    window = 20  # chars before/after entity to check for keyword
                    context_start = max(0, ent_start - window)
                    context_end = min(len(sent.text), ent_end + window)
                    context = sent.text[context_start:context_end].lower()
                    if any(kw in context for kw in deadline_keywords):
                        due = ent.text
                        break
            # Title: use the sentence, or try to extract main verb phrase
            title = sent_text
            # Leave description blank
            description = ""
            # Set default due date if not found: last day of this week (Sunday)
            if due is None:
                today = datetime.date.today()
                days_until_sunday = 6 - today.weekday() if today.weekday() < 6 else 0
                end_of_week = today + datetime.timedelta(days=days_until_sunday)
                due = end_of_week.isoformat()
            tasks.append({
                "title": title,
                "owner": owner,
                "due": due
            })
    # Return only the top 3 most important tasks (first 3 found)
    return tasks[:3]
