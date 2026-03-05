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
    use_rag = st.checkbox("Enable RAG", value=True)
    rag_k = st.number_input("RAG k", 1, 5, 2)
    workers = st.number_input("Parallel Workers", 1, 20, 5)

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
        bridge.run_experiment(
            mode=mode, n_runs=n_runs, use_rag=use_rag, hard_only=hard_only,
            model_name=model_choice, prompt_name=prompt_choice,
            custom_system_prompt=edited_prompt, temperature=temp,
            rag_k=rag_k, max_workers=workers,
            progress_callback=st.session_state.callback
        )
        st.session_state.is_running = False
        
        # After run, show summary
        if not st.session_state.callback.stop_requested:
            st.success("Campaign finished!")
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
        
        # Kaggle Score Calculation (Accuracy - 0.15 * Cost_75)
        # We need the average cost for ONE complete run of 75 questions
        total_questions_processed = len(ldf)
        total_cost = ldf["cost"].sum() if "cost" in ldf.columns else 0
        
        if total_questions_processed > 0:
            avg_cost_per_question = total_cost / total_questions_processed
            est_cost_75 = avg_cost_per_question * 75
            kaggle_score = acc - (0.15 * est_cost_75)
            c3.metric("Est. Kaggle Score", f"{kaggle_score:.3f}", help=f"Formula: Accuracy - 0.15 * (AvgCostPerQ * 75). Estimated cost for 75 questions: ${est_cost_75:.4f}")
    
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
            st.dataframe(df, width='stretch')
            
            # Improved stats for historical view
            train_data_path = Path(__file__).parent / "data" / "train.csv"
            if train_data_path.exists():
                train_df = pd.read_csv(train_data_path)
                merged = df.merge(train_df[["question_id", "answer"]], on="question_id", how="inner")
                if not merged.empty:
                    # Calculate accuracy for EACH prediction column
                    pred_cols = [c for c in df.columns if c.startswith("prediction_")]
                    accuracies = []
                    for col in pred_cols:
                        acc_run = (merged[col].astype(str).str.lower().str.strip() == merged["answer"].astype(str).str.lower().str.strip()).mean()
                        accuracies.append(acc_run)
                    
                    mean_acc = sum(accuracies) / len(accuracies)
                    
                    # Try to get cost from JSON to calculate Kaggle Score
                    c1, c2 = st.columns(2)
                    c1.metric("Mean Accuracy (All Runs)", f"{mean_acc:.1%}")
                    
                    # Estimate Kaggle Score if cost info is available in a results JSON
                    run_json = run_path / "run_1_results.json"
                    if run_json.exists():
                        try:
                            with open(run_json, "r") as f:
                                data = json.load(f)
                                total_run_cost = sum(q.get("usage", {}).get("cost", 0) for q in data)
                                n_q = len(data)
                                if n_q > 0:
                                    avg_cost_q = total_run_cost / n_q
                                    est_75 = avg_cost_q * 75
                                    k_score = mean_acc - (0.15 * est_75)
                                    c2.metric("Est. Kaggle Score", f"{k_score:.3f}", help=f"Based on Run 1 average cost: ${est_75:.4f} for 75 questions")
                        except:
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

