import re
import json
import torch

def summarize_with_mistral(mistral_tokenizer, mistral_model, transcript, meeting_id):
    if not transcript or len(transcript.split()) < 10:
        return {
            'meeting_id': meeting_id,
            'summary_text': "Transcript too short for summarization.",
            'action_items': []
        }
    mistral_prompt = (
        "You are an AI specialized in analyzing meeting transcripts.\n"
        "Your task is to produce:\n"
        "1. A clear and concise SUMMARY of the meeting.\n"
        "2. A list of ACTION ITEMS with owners and deadlines if mentioned.\n"
        "3. A list of DECISIONS made during the meeting.\n"
        "4. A list of RISKS, blockers, or concerns raised.\n"
        "5. A list of FOLLOW-UP QUESTIONS that attendees should clarify.\n"
        "\n"
        "INSTRUCTIONS:\n"
        "- Read the provided meeting transcript thoroughly.\n"
        "- Do NOT invent information. Only extract what is explicitly or implicitly present.\n"
        "- If some sections have no information, return an empty list.\n"
        "- Keep summary short but complete (5–8 bullet points).\n"
        "- Use simple, business-friendly language.\n"
        "\n"
        "RETURN THE OUTPUT IN THIS EXACT JSON FORMAT:\n"
        "{\n"
        "  \"summary\": [\"point 1\", \"point 2\"],\n"
        "  \"action_items\": [ {\"task\": \"\", \"owner\": \"\", \"deadline\": \"\"} ]\n"
        "}\n"
        "\n"
        "TRANSCRIPT:\n"
        f"{transcript}\n"
    )
    device = next(mistral_model.parameters()).device
    encoded = mistral_tokenizer.encode_plus(
        mistral_prompt,
        truncation=True,
        max_length=4096,
        return_tensors="pt"
    )
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    summary_ids = mistral_model.generate(
        input_ids,
        attention_mask=attention_mask,
        max_new_tokens=512,
        do_sample=False,
        num_beams=4,
        early_stopping=True,
        pad_token_id=mistral_tokenizer.eos_token_id
    )
    mistral_output = mistral_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    json_match = re.search(r'\{.*\}', mistral_output, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            summary_text = parsed.get('summary', [])
            action_items = parsed.get('action_items', [])
        except Exception:
            summary_text = mistral_output
            action_items = []
    else:
        summary_text = mistral_output
        action_items = []
    return {
        'meeting_id': meeting_id,
        'summary_text': summary_text,
        'action_items': action_items
    }
