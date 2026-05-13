import json
import os
import sys
from pathlib import Path

import google.generativeai as genai

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3-flash-preview")

# Load your bug template
with open(Path(__file__).parent / "bugs" / "bug-template.json") as f:
    bug_template = json.load(f)

def extract_bug_info(bug_report_text, bug_id=None):
    """Send bug report to Gemini and extract structured info, and ask clarifying questions if needed."""
    exclude_msg = ""
    if bug_id:
        exclude_msg = f"\nIMPORTANT: Do NOT include https://bugs.launchpad.net/bugs/{bug_id} in related_bugs (this is the current bug itself, not a related bug)."
    
    prompt = (
        "Extract bug information from the following bug report text and assess the completeness of the information. "
        "Fill in the JSON template fields as completely as possible. "
        "For missing information, use null values. "
        "For array fields (related_bugs, environment, steps_to_reproduce, logs, attachments), use empty arrays [] if no data is found. "
        "For related_bugs, only include OTHER bugs that this one relates to - do not include the bug itself."
        f"{exclude_msg}\n\n"
        "After extracting the information, evaluate whether the bug report contains enough information for triage. "
        "If critical information is missing (e.g., reproduction steps, expected vs actual results, environment details), "
        "generate a list of clarifying questions to ask the bug reporter.\n\n"
        f"Template structure:\n{json.dumps(bug_template, indent=2)}\n\n"
        f"Bug report:\n{bug_report_text}\n\n"
        "Respond with a JSON object containing:\n"
        "{\n"
        "  \"filled_template\": { ...the extracted bug data... },\n"
        "  \"is_complete\": true/false (is the information sufficient for triage?),\n"
        "  \"completeness_summary\": \"brief assessment of what information is available and what's missing\",\n"
        "  \"clarifying_questions\": [\"question 1?\", \"question 2?\", ...] (empty array if sufficient)\n"
        "}"
    )
    
    response = model.generate_content(prompt)
    try:
        # Extract JSON from response
        response_text = response.text
        # Try to parse as JSON
        extracted = json.loads(response_text)
        return extracted
    except json.JSONDecodeError:
        # If not valid JSON, try to extract JSON from the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"Could not parse Gemini response: {response_text}")

def format_bug_for_gemini(bug_dict):
    """Format a bug dict (from JSON) into text for Gemini."""
    text = f"""
Bug ID: {bug_dict['id']}
Title: {bug_dict['title']}
Status: {bug_dict['status']}
Importance: {bug_dict['importance']}
Assigned to: {bug_dict['assignee'] or 'Unassigned'}
URL: {bug_dict['web_link']}

Description:
{bug_dict['description'] or 'N/A'}
"""
    if bug_dict.get('messages'):
        text += f"\nComments ({len(bug_dict['messages'])}):\n"
        for msg in bug_dict['messages']:
            text += f"\n- {msg['owner_display_name']} ({msg['date_created']}):\n{msg['content']}\n"
    return text

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract bug info using Gemini")
    parser.add_argument("--input", type=str, default="bugs.json",
                        help="Input JSON file with bugs (default: bugs.json)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        print(f"\nFirst, run from the lp directory:")
        print(f"  uv run main.py --limit 5 --output ../bug-processor/bugs.json")
        sys.exit(1)
    
    # Load bugs from JSON
    with open(input_path, "r") as f:
        bugs = json.load(f)
    
    print(f"Loaded {len(bugs)} bugs. Processing with Gemini...\n")
    
    output_dir = Path("bug-processor/bugs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, bug in enumerate(bugs, 1):
        print(f"[{i}/{len(bugs)}] Processing bug #{bug['id']}: {bug['title']}")
        bug_text = format_bug_for_gemini(bug)
        try:
            result = extract_bug_info(bug_text, bug_id=bug['id'])
            
            # Prepare output
            is_complete = result.get("is_complete", True)
            summary = result.get("completeness_summary", "")
            questions = result.get("clarifying_questions", [])
            
            # Display status
            status = "✓ COMPLETE" if is_complete else "⚠ INCOMPLETE"
            print(f"  {status}")
            if summary:
                print(f"    Summary: {summary}")
            if questions:
                print(f"    Questions needed ({len(questions)}):")
                for q in questions:
                    print(f"      - {q}")
            
            # Save extracted bug (including template, completeness info, and questions)
            output_file = output_dir / f"bug-{bug['id']}.json"
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"    Saved to {output_file}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
