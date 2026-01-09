import os
import re
import json

TRANSCRIPTS_DIR = "data/transcripts"
SUMMARIES_DIR = "data/summaries"

if not os.path.exists(SUMMARIES_DIR):
    os.makedirs(SUMMARIES_DIR)

def extract_json_block(text):
    """
    Extracts a JSON block that follows a marker (e.g., **JSON Summary Output:** or ---) in the text.
    Returns the JSON string if found, else None.
    """
    # Find the marker (**JSON Summary Output:** or ---)
    # Line-by-line search for marker
    lines = text.splitlines()
    marker_idx = None
    for idx, line in enumerate(lines):
        if "json summary" in line.lower():
            marker_idx = idx
            print(f"[DEBUG] Marker found at line {idx}: {repr(line)}")
            break
    # If no marker, look for first ```json code block
    if marker_idx is None:
        print("[DEBUG] No marker found in any line. Searching for first ```json code block.")
        block_start = None
        block_end = None
        for idx, line in enumerate(lines):
            if line.strip().startswith("```json"):
                block_start = idx
                break
        if block_start is not None:
            for idx in range(block_start+1, len(lines)):
                if lines[idx].strip().startswith("```"):
                    block_end = idx
                    break
        if block_start is not None and block_end is not None:
            json_lines = lines[block_start+1:block_end]
            json_text = '\n'.join(json_lines)
            # Find first '{' and extract JSON block using brace matching
            brace_count = 0
            start_pos = json_text.find('{')
            for i in range(start_pos, len(json_text)):
                if json_text[i] == '{':
                    brace_count += 1
                elif json_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        print(f"[DEBUG] JSON block extracted from {start_pos} to {i+1}")
                        return json_text[start_pos:i+1]
            print("[DEBUG] No matching closing brace found for JSON block in code block.")
            return None
        print("[DEBUG] No ```json code block found.")
        return None
    # Find code block marker (``` or ```json) after marker
    codeblock_idx = None
    for idx in range(marker_idx+1, len(lines)):
        if lines[idx].strip().startswith("```"):
            codeblock_idx = idx
            print(f"[DEBUG] Code block marker found at line {idx}: {repr(lines[idx])}")
            break
    if codeblock_idx is not None:
        # Find first '{' after code block marker
        json_start = None
        for idx in range(codeblock_idx+1, len(lines)):
            if '{' in lines[idx]:
                json_start = idx
                brace_pos = lines[idx].find('{')
                break
        if json_start is None:
            print("[DEBUG] No opening brace found after code block marker.")
            return None
        # Extract JSON block using brace matching
        json_text = '\n'.join(lines[json_start:])
        start_pos = json_text.find('{')
    else:
        # No code block marker, find first '{' after marker line
        print("[DEBUG] No code block marker found after marker. Searching for '{' after marker line.")
        json_start = None
        for idx in range(marker_idx+1, len(lines)):
            if '{' in lines[idx]:
                json_start = idx
                break
        if json_start is None:
            print("[DEBUG] No opening brace found after marker line.")
            return None
        json_text = '\n'.join(lines[json_start:])
        start_pos = json_text.find('{')
    # Extract JSON block using brace matching
    brace_count = 0
    for i in range(start_pos, len(json_text)):
        if json_text[i] == '{':
            brace_count += 1
        elif json_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                print(f"[DEBUG] JSON block extracted from {start_pos} to {i+1}")
                return json_text[start_pos:i+1]
    print("[DEBUG] No matching closing brace found for JSON block.")
    return None

def main():
    count = 1
    for filename in os.listdir(TRANSCRIPTS_DIR):
        if filename.endswith(".txt"):
            transcript_path = os.path.abspath(os.path.join(TRANSCRIPTS_DIR, filename))
            print(f"Processing file: {transcript_path}")
            with open(transcript_path, "r", encoding="utf-8") as f:
                content = f.read()

            json_block = extract_json_block(content)
            if json_block:
                try:
                    summary_data = json.loads(json_block)
                    # Replace _transcript_ with _summary_ for output file
                    if "_transcript_" in filename:
                        summary_filename = filename.replace("_transcript_", "_summary_").replace(".txt", ".json")
                    else:
                        summary_filename = os.path.splitext(filename)[0] + ".json"
                    summary_path = os.path.join(SUMMARIES_DIR, summary_filename)
                    with open(summary_path, "w", encoding="utf-8") as sf:
                        json.dump(summary_data, sf, indent=2, ensure_ascii=False)
                    # Remove the JSON block from the transcript
                    content = content.replace(json_block, "")
                    # Remove the entire summary section (marker, optional backticks, and JSON block), even if JSON is empty
                    marker_pattern = re.compile(r'(\*\*JSON Summary(?: Output)?\*\*:?|---)', re.MULTILINE)
                    marker_match = marker_pattern.search(content)
                    if marker_match:
                        marker_start = marker_match.start()
                        # Try to find the first '{' after the marker
                        brace_start = content.find('{', marker_match.end())
                        if brace_start != -1:
                            # Find the matching closing '}'
                            brace_count = 0
                            for i in range(brace_start, len(content)):
                                if content[i] == '{':
                                    brace_count += 1
                                elif content[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        # Optionally include trailing triple backticks and whitespace
                                        after_json = content[json_end:]
                                        backtick_match = re.match(r'\s*```.*', after_json)
                                        if backtick_match:
                                            json_end += backtick_match.end()
                                        # Remove from marker_start to json_end
                                        content = content[:marker_start] + content[json_end:]
                                        break
                        else:
                            # No JSON, just remove marker and any following code block
                            after_marker = content[marker_match.end():]
                            codeblock_match = re.match(r'\s*```(?:json)?\s*```', after_marker)
                            if codeblock_match:
                                codeblock_end = marker_match.end() + codeblock_match.end()
                                content = content[:marker_start] + content[codeblock_end:]
                    with open(transcript_path, "w", encoding="utf-8") as f:
                        f.write(content.strip() + "\n")
                    print(f"Processed: {filename}")
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    print(f"Extracted JSON block from {filename} was:\n{json_block}\n---END JSON BLOCK---")
            else:
                # Even if no JSON, still remove empty summary marker/code block
                marker_pattern = re.compile(r'(\*\*JSON Summary(?: Output)?\*\*:?|---)', re.MULTILINE)
                marker_match = marker_pattern.search(content)
                if marker_match:
                    marker_start = marker_match.start()
                    after_marker = content[marker_match.end():]
                    # Match any code block (```json ... ``` or ``` ... ```), even if empty
                    codeblock_match = re.match(r'\s*```(?:json)?[ \t]*\n[\s\S]*?```', after_marker)
                    if codeblock_match:
                        codeblock_end = marker_match.end() + codeblock_match.end()
                        content = content[:marker_start] + content[codeblock_end:]
                    else:
                        # If no code block, just remove the marker line
                        content = content[:marker_start] + content[marker_match.end():]
                    with open(transcript_path, "w", encoding="utf-8") as f:
                        f.write(content.strip() + "\n")
                    print(f"Processed: {filename}")
                else:
                    print(f"No JSON summary found in: {filename}")
           
    print("Batch processing complete.")

if __name__ == "__main__":
    main()