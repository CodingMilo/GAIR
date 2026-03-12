import streamlit as st
import pandas as pd
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import time
import threading

# Add current directory to sys.path for local imports
sys.path.append(str(Path(__file__).parent))

# Import logic from bridge
try:
    import bridge
except ImportError as e:
    st.error(f"Failed to import project modules: {e}")
    st.stop()

# Mock models and prompts if files are missing
def get_prompts():
    path = Path(__file__).parent / "prompts.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"default": "You are a Reliability Engineering expert. Answer the following CRE exam question."}

def get_models():
    path = Path(__file__).parent / "models.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"openai/gpt-4o-mini": "GPT-4o Mini", "google/gemini-2.0-flash-001": "Gemini 2.0 Flash"}


def load_run_cost_breakdown(run_path: Path) -> pd.DataFrame:
    rows = []
    for result_file in sorted(run_path.glob("run_*_results.json")):
        run_name = result_file.stem.replace("_results", "")
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            continue

        total_cost = 0.0
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        request_count = 0
        question_count = len(entries)

        for entry in entries:
            usage = entry.get("usage", {}) or {}
            total_cost += usage.get("cost", 0.0) or 0.0
            total_tokens += usage.get("total_tokens", 0) or 0
            prompt_tokens += usage.get("prompt_tokens", 0) or 0
            completion_tokens += usage.get("completion_tokens", 0) or 0
            request_count += usage.get("request_count", 0) or 0

        rows.append({
            "run": run_name,
            "cost_usd": total_cost,
            "avg_cost_per_question_usd": (total_cost / question_count) if question_count else 0.0,
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "request_count": request_count,
        })

    return pd.DataFrame(rows)

st.set_page_config(page_title="GAIR Dashboard", layout="wide", page_icon="🛡️")

# --- SIDEBAR: Configuration ---
st.sidebar.title("🚀 Run Configuration")

mode = st.sidebar.selectbox("Mode", ["train", "test"], index=0)
models_dict = get_models()
model_choice = st.sidebar.selectbox("Model", list(models_dict.keys()), format_func=lambda x: models_dict[x])
prompts_dict = get_prompts()
prompt_choice = st.sidebar.selectbox("System Prompt", list(prompts_dict.keys()))

with st.sidebar.expander("⚙️ Hyperparameters", expanded=True):
    temp = st.slider("Temperature", 0.0, 2.0, 1.0, 0.1)
    n_runs = st.number_input("Number of Runs", 1, 10, 5 if mode == "test" else 1)
    max_tokens = st.number_input(
        "Max Output Tokens",
        min_value=50, max_value=8000, value=512, step=50,
        help="Limit per-response token length. Lower = faster & cheaper (e.g. 256 for simple prompts, 512-1024 for CoT)."
    )
    use_rag = st.checkbox("Enable RAG", value=True)
    rag_k = st.number_input("RAG k", 1, 20, 8)
    workers = st.number_input("Parallel Workers", 1, 20, 5)
    rate_limit = st.number_input(
        "Rate Limit (s between calls)", 0.0, 5.0, 0.3, 0.1,
        help="Minimum seconds between API calls across all parallel workers."
    )

st.sidebar.divider()
st.sidebar.subheader("🧠 Advanced Techniques")
use_fewshot = st.sidebar.checkbox(
    "Few-shot Examples (from train set)",
    value=False,
    help="Retrieve the k most similar training Q&A pairs and prepend them to each question. During train evaluation, the current question is excluded (leave-one-out) to avoid answer leakage. Costs extra embedding tokens."
)
if use_fewshot:
    fewshot_k = st.sidebar.number_input("Few-shot k", 1, 10, 3)
else:
    fewshot_k = 3

use_self_critique = st.sidebar.checkbox(
    "Self-Critique Pass (2× cost)",
    value=False,
    help="After the first answer, send a second call asking the model to check common CRE pitfalls and correct itself."
)

use_tool_calling = st.sidebar.checkbox(
    "Tool Calling — Python math executor",
    value=False,
    help=(
        "Gives the LLM a sandboxed Python tool (execute_python_math) for precise "
        "Weibull / Poisson / MTBF calculations. Recommended with the 'deep_think_json' prompt. "
        "May add 1-3 extra API calls per question when math is detected."
    )
)

