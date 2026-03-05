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
                self.live_table.dataframe(ldf[["question_id", "prediction", "is_correct"]].tail(10), use_container_width=True)
        return self.stop_requested

if 'callback' not in st.session_state:
    st.session_state.callback = ProgressCallback()

# --- MAIN AREA ---
st.title("🛡️ GAIR: Reliability Agent Dashboard")

st.subheader(f"Current Prompt: `{prompt_choice}`")
edited_prompt = st.text_area("System Prompt Editor", prompts_dict[prompt_choice], height=150)

col_run, col_stop = st.columns([1, 1])

if col_run.button("🔥 RUN CAMPAIGN", type="primary", use_container_width=True, disabled=st.session_state.is_running):
    st.session_state.live_data = []
    st.session_state.progress = 0.0
    st.session_state.is_running = True
    st.session_state.callback.stop_requested = False
    st.rerun()

if st.session_state.is_running:
    if col_stop.button("🛑 STOP FORCE", type="secondary", use_container_width=True):
        st.session_state.callback.stop_requested = True
        st.warning("Stop signal sent... waiting for current workers to finish.")

    # Execution wrapper
    progress_bar = st.progress(st.session_state.progress)
    status_msg = st.empty()
    
    st.divider()
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
        if st.session_state.callback.stop_requested:
            st.error("Run aborted by user.")
        else:
            st.success("Campaign finished!")
            st.balloons()
        st.session_state.is_running = False
    except Exception as e:
        st.error(f"Run failed: {e}")
        st.session_state.is_running = False

# --- LIVE LOGS ---
elif st.session_state.live_data and not st.session_state.is_running:
    st.divider()
    st.subheader("📡 Last Run Results")
    ldf = pd.DataFrame(st.session_state.live_data)
    
    # Check for errors in the raw response
    if "raw_response" in ldf.columns:
        err_count = ldf["raw_response"].str.contains(r"\[ERROR", na=False).sum()
        if err_count > 0:
            st.error(f"⚠️ {err_count} API Errors detected in this run. Check Failure Logs below.")

    st.dataframe(ldf[["question_id", "prediction", "is_correct"]].tail(10), use_container_width=True)

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
    
    solution_file = run_path / "solution.csv"
    summary_file = run_path / "run_1_results.json" # Teacher stores usage here
    
    c1, c2, c3 = st.columns(3)
    if solution_file.exists():
        df = pd.read_csv(solution_file)
        # Check if we have ground truth (train mode)
        train_data_path = Path(__file__).parent / "data" / "train.csv"
        if train_data_path.exists():
            train_df = pd.read_csv(train_data_path)
            merged = df.merge(train_df[["question_id", "answer"]], on="question_id", how="inner")
            if not merged.empty:
                acc = (merged["prediction_1"].astype(str).str.lower().str.strip() == merged["answer"].astype(str).str.lower().str.strip()).mean()
                c1.metric("Accuracy (Run 1)", f"{acc:.1%}")
        
        c3.metric("Questions", len(df))
    
    # Show summary report if exists
    report_file = run_path / "result_analysis.md"
    if report_file.exists():
        with st.expander("📄 View Analysis Report"):
            st.markdown(report_file.read_text(encoding="utf-8"))
