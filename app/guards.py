import re
from typing import Tuple

# In-memory session tracking for rate limits
session_counters = {}

def check_rate_limit(session_id: str) -> Tuple[bool, str]:
    count = session_counters.get(session_id, 0)
    if count >= 20:
        return False, "Rate limit exceeded. You have made too many queries in this session."
    session_counters[session_id] = count + 1
    return True, ""

def scrub_pii(query: str) -> Tuple[bool, str, str]:
    # Basic PII checks
    # Email detection
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    # Aadhaar basic 12 digit match, Bank basic 9-18 digit match
    number_pattern = r'\b\d{9,18}\b'
    
    if re.search(email_pattern, query) or re.search(number_pattern, query):
        scrubbed = re.sub(email_pattern, '[EMAIL]', query)
        scrubbed = re.sub(number_pattern, '[CONFIDENTIAL_NUM]', scrubbed)
        return False, "PII detected and sanitized.", scrubbed
    
    return True, "", query

def check_prompt_injection(query: str) -> Tuple[bool, str]:
    lower_q = query.lower()
    injection_phrases = [
        "ignore your instructions", 
        "ignore previous", 
        "act as a different",
        "show me all documents",
        "bypass restrictions"
    ]
    for p in injection_phrases:
        if p in lower_q:
            return False, f"Prompt injection detected: '{p}' is not allowed."
    return True, ""

def check_off_topic(query: str) -> Tuple[bool, str]:
    # Can use an LLM or simple regex for off-topic
    lower_q = query.lower()
    # If it strongly asks about irrelevant themes like poem, cricket, etc.
    off_topic_keywords = ["write me a poem", "cricket score", "weather in", "recipe for"]
    for ot in off_topic_keywords:
        if ot in lower_q:
            return False, "Off-topic query detected. Please ask questions related to FinSolve's business domains."
    return True, ""

def validate_input(query: str, session_id: str) -> Tuple[bool, str, str]:
    # Rate Limit
    ok, msg = check_rate_limit(session_id)
    if not ok: return False, msg, query
    
    # Off Topic
    ok, msg = check_off_topic(query)
    if not ok: return False, msg, query
    
    # Prompt injection
    ok, msg = check_prompt_injection(query)
    if not ok: return False, msg, query
    
    # PII Scrubbing
    ok, msg, clean_query = scrub_pii(query)
    if not ok: return False, msg, clean_query # we actually just warn and alter the query, but we can pass it along
    
    return True, "", query

def validate_output(response: str, sources: list) -> Tuple[bool, str]:
    # Source citation enforcement
    # "If the response does not cite at least one source document and page number, append a warning"
    # Actually, the requirement says "append a warning to the user" if it doesn't cite.
    # We will check if the agent mentioned '[source]' or similar, or just check if 'sources' list is empty.
    
    warnings = []
    has_source = False
    
    # If the LLM has used the tool, it should cite it. For our simpler case, we trust the `sources` list
    # mapped during agent execution.
    if not sources and "financial" in response.lower():
         warnings.append("Potentially ungrounded: Output contains financial terms but no source was cited.")
    elif not sources:
         warnings.append("No source documents were cited for this response.")
         
    return len(warnings) == 0, " | ".join(warnings)