use_json_format = st.sidebar.checkbox(
    "Structured JSON Output",
    value=False,
    help=(
        "Expects a final JSON block containing 'selected_letter' while still allowing the model to "
        "show its reasoning above it. Use with the 'deep_think_json' prompt."
    )
)

st.sidebar.divider()
hard_only = st.sidebar.checkbox("Hard Questions Only", value=False)

# --- STATE MANAGEMENT ---
if 'live_data' not in st.session_state:
    st.session_state.live_data = []
if 'progress' not in st.session_state:
    st.session_state.progress = 0.0
if 'is_running' not in st.session_state:
    st.session_state.is_running = False

# Callback structure
class ProgressCallback:
    def __init__(self, progress_bar=None, status_msg=None, live_table=None):
        self.stop_requested = False
        self.progress_bar = progress_bar
        self.status_msg = status_msg
        self.live_table = live_table
    
    def __call__(self, info):
        if info["type"] == "update":
            st.session_state.live_data.append(info["last_log"])
            prog = info["completed"] / info["total"]
            st.session_state.progress = prog
            
            if self.progress_bar:
                self.progress_bar.progress(prog)
            if self.status_msg:
                self.status_msg.text(f"Processed {info['completed']}/{info['total']} questions...")
            if self.live_table:
                ldf = pd.DataFrame(st.session_state.live_data)
                self.live_table.dataframe(ldf[["question_id", "prediction", "is_correct"]].tail(10), width='stretch')
        return self.stop_requested

if 'callback' not in st.session_state:
    st.session_state.callback = ProgressCallback()

# --- MAIN AREA ---
st.title("🛡️ GAIR: Reliability Agent Dashboard")

st.subheader(f"Current Prompt: `{prompt_choice}`")
edited_prompt = st.text_area("System Prompt Editor", prompts_dict[prompt_choice], height=150)

col_run, col_stop = st.columns([1, 1])

if col_run.button("🔥 RUN CAMPAIGN", type="primary", width='stretch', disabled=st.session_state.is_running):
    st.session_state.live_data = []
    st.session_state.progress = 0.0
    st.session_state.is_running = True
    st.session_state.callback.stop_requested = False
    st.rerun()

if st.session_state.is_running:
    if col_stop.button("🛑 STOP FORCE", type="secondary", width='stretch'):
        st.session_state.callback.stop_requested = True
        st.warning("Stop signal sent... waiting for current workers to finish.")

    # Execution wrapper
    progress_bar = st.progress(st.session_state.progress)
    status_msg = st.empty()
    
    st.divider()
    
    # --- LIVE METRICS ---
    m1, m2, m3 = st.columns(3)
    acc_metric = m1.empty()
    cost_metric = m2.empty()
    score_metric = m3.empty()

    st.subheader("📡 Live Results")
    live_table = st.empty()
    
    st.session_state.callback.progress_bar = progress_bar
    st.session_state.callback.status_msg = status_msg
    st.session_state.callback.live_table = live_table
    
    try:
        result_df = bridge.run_experiment(
            mode=mode, n_runs=n_runs, use_rag=use_rag, hard_only=hard_only,
            model_name=model_choice, prompt_name=prompt_choice,
            custom_system_prompt=edited_prompt, temperature=temp,
            rag_k=rag_k, max_workers=workers,
            max_tokens=max_tokens, rate_limit_seconds=rate_limit,
            use_fewshot=use_fewshot, fewshot_k=fewshot_k,
            use_self_critique=use_self_critique,
            use_tool_calling=use_tool_calling,
            use_json_format=use_json_format,
            progress_callback=st.session_state.callback
        )
        st.session_state.is_running = False
        st.session_state.last_result_df = result_df
        
        # After run, show summary
        if not st.session_state.callback.stop_requested:
            st.success("Campaign finished!")
            if mode == "test":
                st.info("Test mode complete. Download the Kaggle submission CSV from the Results History below.")
            st.balloons()
            # Refresh to show historical analysis tabs
            st.rerun()
            
    except Exception as e:
        st.error(f"Run failed: {e}")
        st.session_state.is_running = False

