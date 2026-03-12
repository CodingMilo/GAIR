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
import subprocess
from pathlib import Path
import sys
import threading

# Ensure the scripts directory is in path for imports
scripts_dir = str(Path(__file__).parent)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# ─── Tool Calling: Python math execution ─────────────────────────────────────
# Tool definition passed to the LLM via OpenRouter's tools API.
_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_python_math",
            "description": (
                "Execute Python code for precise mathematical calculations. "
                "Use this whenever the question involves numerical computation: "
                "Weibull, Poisson, exponential distribution, MTBF/MTTF, chi-squared, "
                "F-distribution, binomial, confidence intervals, or any reliability formula. "
                "Available libraries: math, numpy (as np), scipy.stats, scipy.special. "
                "The code MUST print the result to stdout."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Valid Python code that prints the final result. "
                            "Example: 'import math; print(math.exp(-1.5))'. "
                            "Do NOT use file system, network, or OS operations."
                        )
                    }
                },
                "required": ["code"]
            }
        }
    }
]

# Patterns that must not appear in submitted code (security guard)
_BLOCKED_CODE_PATTERNS = (
    'import os', 'import sys', 'import subprocess', 'import socket',
    'import urllib', 'import requests', 'import pathlib', 'import shutil',
    'import ctypes', 'import pickle', 'from os', 'from sys',
    '__import__', 'open(', 'exec(', 'eval(', 'compile(',
    'os.', 'sys.', 'subprocess.',
)


def run_python_code(code: str, timeout: int = 5) -> str:
    """Execute Python math code safely in a subprocess with timeout.

    Blocks dangerous imports/operations. Only allows mathematical computation.

    Args:
        code: Python code string to execute (must print result to stdout).
        timeout: Maximum execution time in seconds (default 5).

    Returns:
        stdout output on success, or an error message string.
    """
    code_lower = code.lower()
    for blocked in _BLOCKED_CODE_PATTERNS:
        if blocked in code_lower:
            return (
                f"Error: Blocked operation '{blocked}'. "
                "Only math/numpy/scipy libraries are allowed."
            )

    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if proc.returncode == 0:
            output = proc.stdout.strip()
            if output:
                return output
            return (
                "The code executed successfully but produced no output. "
                "Did you forget to use print()?"
            )
        else:
            return f"Error: {proc.stderr.strip()[:500]}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (5 s limit)."
    except Exception as exc:
        return f"Error: {exc}"

try:
    from rag import RAGEngine
except ImportError:
    # Fallback for different execution contexts
    import scripts.rag as rag
    RAGEngine = rag.RAGEngine

# Global RAG instance to persist across calls
# We store it in sys to survive module re-execution by BenchmarkRunner
_rag_init_lock = threading.Lock()


def _rag_cache_signature(config) -> tuple:
    """Build a cache signature so RAG is rebuilt only when relevant inputs change."""
    rag_path = config.get('rag_tex_path') if isinstance(config, dict) else getattr(config, 'rag_tex_path', None)
    embedding_model = config.get('embedding_model') if isinstance(config, dict) else getattr(config, 'embedding_model', None)
    resolved_path = Path(rag_path) if rag_path else (Path(__file__).parent / "rag.tex")
    try:
        mtime_ns = resolved_path.stat().st_mtime_ns if resolved_path.exists() else None
    except OSError:
        mtime_ns = None
    return (str(resolved_path), mtime_ns, embedding_model)


def _fewshot_cache_signature(config) -> tuple:
    """Build a cache signature so few-shot embeddings are rebuilt only when needed."""
    train_path = config.get('train_path') if isinstance(config, dict) else getattr(config, 'train_path', None)
    embedding_model = config.get('embedding_model') if isinstance(config, dict) else getattr(config, 'embedding_model', None)
    resolved_path = Path(train_path) if train_path else (Path(__file__).parent.parent / "data" / "train.csv")
    try:
        mtime_ns = resolved_path.stat().st_mtime_ns if resolved_path.exists() else None
    except OSError:
        mtime_ns = None
    return (str(resolved_path), mtime_ns, embedding_model)

def get_rag_engine(client, config):
    # Double-checked locking: avoid re-init under concurrent parallel workers.
    desired_signature = _rag_cache_signature(config)
    current_signature = getattr(sys, "_gair_rag_engine_signature", None)
    if (not hasattr(sys, "_gair_rag_engine")) or current_signature != desired_signature:
        with _rag_init_lock:
            current_signature = getattr(sys, "_gair_rag_engine_signature", None)
            if (not hasattr(sys, "_gair_rag_engine")) or current_signature != desired_signature:
                print("Initializing RAG Engine (first time)...")
                engine = RAGEngine(client, config)
                engine.prepare_embeddings()
                setattr(sys, "_gair_rag_engine", engine)
                setattr(sys, "_gair_rag_engine_signature", desired_signature)
    return getattr(sys, "_gair_rag_engine")


