"""
Evaluation script template for benchmark testing.

REQUIRED OUTPUTS:
==================
The evaluate_question() function MUST return a dictionary with these fields:

    {
        'raw_response': str,        # REQUIRED - Complete LLM response text (stored in run_N_results.json)
        'extracted_answer': str,    # REQUIRED - Final answer extracted from response (becomes prediction_{run_idx} column in solution.csv)
        'usage': dict,              # REQUIRED - API usage metadata (tracks costs and tokens)
        'metadata': dict            # OPTIONAL - Any additional information you want to log
    }

FIELD USAGE:
============
- raw_response: Stored in run_N_results.json for debugging and analysis
- extracted_answer: Used to create prediction columns in solution.csv for evaluation
- usage: Per-question usage calculated as difference in client.get_usage_summary() before/after API call
- metadata: Optional field for any additional logging (e.g., model version, finish_reason)

IMPORTANT NOTES:
================
- extracted_answer must be the final answer, not intermediate reasoning
- For multiple-choice questions, return comma-separated lowercase letters (e.g., "a,b,c")
- The system will compare extracted_answer against ground truth for accuracy calculation
- usage field is calculated as difference in client.get_usage_summary() before and after API call
- Missing required fields will cause the benchmark to fail
"""
import re
import json
from pathlib import Path


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
            'usage': dict,              # REQUIRED
            'metadata': dict            # OPTIONAL
        }
    """
    # Get prompt from config (loaded from system_prompt.md)
    prompt = """
    You will be given a CRE exam question. Do not reason, and answer directly. Limit your answer to 600 words maximum. At the end of your response, start a new line and output your answer as a JSON object with the following format:\n{\n\"answer\": [\"a\"] or [\"a\", \"b\", \"c\"] for multiple answers\n}\nFor example: {\"answer\": [\"a\"]} or {\"answer\": [\"a\", \"b\", \"c\"]}\n Output only the json, and nothing else.
 """

    # Get usage summary before API call
    usage_before = client.get_usage_summary()

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

    # Get usage summary after API call
    usage_after = client.get_usage_summary()

    raw_response = response['choices'][0]['message']['content']

    # Extract answer from raw response
    parsed = extract_answer(raw_response)
    answer_extracted = parsed['answer']

    # Calculate per-question usage as difference
    total_usage = {
        'cost': usage_after['cumulative_cost'] - usage_before['cumulative_cost'],
        'total_tokens': usage_after['total_tokens'] - usage_before['total_tokens'],
        'prompt_tokens': usage_after['total_prompt_tokens'] - usage_before['total_prompt_tokens'],
        'completion_tokens': usage_after['total_completion_tokens'] - usage_before['total_completion_tokens'],
        'reasoning_tokens': usage_after['total_reasoning_tokens'] - usage_before['total_reasoning_tokens'],
        'cached_tokens': usage_after['total_cached_tokens'] - usage_before['total_cached_tokens'],
        'request_count': usage_after['request_count'] - usage_before['request_count']
    }

    return {
        'raw_response': raw_response,
        'extracted_answer': answer_extracted,
        'usage': total_usage,
        'metadata': {
            'model': model,
            'finish_reason': response['choices'][0].get('finish_reason')
        }
    }


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


if __name__ == '__main__':
    """
    Test mode for development and validation.
    
    This allows you to test evaluate_question() with a single question
    without running the full benchmark. Useful for:
    - Testing your evaluation logic
    - Verifying answer extraction works correctly
    - Debugging API calls
    - Validating output format
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from supporting_scripts import OpenRouterClient
    
    # Mock configuration for testing
    test_config = {
        'temperature': 1.0,
        'max_tokens': 4096,
        'max_reasoning_tokens': None
    }
    
    # Test question (single-choice CRE question)
    test_question = """
    Which of the following is a key principle of the COSO ERM framework?

    A) Risk assessment is optional for mature organizations
    B) Risk management should be integrated with business strategy
    C) Only financial risks need to be considered
    D) Risk response is the responsibility of external auditors only
    
    Choose the correct answer.
    """
    
    # Initialize client (uses OPENROUTER_API_KEY from environment)
    print("=" * 80)
    print("EVALUATION SCRIPT TEST MODE")
    print("=" * 80)
    print("Testing evaluate_question() with a single question...")
    print()
    
    # Check if API key is available
    import os
    if not os.getenv('OPENROUTER_API_KEY'):
        raise KeyError('Must have a valid openrouter key!')
    else:
        client = OpenRouterClient()
        test_model = "openai/gpt-4o-mini"  # Use a real model for testing
        using_mock = False
    
    try:
        result = evaluate_question(
            question=test_question,
            client=client,
            model=test_model,
            config=test_config
        )
        
        # Verify required fields
        required_fields = ['raw_response', 'extracted_answer', 'usage']
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"[FAILED] Missing required fields: {missing_fields}")
            sys.exit(1)
        
        # Display results
        print("[SUCCESS] All required fields present")
        print()
        print("RESULTS:")
        print("-" * 80)
        print(f"Extracted Answer: {result['extracted_answer']}")
        print(f"Usage: {result['usage']}")
        print(f"Metadata: {result.get('metadata', {})}")
        print()
        print("Raw Response:")
        print("-" * 80)
        print(result['raw_response'][:500])  # Show first 500 chars
        if len(result['raw_response']) > 500:
            print("... (truncated)")
        print("-" * 80)
        print()
        if using_mock:
            print("[SUCCESS] Test passed! (Mock mode - no API call made)")
            print("To test with real API, set OPENROUTER_API_KEY environment variable")
        else:
            print("[SUCCESS] Test passed! Your evaluation script is ready for benchmarking.")
        
    except Exception as e:
        print(f"[FAILED] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
