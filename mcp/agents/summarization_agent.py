
import os
import asyncio
import json
from mcp.core.utils import gen_id
from mcp.core.context_handler import ContextHandler
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
from transformers import BitsAndBytesConfig
try:
    import openai
    from openai import OpenAI
except Exception:
    openai = None

with open('mcp/config/credentials.json') as f:
    creds = json.load(f)
os.environ["OPENAI_API_KEY"] = creds.get("openai_api_key", "")

def get_bart_model():
    if not hasattr(get_bart_model, "tokenizer") or not hasattr(get_bart_model, "model"):
        local_bart_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "bart_finetuned_meeting_summary"))
        get_bart_model.tokenizer = AutoTokenizer.from_pretrained(local_bart_path)
        get_bart_model.model = AutoModelForSeq2SeqLM.from_pretrained(local_bart_path)
        #print(f"[INFO] Loaded local BART model from {local_bart_path}")
    return get_bart_model.tokenizer, get_bart_model.model

def get_mistral_model():
    if not hasattr(get_mistral_model, "tokenizer") or not hasattr(get_mistral_model, "model"):
        local_mistral_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "mistral-7B-Instruct-v0.2"))
        if not os.path.exists(local_mistral_path):
            raise FileNotFoundError(f"Mistral model path not found: {local_mistral_path}")
        get_mistral_model.tokenizer = AutoTokenizer.from_pretrained(local_mistral_path)
        try:
            print("[INFO] Attempting to load Mistral in 4-bit quantized mode (bitsandbytes)...")
            get_mistral_model.model = AutoModelForCausalLM.from_pretrained(
                local_mistral_path,
                device_map="auto",
                load_in_4bit=True,
                quantization_config=BitsAndBytesConfig(load_in_4bit=True)
            )
            print("[INFO] Loaded Mistral in 4-bit quantized mode.")
        except Exception as e:
            print(f"[WARN] 4-bit quantization failed or bitsandbytes not available: {e}\nFalling back to normal model load.")
            get_mistral_model.model = AutoModelForCausalLM.from_pretrained(local_mistral_path)
    return get_mistral_model.tokenizer, get_mistral_model.model


