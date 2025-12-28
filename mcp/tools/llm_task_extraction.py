"""
LLM-based Task Extraction Tool for MCP
Outputs tasks in Jira issue format using a local BART model.
"""


from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

MODEL_PATH = "models/bart_finetuned_meeting_summary"
_tokenizer = None
_model = None
_pipe = None

def get_llm_pipeline():
    global _tokenizer, _model, _pipe
    if _pipe is None or _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        _model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
        _pipe = pipeline("text-generation", model=_model, tokenizer=_tokenizer, device=-1)
    return _tokenizer, _model, _pipe

def extract_tasks_jira_format(transcript):
    tokenizer, model, pipe = get_llm_pipeline()
    # --- Original code commented for reference ---
    # Build prompt
    # prompt = (
    #     "Extract all action items or tasks from the following meeting transcript. "
    #     "For each, output in Jira issue format as strictly as possible, one after another, with each field on its own line.\n"
    #     "- Summary: <short summary>\n"
    #     "- Description: <detailed description>\n"
    #     "- Assignee: <person, if mentioned>\n"
    #     "- Due Date: <date, if mentioned>\n"
    #     "Transcript:\n"
    #     f"{transcript}\n"
    #     "Tasks:"
    # )
    # max_length = getattr(model.config, 'max_position_embeddings', 1024)
    # prompt_token_allowance = max_length - 128  # leave room for output tokens
    # input_ids = tokenizer.encode(prompt, truncation=True, max_length=prompt_token_allowance)
    # print(f"[DEBUG] Truncated input token length: {len(input_ids)}, Model max: {max_length}")
    # truncated_prompt = tokenizer.decode(input_ids, skip_special_tokens=True)
    # result = pipe(truncated_prompt, max_new_tokens=128, temperature=0.3)
    # print("RAW OUTPUT:", result)
    # output_text = result[0]['generated_text']
    # def parse_tasks(text):
    #     tasks = []
    #     current_task = {}
    #     for line in text.splitlines():
    #         line = line.strip()
    #         if line.startswith('- Summary:'):
    #             if current_task:
    #                 tasks.append(current_task)
    #                 current_task = {}
    #             current_task['Summary'] = line[len('- Summary:'):].strip()
    #         elif line.startswith('- Description:'):
    #             current_task['Description'] = line[len('- Description:'):].strip()
    #         elif line.startswith('- Assignee:'):
    #             current_task['Assignee'] = line[len('- Assignee:'):].strip()
    #         elif line.startswith('- Due Date:'):
    #             current_task['Due Date'] = line[len('- Due Date:'):].strip()
    #     if current_task:
    #         tasks.append(current_task)
    #     return tasks
    # tasks = parse_tasks(output_text)
    # return tasks  # List of dicts, each representing a task

    # --- New, faster version for CPU ---
    prompt = (
        "Extract up to 3 action items or tasks from the following meeting transcript. "
        "For each, output in Jira issue format as strictly as possible, one after another, with each field on its own line.\n"
        "- Summary: <short summary>\n"
        "- Description: <detailed description>\n"
        "- Assignee: <person, if mentioned>\n"
        "- Due Date: <date, if mentioned>\n"
        "Transcript:\n"
        f"{transcript}\n"
        "Tasks:"
    )
    max_length = getattr(model.config, 'max_position_embeddings', 1024)
    prompt_token_allowance = max_length - 32  # leave more room for output tokens
    input_ids = tokenizer.encode(prompt, truncation=True, max_length=prompt_token_allowance)
    print(f"[DEBUG] Truncated input token length: {len(input_ids)}, Model max: {max_length}")
    truncated_prompt = tokenizer.decode(input_ids, skip_special_tokens=True)
    result = pipe(truncated_prompt, max_new_tokens=32, temperature=0.3)
    print("RAW OUTPUT:", result)
    output_text = result[0]['generated_text']

    def parse_tasks(text):
        tasks = []
        current_task = {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('- Summary:'):
                if current_task:
                    tasks.append(current_task)
                    current_task = {}
                current_task['Summary'] = line[len('- Summary:'):].strip()
            elif line.startswith('- Description:'):
                current_task['Description'] = line[len('- Description:'):].strip()
            elif line.startswith('- Assignee:'):
                current_task['Assignee'] = line[len('- Assignee:'):].strip()
            elif line.startswith('- Due Date:'):
                current_task['Due Date'] = line[len('- Due Date:'):].strip()
        if current_task:
            tasks.append(current_task)
        return tasks

    tasks = parse_tasks(output_text)
    return tasks  # List of dicts, each representing a task

if __name__ == "__main__":
    transcript = "Your transcript text here..."
    print(extract_tasks_jira_format(transcript))