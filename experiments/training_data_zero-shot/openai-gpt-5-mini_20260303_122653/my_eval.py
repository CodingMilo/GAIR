"""
Evaluation script template for benchmark testing.
"""
import re
import json


def extract_answer(response_content: str) -> dict:
    """
    Extract answer and reasoning from JSON response with fallback to regex.

    This function parses LLM responses to extract structured answers.
    Supports multiple formats:
    - JSON: {"answer": ["a"], "reasoning": "..."}
    - JSON with multiple answers: {"answer": ["a", "b", "c"], "reasoning": "..."}
    - Fallback regex for backward compatibility

    Args:
        response_content: Raw response content from LLM

    Returns:
        Dictionary with 'answer' and 'reasoning' keys
    """
    result = {"answer": "", "reasoning": ""}

    # FIX: Un-escape literal escape sequences before JSON parsing
    # Some LLMs return literal \n, \t, etc. instead of actual characters
    escape_map = {
        '\\n': '\n',   # Literal backslash-n -> newline
        '\\t': '\t',   # Literal backslash-t -> tab
        '\\r': '\r',   # Literal backslash-r -> carriage return
        '\\"': '"',    # Literal backslash-quote -> quote
    }

    for literal, actual in escape_map.items():
        response_content = response_content.replace(literal, actual)

    # First, try to parse the entire response as JSON
    # This handles cases where JSON is embedded in markdown code blocks
    try:
        cleaned_content = response_content.strip()
        if cleaned_content.startswith('```'):
            lines = cleaned_content.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].startswith('```'):
                lines = lines[:-1]
            cleaned_content = '\n'.join(lines).strip()

        data = json.loads(cleaned_content)
        answer_field = data.get('answer', [])
        reasoning_field = data.get('reasoning', '')

        if isinstance(answer_field, list):
            answers = [str(a).strip().lower() for a in answer_field if str(a).strip()]
            if answers:
                result["answer"] = ', '.join(answers)
        elif isinstance(answer_field, str):
            result["answer"] = answer_field.strip()

        result["reasoning"] = reasoning_field.strip()
        return result
    except (json.JSONDecodeError, AttributeError, KeyError):
        pass

    # Second attempt: Find ALL JSON objects and use the LAST valid one
    # This handles cases where LLM mentions answer format multiple times
    # The LAST valid JSON is most likely to be the final answer
    try:
        last_valid_result = None

        for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_content):
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
                if 'answer' in data:
                    answer_field = data.get('answer', [])
                    reasoning_field = data.get('reasoning', '')

                    extracted_answer = ""
                    if isinstance(answer_field, list):
                        answers = [str(a).strip().lower() for a in answer_field if str(a).strip()]
                        if answers:
                            extracted_answer = ', '.join(answers)
                    elif isinstance(answer_field, str):
                        extracted_answer = answer_field.strip()

                    last_valid_result = {
                        "answer": extracted_answer,
                        "reasoning": reasoning_field.strip()
                    }
            except json.JSONDecodeError:
                continue

        if last_valid_result and last_valid_result["answer"]:
            result["answer"] = last_valid_result["answer"]
            result["reasoning"] = last_valid_result["reasoning"]
            return result
    except Exception:
        pass

    # Fallback to regex extraction (backward compatibility)
    letters = re.findall(r'\[([a-zA-Z])\]', response_content)
    if letters:
        result["answer"] = ', '.join([l.lower() for l in letters])

    if '[Reason]' in response_content:
        parts = response_content.split('[Reason]')
        if len(parts) > 1:
            reason_part = parts[1].split('[Answer]')[0] if '[Answer]' in parts[1] else parts[1]
            result["reasoning"] = reason_part.strip()

    if not result["answer"] and '[Answer]' in response_content:
        after_answer = response_content.split('[Answer]')[-1]
        standalone = re.findall(r'\b([a-zA-Z])\b', after_answer)
        if standalone:
            result["answer"] = ', '.join([s.lower() for s in standalone[:5]])

    return result


def evaluate_question(
    question: str,
    client,  # OpenRouterClient instance
    model: str,
    config: dict
) -> dict:
    """
    Evaluate a single question with single LLM call.

    Args:
        question: Question text
        client: OpenRouterClient instance (same instance across all calls)
        model: Model name
        config: Full config dict (includes system_prompt loaded from system_prompt.md)

    Returns:
        {
            'raw_response': str,        # REQUIRED
            'extracted_answer': str,    # REQUIRED
            'script_executed': bool,    # REQUIRED (default False)
            'usage': dict,              # REQUIRED
            'metadata': dict            # OPTIONAL
        }
    """
    # Get prompt from config (loaded from system_prompt.md)
    prompt = """
    You will be given a CRE exam question. Do not reason and choose the correct answer(s) directly. At the end of your response, start a new line and output your answer as a JSON object with the following format:\n{\n\"answer\": [\"a\"] or [\"a\", \"b\", \"c\"] for multiple answers\n}\nFor example: {\"answer\": [\"a\"]} or {\"answer\": [\"a\", \"b\", \"c\"]}\n
"""

    # Single LLM call
    response = client.chat_completion(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ],
        temperature=config.get('temperature', 1.0),
        max_tokens=config.get('max_tokens'),
        max_reasoning_tokens=config.get('max_reasoning_tokens')
    )

    raw_response = response['choices'][0]['message']['content']

    # Extract answer from raw response
    parsed = extract_answer(raw_response)

    return {
        'raw_response': raw_response,
        'extracted_answer': parsed['answer'],
        'script_executed': False,
        'usage': response.get('usage', {}),
        'metadata': {
            'model': model,
            'finish_reason': response['choices'][0].get('finish_reason')
        }
    }
