"""
Standalone experiment runner for quick iteration on hard questions.
Runs multiple configs, prints accuracy, and saves a summary CSV.

Usage:
    python scripts/run_experiments.py
"""
import sys
import os
import json
import time
import importlib.util
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from supporting_scripts import OpenRouterClient
from supporting_scripts.openrouter_client import GlobalRateLimiter

# ─── Hard question IDs (0% accuracy on Trinity baseline) ───────────────────
HARD_IDS = [7, 9, 10, 11, 16, 17, 19, 24, 25, 26, 29, 34, 35, 39, 45, 47]

# ─── Experiment configs to test ─────────────────────────────────────────────
EXPERIMENTS = [
    # Broad multi-model screen with one comparable baseline.
    {
        "name": "gpt41mini|precise+RAG+t0.3",
        "model": "openai/gpt-4.1-mini",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "gpt5mini|precise+RAG+t0.3",
        "model": "openai/gpt-5-mini",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "gemini3flash|precise+RAG+t0.3",
        "model": "google/gemini-3-flash-preview",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "qwen235b|precise+RAG+t0.3",
        "model": "qwen/qwen3-235b-a22b-2507",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "mistrallarge|precise+RAG+t0.3",
        "model": "mistralai/mistral-large-2512",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "grokfast|precise+RAG+t0.3",
        "model": "x-ai/grok-4.1-fast",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "deepseekv32|precise+RAG+t0.3",
        "model": "deepseek/deepseek-v3.2",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 700,
        "temperature": 0.3,
    },
    # Parameter variations on likely strong candidates / distinct behaviors.
    {
        "name": "gpt5mini|precise+RAG+t0.0",
        "model": "openai/gpt-5-mini",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.0,
    },
    {
        "name": "gpt5mini|deep_think+RAG",
        "model": "openai/gpt-5-mini",
        "prompt": "deep_think",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 1200,
        "temperature": 0.3,
    },
    {
        "name": "gemini3flash|deep_think+RAG",
        "model": "google/gemini-3-flash-preview",
        "prompt": "deep_think",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 1200,
        "temperature": 0.3,
    },
    {
        "name": "qwen235b|deep_think+RAG",
        "model": "qwen/qwen3-235b-a22b-2507",
        "prompt": "deep_think",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 1200,
        "temperature": 0.3,
    },
    {
        "name": "gpt41mini|precise+RAG+critique",
        "model": "openai/gpt-4.1-mini",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": False,
        "use_self_critique": True,
        "max_tokens": 700,
        "temperature": 0.3,
    },
    {
        "name": "gpt41mini|precise+noRAG",
        "model": "openai/gpt-4.1-mini",
        "prompt": "precise_instructions",
        "use_rag": False,
        "use_fewshot": False,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
    {
        "name": "gpt41mini|fewshot5_loo+RAG+precise",
        "model": "openai/gpt-4.1-mini",
        "prompt": "precise_instructions",
        "use_rag": True,
        "use_fewshot": True,
        "fewshot_k": 5,
        "use_self_critique": False,
        "max_tokens": 900,
        "temperature": 0.3,
    },
]

DEFAULT_MODEL = "openai/gpt-4.1-mini"
RATE_LIMIT = 0.3  # seconds between calls
MAX_WORKERS = 8


def log(message):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {message}", flush=True)


def load_module():
    spec = importlib.util.spec_from_file_location("my_eval", ROOT / "scripts" / "my_eval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_prompts():
    with open(ROOT / "prompts.json", encoding="utf-8") as f:
        return json.load(f)


def run_single(q_text, q_id, correct, client, config, mod):
    local_config = dict(config)
    local_config["current_question_id"] = q_id
    local_config["current_question_text"] = q_text
    result = mod.evaluate_question(
        question=q_text,
        client=client,
        model=config["model"],
        config=local_config,
    )
    answer = result["extracted_answer"]
    is_correct = (str(answer).strip().lower() == str(correct).strip().lower()) if correct else None
    cost = result.get("usage", {}).get("cost", 0.0)
    return {
        "question_id": q_id,
        "prediction": answer,
        "correct": correct,
        "is_correct": is_correct,
        "cost": cost,
        "raw_response": result.get("raw_response", "")[:200],
    }


def run_experiment(exp_cfg, df, prompts):
    log(f"{'='*70}")
    log(f"CONFIG: {exp_cfg['name']}")
    log(f"{'='*70}")

    # Configure rate limiter
    GlobalRateLimiter.reset()
    GlobalRateLimiter.get_instance(min_interval=RATE_LIMIT)

    client = OpenRouterClient()
    mod = load_module()
    model = exp_cfg.get("model", DEFAULT_MODEL)

    scripts_dir = ROOT / "scripts"
    rag_path = str(scripts_dir / "rag.tex") if exp_cfg.get("use_rag") else None

    config = {
        "model": model,
        "temperature": exp_cfg.get("temperature", 0.3),
        "max_tokens": exp_cfg.get("max_tokens", 600),
        "max_reasoning_tokens": None,
        "rag_tex_path": rag_path,
        "rag_k": 2,
        "system_prompt": prompts[exp_cfg["prompt"]],
        "use_fewshot": exp_cfg.get("use_fewshot", False),
        "fewshot_k": exp_cfg.get("fewshot_k", 3),
        "use_self_critique": exp_cfg.get("use_self_critique", False),
        "train_path": str(ROOT / "data" / "train.csv"),
        "embedding_model": "text-embedding-3-small",
    }

    rows = list(df.iterrows())
    results = []
    started_at = time.time()
    log(
        f"Preparing run for model={model} with "
        f"RAG={'on' if exp_cfg.get('use_rag') else 'off'}, "
        f"fewshot={exp_cfg.get('fewshot_k', 0) if exp_cfg.get('use_fewshot') else 0}, "
        f"critique={'on' if exp_cfg.get('use_self_critique') else 'off'}, "
        f"max_tokens={config['max_tokens']}, temp={config['temperature']}"
    )

    # Use threadpool for parallel execution
    def task(idx_row):
        _, row = idx_row
        return run_single(
            row["question"], row["question_id"], row["answer"],
            client, config, mod
        )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(task, r): r[1]["question_id"] for r in rows}
        log(f"Submitted {len(futures)} questions with {MAX_WORKERS} workers.")
        completed = 0
        for future in as_completed(futures):
            qid = futures[future]
            try:
                res = future.result()
                results.append(res)
                completed += 1
                status = "✓" if res["is_correct"] else "✗"
                empty = " [EMPTY]" if not res["prediction"] else ""
                elapsed = time.time() - started_at
                log(
                    f"{completed:02d}/{len(futures)} Q{res['question_id']:02d} {status} "
                    f"pred={res['prediction'] or '<empty>'!r:8s} ans={res['correct']}{empty} "
                    f"cost=${res['cost']:.5f} elapsed={elapsed:.1f}s"
                )
            except Exception as e:
                completed += 1
                log(f"{completed:02d}/{len(futures)} Q{qid:02d} ERROR: {e}")
                results.append({"question_id": qid, "prediction": "", "is_correct": False, "cost": 0.0})

    n_correct = sum(1 for r in results if r.get("is_correct"))
    n_answered = sum(1 for r in results if r.get("prediction"))
    n_empty = len(results) - n_answered
    accuracy = n_correct / len(results) if results else 0
    total_cost = sum(r.get("cost", 0) for r in results)

    log(f"Accuracy : {n_correct}/{len(results)} = {accuracy:.1%}")
    log(f"Answered : {n_answered}/{len(results)} ({n_empty} empty)")
    log(f"Total cost: ${total_cost:.5f}")

    return {
        "config": exp_cfg["name"],
        "accuracy": accuracy,
        "n_correct": n_correct,
        "n_total": len(results),
        "n_empty": n_empty,
        "cost": total_cost,
        "details": results,
    }


def main():
    # Load data
    train_df = pd.read_csv(ROOT / "data" / "train.csv")
    hard_df = train_df[train_df["question_id"].isin(HARD_IDS)].reset_index(drop=True)
    prompts = load_prompts()

    models = sorted({exp.get("model", DEFAULT_MODEL) for exp in EXPERIMENTS})
    log(f"Running experiments on {len(hard_df)} hard questions across models: {models}")
    log(f"Experiments to run: {[e['name'] for e in EXPERIMENTS]}")

    warm_cfg = next((exp for exp in EXPERIMENTS if exp.get("use_rag") or exp.get("use_fewshot")), None)
    if warm_cfg is not None:
        log("Warming shared caches once before the sweep to avoid repeated embedding-only startup.")
        client = OpenRouterClient()
        mod = load_module()
        scripts_dir = ROOT / "scripts"
        warm_config = {
            "model": warm_cfg.get("model", DEFAULT_MODEL),
            "temperature": warm_cfg.get("temperature", 0.3),
            "max_tokens": warm_cfg.get("max_tokens", 600),
            "max_reasoning_tokens": None,
            "rag_tex_path": str(scripts_dir / "rag.tex") if warm_cfg.get("use_rag") else None,
            "rag_k": 2,
            "system_prompt": prompts[warm_cfg["prompt"]],
            "use_fewshot": warm_cfg.get("use_fewshot", False),
            "fewshot_k": warm_cfg.get("fewshot_k", 3),
            "use_self_critique": False,
            "train_path": str(ROOT / "data" / "train.csv"),
            "embedding_model": "text-embedding-3-small",
        }
        if warm_cfg.get("use_rag"):
            log("Warmup: building or reusing RAG embeddings.")
            mod.get_rag_engine(client, warm_config)
        if warm_cfg.get("use_fewshot"):
            log("Warmup: building or reusing few-shot embeddings.")
            mod.get_fewshot_cache(client, warm_config)
        log("Warmup complete. Chat experiments start now.")

    summary_rows = []
    for exp in EXPERIMENTS:
        try:
            result = run_experiment(exp, hard_df, prompts)
            summary_rows.append({
                "config": result["config"],
                "accuracy": f"{result['accuracy']:.1%}",
                "n_correct": result["n_correct"],
                "n_total": result["n_total"],
                "n_empty": result["n_empty"],
                "cost_usd": f"${result['cost']:.5f}",
            })
        except Exception as e:
            log(f"ERROR in experiment {exp['name']}: {e}")
            import traceback; traceback.print_exc()
            summary_rows.append({"config": exp["name"], "accuracy": "ERROR", "n_correct": 0, "n_total": len(hard_df), "n_empty": 0, "cost_usd": "$0"})

    log(f"{'='*70}")
    log("SUMMARY")
    log(f"{'='*70}")
    summary_df = pd.DataFrame(summary_rows)
    if not summary_df.empty and "n_correct" in summary_df.columns:
        summary_df = summary_df.sort_values(["n_correct", "n_empty", "config"], ascending=[False, True, True])
    print(summary_df.to_string(index=False), flush=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = ROOT / "experiments" / f"hard_q_sweep_{ts}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_path, index=False)
    log(f"Summary saved: {out_path}")


if __name__ == "__main__":
    main()