# --- RESULTS VIEW (LAST RUN OR ARCHIVE) ---
elif st.session_state.live_data:
    st.divider()
    ldf = pd.DataFrame(st.session_state.live_data)
    
    # Top Stats
    c1, c2, c3, c4 = st.columns(4)
    
    total_cost = ldf["cost"].sum() if "cost" in ldf.columns else 0
    c1.metric("Total Cost", f"${total_cost:.4f}")
    
    if "is_correct" in ldf.columns and ldf["is_correct"].dtype == bool:
        # Calculate accuracy per run then average
        if "run" in ldf.columns:
            acc_per_run = ldf.groupby("run")["is_correct"].mean()
            acc = acc_per_run.mean()
        else:
            acc = ldf["is_correct"].mean()
            
        c2.metric("Mean Accuracy", f"{acc:.1%}")
        
        # Kaggle Score: accuracy - 0.15 * avg_cost_per_run (for 75 questions); 0 if cost > 0.4
        total_questions_processed = len(ldf)
        total_cost = ldf["cost"].sum() if "cost" in ldf.columns else 0
        n_runs_done = ldf["run"].nunique() if "run" in ldf.columns else 1
        
        if total_questions_processed > 0 and n_runs_done > 0:
            avg_cost_per_question = total_cost / total_questions_processed
            est_cost_per_run = avg_cost_per_question * 75
            if est_cost_per_run > 0.4:
                kaggle_score = 0.0
                score_help = f"Cost ${est_cost_per_run:.4f} > $0.40 threshold → score = 0"
            else:
                kaggle_score = max(0, min(1, acc - 0.15 * est_cost_per_run))
                score_help = f"acc - 0.15 × cost = {acc:.3f} - 0.15 × {est_cost_per_run:.4f}. Threshold: $0.40/run."
            c3.metric("Est. Kaggle Score", f"{kaggle_score:.3f}", help=score_help)
    
    c4.metric("Questions", len(ldf))

    # Tabs for different views
    tab_res, tab_analysis, tab_wrong = st.tabs(["📋 Detailed Results", "📝 Analysis Report", "❌ Failure Log"])
    
    with tab_res:
        st.subheader("Last Run Summary")
        s1, s2, s3 = st.columns(3)
        avg_cost = ldf["cost"].mean() if "cost" in ldf.columns else 0
        s1.write(f"**Avg Cost / Question:** ${avg_cost:.6f}")
        s2.write(f"**Total Questions:** {len(ldf)}")
        s3.write(f"**Estimated 75q Cost:** ${avg_cost*75:.4f}")
        
        st.divider()
        st.dataframe(ldf, width='stretch')
    
    with tab_analysis:
        # Search for the latest report in experiments
        st.info("Select a run in 'Results History' below to view the detailed Markdown reports generated by the engine.")

# --- HISTORY ---
st.divider()
st.header("📊 Results History")
outputs_dir = Path(__file__).parent / "experiments" / "dashboard_runs"
if not outputs_dir.exists():
    outputs_dir.mkdir(parents=True, exist_ok=True)

# Also check teacher's standard folders
teacher_dirs = [d for d in (Path(__file__).parent / "experiments").iterdir() if d.is_dir() and d.name != "dashboard_runs"]

all_runs = []
for d in [outputs_dir] + teacher_dirs:
    all_runs.extend([r for r in d.iterdir() if r.is_dir() and (r / "config.json").exists()])

runs = sorted(all_runs, key=lambda x: x.stat().st_mtime, reverse=True)

