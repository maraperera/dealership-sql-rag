import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8001"

st.set_page_config(
    page_title="Melbourne Auto Dealership Network",
    layout="wide",
    page_icon="🚗"
)

# Custom CSS for ChatGPT layout: sticky bottom bar and tight padding
st.markdown("""
<style>
    /* Remove unnecessary top space */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    /* Ensure the chat scroll container looks clean */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚗 Melbourne Auto Dealership Network")
st.caption("Internal inventory intelligence covering Melbourne CBD, Doncaster, and Dandenong branches.")

tab_assistant, tab_observability, tab_ragas = st.tabs([
    "💬 Dealership Assistant",
    "📊 Observability & Tracing",
    "🧪 Ragas Evaluation Engine"
])

# ----------------- TAB 1: DEALERSHIP ASSISTANT (CHATGPT SCROLLING UI) -----------------
with tab_assistant:
    # Initialize message memory
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your internal inventory assistant. Ask me anything about our vehicles across Melbourne CBD, Doncaster, and Dandenong."
            }
        ]

    # Fixed-height scrollable container (scrolls conversation just like ChatGPT)
    chat_box = st.container(height=540)

    # Render all previous chat history inside the scrollable box
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("table"):
                    with st.expander("View Car Details"):
                        st.dataframe(pd.DataFrame(msg["table"]), width="stretch")

    # Bottom sticky chat input bar
    if user_prompt := st.chat_input("Ask about vehicles, branches, pricing, or stock..."):
        # 1. Add user prompt to state & render immediately in the scroll container
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with chat_box:
            with st.chat_message("user"):
                st.markdown(user_prompt)

            # 2. Assistant loading spinner & backend call
            with st.chat_message("assistant"):
                with st.spinner("Checking inventory..."):
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/rag/query", json={"query": user_prompt})
                        if res.status_code == 200:
                            data = res.json()
                            answer_text = data.get("answer", "No response generated.")
                            st.markdown(answer_text)

                            table_data = None
                            if data.get("results") and isinstance(data["results"], list) and len(data["results"]) > 0:
                                first_row = data["results"][0]
                                if not (len(data["results"]) == 1 and ("count" in first_row or len(first_row) == 1)):
                                    table_data = data["results"]
                                    with st.expander("View Car Details"):
                                        st.dataframe(pd.DataFrame(table_data), width="stretch")

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer_text,
                                "table": table_data
                            })
                        else:
                            err_msg = f"Backend error ({res.status_code}): {res.text}"
                            st.error(err_msg)
                            st.session_state.messages.append({"role": "assistant", "content": err_msg})
                    except Exception as e:
                        err_msg = f"Connection error: {e}"
                        st.error(err_msg)
                        st.session_state.messages.append({"role": "assistant", "content": err_msg})

        # Auto-refresh to ensure latest message is scrolled to bottom
        st.rerun()

# ----------------- TAB 2: OBSERVABILITY & TRACING -----------------
with tab_observability:
    st.subheader("System Observability & Audit Logs")
    st.caption("Track backend operations, executed SQL queries, context generation, and hallucination metrics.")

    if st.button("Refresh Logs"):
        st.rerun()

    try:
        res = requests.get(f"{BACKEND_URL}/api/observability/traces?limit=100")
        if res.status_code == 200:
            traces = res.json()
            if not traces:
                st.info("No traces logged yet.")
            else:
                df_traces = pd.DataFrame(traces)

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Requests", len(df_traces))
                failures = len(df_traces[df_traces["status"] != "SUCCESS"])
                c2.metric("Errors / Out of Scope", failures)
                hallucinations = int(df_traces["hallucination_flag"].sum())
                c3.metric("Flagged Hallucinations", hallucinations)

                st.markdown("### Recent Queries")
                display_cols = ["timestamp", "user_query", "execution_time_ms", "status", "hallucination_flag"]
                st.dataframe(
                    df_traces[display_cols],
                    width="stretch",
                    hide_index=False
                )

                st.divider()

                st.markdown("### Query Deep Dive")
                selected_trace_id = st.selectbox(
                    "Select Trace ID",
                    options=df_traces["trace_id"].tolist(),
                    label_visibility="visible"
                )

                trace = df_traces[df_traces["trace_id"] == selected_trace_id].iloc[0]

                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("**User Question:**")
                    st.write(trace["user_query"])
                    st.markdown("**Generated SQL:**")
                    st.code(trace["generated_sql"], language="sql")

                with col_right:
                    st.markdown("**Final Synthesized Response:**")
                    st.success(trace["final_response"])
                    st.markdown("**Retrieved Data Context:**")
                    st.caption("Context")
                    st.text_area(
                        "Context",
                        value=trace["retrieved_context"],
                        height=100,
                        label_visibility="collapsed",
                        disabled=True
                    )
        else:
            st.error("Failed to load logs from server.")
    except Exception as e:
        st.error(f"Observability connection error: {e}")

# ----------------- TAB 3: RAGAS EVALUATION -----------------
with tab_ragas:
    st.subheader("Automated Pipeline Evaluation")
    st.caption("Benchmark logged production conversations using Ragas metrics.")

    num_traces = st.slider("Select number of recent interactions to evaluate", min_value=1, max_value=20, value=5)

    if st.button("Run Automated Evaluation on Logs", type="primary"):
        with st.spinner("Evaluating logged conversations using local LLM..."):
            try:
                res = requests.post(f"{BACKEND_URL}/api/eval/batch?limit={num_traces}")
                if res.status_code == 200:
                    data = res.json()
                    eval_list = data.get("evaluations", [])

                    if not eval_list:
                        st.warning("No successful traces found in the database to evaluate. Run some dealership queries first!")
                    else:
                        eval_df = pd.DataFrame(eval_list)

                        faith_mean = eval_df["faithfulness"].mean() if "faithfulness" in eval_df.columns else 0.0
                        rel_mean = eval_df["answer_relevancy"].mean() if "answer_relevancy" in eval_df.columns else 0.0

                        c1, c2 = st.columns(2)
                        c1.metric("Average Faithfulness", f"{faith_mean:.2f}")
                        c2.metric("Average Relevancy", f"{rel_mean:.2f}")

                        st.dataframe(eval_df, width="stretch")
                        st.success(f"Successfully evaluated {len(eval_df)} trace(s).")
                else:
                    st.error(f"Failed to run automated evaluation: {res.text}")
            except Exception as e:
                st.error(f"Evaluation error: {e}")