class SummarizationAgent:
    def __init__(self, mode="auto"):
        """
        mode: "auto" (default) - use LLM if API key, else BART
              "llm"            - force LLM
              "bart"           - force BART
              "mistral"        - force local Mistral
        """
        self.context = ContextHandler()
        self.mode = mode

    async def summarize(self, meeting_id: str, transcript: str) -> dict:
        api_key = os.environ.get('OPENAI_API_KEY')
        print(f"SummarizationAgent: Using mode={self.mode}")
        #print(f"SummarizationAgent: OPENAI_API_KEY set: {bool(api_key)}")
        use_llm = (self.mode == "llm") or (self.mode == "auto" and api_key and openai)
        use_bart = (self.mode == "bart") or (self.mode == "auto" and not use_llm and self.mode != "mistral")
        use_mistral = (self.mode == "mistral") or (self.mode == "auto" and not use_llm and not use_bart)
        if use_llm:
            print("SummarizationAgent: Using LLM summarizer")
            prompt = (
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
                "  \"decisions\": [ {\"decision\": \"\", \"reason\": \"\", \"made_by\": \"\"} ],\n"
                "  \"action_items\": [ {\"task\": \"\", \"owner\": \"\", \"deadline\": \"\"} ],\n"
                "  \"risks\": [ {\"risk\": \"\", \"impact\": \"\", \"raised_by\": \"\"} ],\n"
                "  \"follow_up_questions\": [\"question 1\"]\n"
                "}\n"
                "\n"
                "TRANSCRIPT:\n"
                f"{transcript}\n"
            )
            print("[DEBUG][LLM] Prompt sent to LLM:\n", prompt[:1000], "..." if len(prompt) > 1000 else "")
            try:
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{'role':'user','content':prompt}],
                    max_tokens=300,
                    temperature=0.2
                )
                text = resp.choices[0].message.content
                print("[DEBUG][LLM] Raw LLM response:\n", text)
                summary_obj = {'meeting_id': meeting_id, 'summary_text': text}
            except Exception as e:
                print(f"[DEBUG][LLM] Exception during LLM summarization: {e}")
                summary_obj = {'meeting_id': meeting_id, 'summary_text': transcript[:300], 'note': str(e)}

        elif use_bart:
            print("SummarizationAgent: Using BART summarizer")
            tokenizer, model = get_bart_model()
            if not transcript or len(transcript.split()) < 10:
                bart_summary = "Transcript too short for summarization."
            else:
                try:
                    input_ids = tokenizer.encode(transcript, truncation=True, max_length=1024, return_tensors="pt")
                    summary_ids = model.generate(
                        input_ids,
                        max_length=130,
                        min_length=30,
                        do_sample=False,
                        num_beams=4,
                        early_stopping=True
                    )
                    bart_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                except Exception as e:
                    bart_summary = f"[BART summarization error: {e}]"
            # Improved rule-based extraction for action items and blockers
            lines = [l.strip() for l in transcript.replace('\n', '. ').split('.') if l.strip()]
            action_keywords = ['fix', 'complete', 'implement', 'create', 'update', 'assign', 'test', 'review', 'prepare', 'set up', 'ensure']
            blocker_keywords = ['block', 'blocked', 'delay', 'pending', 'cannot', 'issue', 'risk', 'concern']
            action_items = [l for l in lines if any(k in l.lower() for k in action_keywords)]
            blockers = [l for l in lines if any(k in l.lower() for k in blocker_keywords)]
            summary_obj = {
                'meeting_id': meeting_id,
                'summary_text': bart_summary,
                'action_items': action_items,
                'blockers': blockers
            }
        elif use_mistral:
            print("SummarizationAgent: Using local Mistral summarizer")
            mistral_tokenizer, mistral_model = get_mistral_model()
            if not transcript or len(transcript.split()) < 10:
                mistral_summary = "Transcript too short for summarization."
            else:
                try:
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
                        "  \"decisions\": [ {\"decision\": \"\", \"reason\": \"\", \"made_by\": \"\"} ],\n"
                        "  \"action_items\": [ {\"task\": \"\", \"owner\": \"\", \"deadline\": \"\"} ],\n"
                        "  \"risks\": [ {\"risk\": \"\", \"impact\": \"\", \"raised_by\": \"\"} ],\n"
                        "  \"follow_up_questions\": [\"question 1\"]\n"
                        "}\n"
                        "\n"
                        "TRANSCRIPT:\n"
                        f"{transcript}\n"
                    )
                    input_ids = mistral_tokenizer.encode(mistral_prompt, truncation=True, max_length=4096, return_tensors="pt")
                    summary_ids = mistral_model.generate(
                        input_ids,
                        max_new_tokens=512,
                        do_sample=False,
                        num_beams=4,
                        early_stopping=True
                    )
                    mistral_summary = mistral_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                except Exception as e:
                    mistral_summary = f"[Mistral summarization error: {e}]"
            summary_obj = {
                'meeting_id': meeting_id,
                'summary_text': mistral_summary
            }
        else:
            print("SummarizationAgent: No valid summarization method available.") 
            # Fallback: very basic extraction
            lines = [l.strip() for l in transcript.replace('\n', '. ').split('.') if l.strip()]
            action_keywords = ['fix', 'complete', 'implement', 'create', 'update', 'assign', 'test', 'review', 'prepare', 'set up', 'ensure']
            blocker_keywords = ['block', 'blocked', 'delay', 'pending', 'cannot', 'issue', 'risk', 'concern']
            summary_text = lines[0] if lines else ''
            action_items = [l for l in lines if any(k in l.lower() for k in action_keywords)]
            blockers = [l for l in lines if any(k in l.lower() for k in blocker_keywords)]
            summary_obj = {
                'meeting_id': meeting_id,
                'summary_text': summary_text,
                'action_items': action_items,
                'blockers': blockers
            }

        self.context.save_summary(meeting_id, summary_obj)
        await asyncio.sleep(0)
        return summary_obj