if runs:
    selected_run_name = st.selectbox("Select a previous run to analyze", [f"{r.parent.name}/{r.name}" for r in runs])
    run_path = next(r for r in runs if f"{r.parent.name}/{r.name}" == selected_run_name)
    
    # Load solution for stats
    solution_file = run_path / "solution.csv"
    
    t1, t2, t3 = st.tabs(["📊 Performance", "📝 Analysis Report", "❌ Failed Questions"])
    
    with t1:
        if solution_file.exists():
            df = pd.read_csv(solution_file)
            pred_cols = [c for c in df.columns if c.startswith("prediction_")]
            
            # Check if this is a test run (no answer column) or train run
            kaggle_file = run_path / "kaggle_submission.csv"
            if kaggle_file.exists():
                st.success("TEST RUN — Kaggle submission ready for download!")
                with open(kaggle_file, "rb") as kf:
                    st.download_button(
                        label="⬇️ Download kaggle_submission.csv",
                        data=kf.read(),
                        file_name="kaggle_submission.csv",
                        mime="text/csv",
                    )
                kaggle_df = pd.read_csv(kaggle_file)
                avg_cost = kaggle_df["Average cost per run"].mean() if "Average cost per run" in kaggle_df.columns else 0.0
                per_question_cost = (avg_cost / len(df)) if len(df) else 0.0
                run_costs_df = load_run_cost_breakdown(run_path)
                total_job_cost = run_costs_df["cost_usd"].sum() if not run_costs_df.empty else avg_cost * max(len(pred_cols), 1)

                mc1, mc2, mc3 = st.columns(3)
                mc1.metric(
                    "Kaggle Cost / Full Run",
                    f"${avg_cost:.6f}",
                    help="Cost of one complete 75-question submission run. This is the value used by the Kaggle evaluator."
                )
                mc2.metric(
                    "Average Cost / Question",
                    f"${per_question_cost:.6f}",
                    help="Average cost per answered question, estimated from the full-run Kaggle cost divided by the number of questions."
                )
                mc3.metric(
                    "Total Cost For This Job",
                    f"${total_job_cost:.6f}",
                    help="Sum of all repetitions executed in this dashboard run."
                )

                st.caption(
                    "The `Average cost per run` field is intentionally identical on every row of `kaggle_submission.csv`: "
                    "the competition scorer reads the column mean as one global cost for a full submission run."
                )

                if not run_costs_df.empty:
                    st.subheader("Run Cost Breakdown")
                    st.dataframe(run_costs_df, width='stretch')
            
            st.dataframe(df, width='stretch')
            
            # Improved stats for historical view (only for train runs with ground truth)
            train_data_path = Path(__file__).parent / "data" / "train.csv"
            if train_data_path.exists():
                train_df = pd.read_csv(train_data_path)
                merged = df.merge(train_df[["question_id", "answer"]], on="question_id", how="inner")
                if not merged.empty:
                    # Calculate accuracy for EACH prediction column
                    accuracies = []
                    for col in pred_cols:
                        acc_run = (merged[col].astype(str).str.lower().str.strip() == merged["answer"].astype(str).str.lower().str.strip()).mean()
                        accuracies.append(acc_run)
                    
                    mean_acc = sum(accuracies) / len(accuracies)
                    
                    # Try to get cost from JSON to calculate Kaggle Score (threshold 0.4)
                    c1, c2 = st.columns(2)
                    c1.metric("Mean Accuracy (All Runs)", f"{mean_acc:.1%}")
                    
                    run_json = run_path / "run_1_results.json"
                    if run_json.exists():
                        try:
                            with open(run_json, "r") as fj:
                                rdata = json.load(fj)
                                total_run_cost = sum(q.get("usage", {}).get("cost", 0) for q in rdata)
                                n_q = len(rdata)
                                if n_q > 0:
                                    avg_cost_q = total_run_cost / n_q
                                    est_75 = avg_cost_q * 75
                                    if est_75 > 0.4:
                                        k_score = 0.0
                                        help_txt = f"Cost ${est_75:.4f} > $0.40 threshold → score = 0"
                                    else:
                                        k_score = max(0, min(1, mean_acc - 0.15 * est_75))
                                        help_txt = f"acc - 0.15 × cost = {mean_acc:.3f} - 0.15 × {est_75:.4f}"
                                    c2.metric("Est. Kaggle Score", f"{k_score:.3f}", help=help_txt)
                        except Exception:
                            pass
    
    with t2:
        report_file = run_path / "result_analysis.md"
        if report_file.exists():
            st.markdown(report_file.read_text(encoding="utf-8"))
        else:
            st.warning("No `result_analysis.md` found for this run.")
            
    with t3:
        wrong_file = run_path / "wrong_answers.md"
        if wrong_file.exists():
            st.markdown(wrong_file.read_text(encoding="utf-8"))
        else:
            # Fallback to JSON logs if MD not present
            st.info("No structured `wrong_answers.md` found. Use the Analysis Report tab for failure details.")