# ---------------------------------------------------------------------------
# FEW-SHOT: retrieve similar training Q&A pairs using cosine similarity
# ---------------------------------------------------------------------------
_fewshot_lock = threading.Lock()


def _log(message: str) -> None:
    """Emit a timestamped log line that flushes immediately to the terminal."""
    from datetime import datetime

    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {message}", flush=True)

def get_fewshot_cache(client, config):
    """Build and cache the few-shot embedding store from train.csv."""
    desired_signature = _fewshot_cache_signature(config)
    current_signature = getattr(sys, "_gair_fewshot_cache_signature", None)
    if (not hasattr(sys, "_gair_fewshot_cache")) or current_signature != desired_signature:
        with _fewshot_lock:
            current_signature = getattr(sys, "_gair_fewshot_cache_signature", None)
            if (not hasattr(sys, "_gair_fewshot_cache")) or current_signature != desired_signature:
                import pandas as pd
                import numpy as np
                from sklearn.metrics.pairwise import cosine_similarity

                train_path = config.get('train_path')
                if not train_path or not Path(train_path).exists():
                    # Try default location relative to this script
                    train_path = Path(__file__).parent.parent / "data" / "train.csv"
                else:
                    train_path = Path(train_path)

                if not train_path.exists():
                    _log("[FewShot] train.csv not found; disabling few-shot cache.")
                    setattr(sys, "_gair_fewshot_cache", None)
                    setattr(sys, "_gair_fewshot_cache_signature", desired_signature)
                    return None

                df = pd.read_csv(train_path)
                _log(f"[FewShot] Building embedding cache for {len(df)} training questions...")
                embeddings = []
                total = len(df)
                for index, (_, row) in enumerate(df.iterrows(), start=1):
                    emb = client.get_embedding(str(row['question']))
                    embeddings.append(emb if emb else [0.0] * 1536)
                    if index == 1 or index == total or index % 10 == 0:
                        _log(f"[FewShot] Embedded {index}/{total} training questions")
                cache = {
                    "df": df,
                    "embeddings": np.array(embeddings, dtype=np.float32)
                }
                _log("[FewShot] Embedding cache ready.")
                setattr(sys, "_gair_fewshot_cache", cache)
                setattr(sys, "_gair_fewshot_cache_signature", desired_signature)
    return getattr(sys, "_gair_fewshot_cache")


def get_fewshot_examples(question: str, client, config, k: int = 3) -> str:
    """Return k most similar training Q&A pairs as a formatted few-shot block."""
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    cache = get_fewshot_cache(client, config)
    if cache is None:
        return ""

    q_emb = client.get_embedding(question)
    if not q_emb:
        return ""

    q_vec = np.array(q_emb, dtype=np.float32).reshape(1, -1)
    sims = cosine_similarity(q_vec, cache["embeddings"])[0]

    current_question_id = config.get('current_question_id')
    current_question_text = str(config.get('current_question_text') or question).strip()
    current_question_norm = " ".join(current_question_text.lower().split())

    candidate_indices = []
    for idx, row in cache["df"].iterrows():
        row_qid = row.get('question_id') if hasattr(row, 'get') else None
        row_question_norm = " ".join(str(row['question']).strip().lower().split())
        same_id = current_question_id is not None and row_qid == current_question_id
        same_text = row_question_norm == current_question_norm
        if same_id or same_text:
            continue
        candidate_indices.append(idx)

    if not candidate_indices:
        return ""

    ranked_candidates = sorted(candidate_indices, key=lambda idx: sims[idx], reverse=True)
    top_k_idx = ranked_candidates[:k]

    examples = []
    for idx in top_k_idx:
        row = cache["df"].iloc[idx]
        examples.append(
            f"Example question:\n{row['question']}\n"
            f"Correct answer: {row['answer']}\n"
        )
    return (
        "--- SIMILAR SOLVED EXAMPLES (from training set) ---\n"
        + "\n".join(examples)
        + "-----------------------------------------------------\n\n"
    )


