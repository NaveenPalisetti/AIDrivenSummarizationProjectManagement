import re
import json
import torch

def summarize_with_mistral(mistral_tokenizer, mistral_model, transcript, meeting_id):
    if not transcript or len(transcript.split()) < 10:
        print("[Mistral] Transcript too short for summarization.")
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
    print("[Mistral] Prompt sent to model (first 500 chars):\n", mistral_prompt[:500], "..." if len(mistral_prompt) > 500 else "")
    device = next(mistral_model.parameters()).device
    print(f"[Mistral] Model device: {device}")
    encoded = mistral_tokenizer.encode_plus(
        mistral_prompt,
        truncation=True,
        max_length=4096,
        return_tensors="pt"
    )
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    print(f"[Mistral] input_ids shape: {input_ids.shape}, attention_mask shape: {attention_mask.shape}")
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
    print("[Mistral] Raw model output (first 500 chars):\n", mistral_output[:500], "..." if len(mistral_output) > 500 else "")
    print("[Mistral] Full decoded output:\n", mistral_output)
    # Remove prompt/instructions/transcript if present in output
    # Try to extract only the JSON block or the part after the JSON block
    # Extract only the first valid JSON object (handle extra data after JSON)
    def extract_first_json(text):
        brace_count = 0
        start = None
        for i, c in enumerate(text):
            if c == '{':
                if brace_count == 0:
                    start = i
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0 and start is not None:
                    return text[start:i+1]
        return None

    json_str = extract_first_json(mistral_output)
    if json_str:
        print("[Mistral] JSON block found in output.")
        try:
            parsed = json.loads(json_str)
            summary_text = parsed.get('summary', [])
            action_items = parsed.get('action_items', [])
            print(f"[Mistral] Parsed summary: {summary_text}")
            print(f"[Mistral] Parsed action_items: {action_items}")
        except Exception as e:
            print(f"[Mistral] JSON parsing error: {e}")
            summary_text = []
            action_items = []
    else:
        print("[Mistral] No JSON block found in output.")
        # Try to heuristically remove prompt/instructions if model echoed them
        # Look for first bullet or numbered list after the prompt
        summary_text = []
        action_items = []
        lines = mistral_output.splitlines()
        summary_started = False
        for line in lines:
            l = line.strip()
            if l.startswith('-') or l.startswith('1.') or l.startswith('•'):
                summary_started = True
            if summary_started and l:
                summary_text.append(l)
        if not summary_text:
            summary_text = [mistral_output.strip()]
    return {
        'meeting_id': meeting_id,
        'summary_text': summary_text,
        'action_items': action_items
    }