def evaluate_question(
    question: str,
    client,  # OpenRouterClient instance
    model: str,
    config: dict
) -> dict:
    """
    Evaluate a single question with an optional self-critique second pass.
    Supports RAG, few-shot examples from training data, and self-critique.
    """
    # 1. Get Context from RAG
    rag_k = config.get('rag_k', 2)
    rag_tex_path = config.get('rag_tex_path')
    rag = get_rag_engine(client, config) if rag_tex_path else None
    context = rag.get_context(question, k=rag_k) if rag else ""

    # 2. Optional few-shot examples from training data
    fewshot_block = ""
    if config.get('use_fewshot'):
        fewshot_block = get_fewshot_examples(
            question, client, config, k=config.get('fewshot_k', 3)
        )

    # 3. Prepare system prompt and user content
    use_tools = config.get('use_tool_calling', False)
    use_json_format = config.get('use_json_format', False)

    system_prompt = config.get('system_prompt') or (
        "You are a Senior Certified Reliability Engineer (CRE). "
        "Reason step by step in plain text, then end with one final JSON object on the last non-empty line. "
        "The final JSON must contain available_options, reasoning, and selected_letter."
        if use_json_format else
        "You are a Senior Certified Reliability Engineer (CRE). "
        "Answer the multiple-choice question clearly and precisely."
    )

    user_content_parts = []
    if fewshot_block:
        user_content_parts.append(fewshot_block)
    if context:
        user_content_parts.append(
            f"--- BACKGROUND KNOWLEDGE FROM CRE MANUAL ---\n{context}\n"
            "---------------------------------------------\n\n"
        )
    user_content_parts.append(f"QUESTION:\n{question}")
    user_content = "".join(user_content_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    # ── Usage accumulator (shared by all LLM calls inside this function) ──────
    total_usage = {
        'cost': 0.0,
        'total_tokens': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'reasoning_tokens': 0,
        'cached_tokens': 0,
        'request_count': 0,
    }

    def _accumulate(resp: dict) -> None:
        u = resp.get('usage', {}) or {}
        total_usage['cost'] += u.get('cost', 0.0) or 0.0
        total_usage['total_tokens'] += u.get('total_tokens', 0) or 0
        total_usage['prompt_tokens'] += u.get('prompt_tokens', 0) or 0
        total_usage['completion_tokens'] += u.get('completion_tokens', 0) or 0
        total_usage['reasoning_tokens'] += (
            (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
        )
        total_usage['cached_tokens'] += (
            (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
        )
        total_usage['request_count'] += 1

    first_call_extra = {}
    if use_tools:
        first_call_extra['tools'] = _TOOL_DEFINITIONS

    response = client.chat_completion(
        model=model,
        messages=messages,
        temperature=config.get('temperature', 1.0),
        max_tokens=config.get('max_tokens') or 600,
        max_reasoning_tokens=config.get('max_reasoning_tokens'),
        **first_call_extra
    )
    _accumulate(response)

    # ── Tool-calling agentic loop (max 4 additional rounds = 5 total) ─────────
    if use_tools:
        for _tool_round in range(4):
            _choice = response['choices'][0]
            _msg = _choice['message']
            _finish = _choice.get('finish_reason', '')
            _tool_calls = _msg.get('tool_calls') or []

            if _finish != 'tool_calls' or not _tool_calls:
                break  # Model gave final text answer — exit loop

            # Add the assistant turn (including tool_calls) to history
            messages.append(_msg)

            # Execute each requested tool and append tool results
            for tc in _tool_calls:
                fn_name = (tc.get('function') or {}).get('name', '')
                fn_args_raw = (tc.get('function') or {}).get('arguments', '{}')
                try:
                    fn_args = json.loads(fn_args_raw)
                except json.JSONDecodeError:
                    fn_args = {}

                if fn_name == 'execute_python_math':
                    tool_result = run_python_code(fn_args.get('code', ''))
                else:
                    tool_result = f"Unknown tool '{fn_name}'."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get('id', ''),
                    "content": tool_result
                })

            # Follow-up call: keep offering tools and allow free-form reasoning
            # followed by a final JSON block.
            follow_extra = {'tools': _TOOL_DEFINITIONS}

            response = client.chat_completion(
                model=model,
                messages=messages,
                temperature=config.get('temperature', 1.0),
                max_tokens=config.get('max_tokens') or 600,
                max_reasoning_tokens=config.get('max_reasoning_tokens'),
                **follow_extra
            )
            _accumulate(response)

    raw_response = response['choices'][0]['message'].get('content') or ""
    reasoning = response['choices'][0]['message'].get('reasoning') or ""
    if not raw_response.strip() and reasoning.strip():
        raw_response = reasoning

    finish_reason = response['choices'][0].get('finish_reason', '')

    # 4b. Truncation recovery: if the model hit max_tokens or produced no valid
    #     trailing JSON answer, ask again for reasoning + final JSON.
    if finish_reason == 'length' or not extract_answer(raw_response).get('answer'):
        recovery_instruction = (
            "Continue the reasoning if needed, then end with exactly one valid JSON object on the last non-empty line. "
            "Use this schema exactly for the final line: "
            "{\"available_options\": {\"a\": \"...\", \"b\": \"...\", \"c\": \"...\", \"d\": \"...\"}, "
            "\"reasoning\": \"short direct reasoning\", "
            "\"selected_letter\": \"a\"}. "
            "Do not output anything after that final JSON line."
            if use_json_format else
            "State your final answer clearly."
        )
        recovery_messages = messages + [
            {"role": "assistant", "content": raw_response},
            {
                "role": "user",
                "content": recovery_instruction
            }
        ]
        recovery_resp = client.chat_completion(
            model=model,
            messages=recovery_messages,
            temperature=0.0,
            max_tokens=config.get('max_tokens') or 512,
            max_reasoning_tokens=None,
        )
        recovery_text = recovery_resp['choices'][0]['message'].get('content') or ""
        if recovery_text.strip():
            raw_response = raw_response + "\n" + recovery_text
        _accumulate(recovery_resp)

    # 5. Optional self-critique second pass
    if config.get('use_self_critique') and raw_response.strip():
        first_answer = extract_answer(raw_response).get('answer', '')
        critique_instruction = (
            f"Your current selected_letter is: {first_answer or '(unclear)'}\n\n"
            "Review the reasoning for common CRE pitfalls and verify the option mapping against available_options. "
            "You may explain the correction in plain text, but you must end with exactly one valid JSON object on the last non-empty line, using the same schema: "
            "{\"available_options\": {\"a\": \"...\", \"b\": \"...\", \"c\": \"...\", \"d\": \"...\"}, "
            "\"reasoning\": \"short direct reasoning\", "
            "\"selected_letter\": \"a\"}."
            if use_json_format else
            (
                f"Your current answer is: {first_answer or '(unclear)'}\n\n"
                "Review your reasoning for these common CRE exam pitfalls:\n"
                "- Instantaneous vs. cumulative failure rates\n"
                "- Series vs. parallel system configurations\n"
                "- MTBF vs. MTTF confusion\n"
                "- Scope of maintenance/lifecycle cost definitions\n"
                "- Censored vs. complete data in Weibull estimation\n"
                "- Confidence interval vs. hypothesis test framing\n\n"
                "If you find an error, state the corrected answer. If your answer is correct, confirm it."
            )
        )
        critique_messages = messages + [
            {"role": "assistant", "content": raw_response},
            {
                "role": "user",
                "content": critique_instruction
            }
        ]
        critique_response = client.chat_completion(
            model=model,
            messages=critique_messages,
            temperature=0.2,
            max_tokens=config.get('max_tokens') or 512,
            max_reasoning_tokens=config.get('max_reasoning_tokens'),
        )
        critique_text = critique_response['choices'][0]['message'].get('content') or ""
        crit_reasoning = critique_response['choices'][0]['message'].get('reasoning') or ""
        if not critique_text.strip() and crit_reasoning.strip():
            critique_text = crit_reasoning

        if critique_text.strip():
            raw_response = raw_response + "\n\n[SELF-CRITIQUE]\n" + critique_text

        _accumulate(critique_response)

    # 6. Extract answer (from the full combined response — self-critique answer wins via Priority 1)
    parsed = extract_answer(raw_response)
    answer_extracted = parsed['answer']

    return {
        'raw_response': raw_response,
        'extracted_answer': answer_extracted,
        'usage': total_usage,
        'metadata': {
            'model': model,
            'finish_reason': response['choices'][0].get('finish_reason'),
            'used_fewshot': bool(fewshot_block),
            'used_self_critique': bool(config.get('use_self_critique')),
        }
    }


def extract_answer(response_content: str) -> dict:
    """
    Extract answer and reasoning from JSON objects only.

    This function ignores all non-JSON text and only trusts parsed JSON blocks.
    Priority is given to the strict selected_letter schema used by deep_think_json.

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

    decoder = json.JSONDecoder()

    # First, try to parse the entire response as JSON.
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

        # Priority: strict selected_letter schema.
        if 'selected_letter' in data:
            letter = str(data.get('selected_letter', '')).strip().lower()
            if letter and len(letter) == 1 and letter.isalpha():
                result["answer"] = letter
                result["reasoning"] = str(data.get('reasoning', '')).strip()
                return result

    except (json.JSONDecodeError, AttributeError, KeyError):
        pass

    # Second attempt: scan the text and keep the last valid JSON object.
    # This supports "reasoning first, final JSON at the end".
    try:
        last_valid_result = None

        for idx, char in enumerate(response_content):
            if char != '{':
                continue
            try:
                data, end_idx = decoder.raw_decode(response_content[idx:])
                if not isinstance(data, dict):
                    continue
                if 'selected_letter' in data:
                    letter = str(data.get('selected_letter', '')).strip().lower()
                    if letter and len(letter) == 1 and letter.isalpha():
                        last_valid_result = {
                            "answer": letter,
                            "reasoning": str(data.get('reasoning', '')).strip()
                        }
            except json.JSONDecodeError:
                continue

        if last_valid_result and last_valid_result["answer"]:
            result["answer"] = last_valid_result["answer"]
            result["reasoning"] = last_valid_result["reasoning"]
            return result
    except Exception:
        pass

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
