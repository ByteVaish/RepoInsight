import json
from datetime import datetime
import pandas as pd
import streamlit as st
from agent.orchestrator import RepositoryAgent

st.set_page_config(page_title="RepoInsight | AI Repository Agent", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: radial-gradient(ellipse at 12% 0%, rgba(35,85,145,.22), transparent 34%), #0b1020 !important;
  color:#eef3ff !important;
}
[data-testid="stHeader"] {background:rgba(11,16,32,.92) !important;}
/* High-contrast text: Streamlit widgets otherwise inherit dark theme defaults inconsistently. */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p,
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  color:#dce6f7 !important;
}
h1,h2,h3,h4,h5,h6 {color:#f4f7ff !important;}
label {color:#dce6f7 !important;}
[data-testid="stSidebar"] {color:#dce6f7 !important;}
.block-container {padding-top:1.6rem; max-width:1500px;}
.hero {padding:25px 28px; border:1px solid rgba(126,160,220,.22); border-radius:20px; background:linear-gradient(115deg,rgba(24,43,76,.94),rgba(16,26,48,.92)); margin-bottom:22px;}
.eyebrow {color:#83b7ff; text-transform:uppercase; letter-spacing:.16em; font-size:11px; font-weight:700;}
.hero h1 {font-family:'Space Grotesk',sans-serif; font-size:32px; margin:6px 0 4px; color:#f4f7ff;}
.hero p {color:#aab8d0; margin:0; font-size:14px;}
.panel {background:rgba(21,31,53,.78); border:1px solid rgba(137,164,207,.17); border-radius:16px; padding:18px 20px;}
.small-muted {color:#93a4c0;font-size:12px;}
div[data-testid="stMetric"] {background:rgba(22,35,60,.82); border:1px solid rgba(137,164,207,.16); padding:14px 16px; border-radius:14px;}
div[data-testid="stMetricLabel"] p {color:#9eb0cc !important;}
div[data-testid="stMetricValue"] {color:#f1f6ff !important;}
.stButton>button {border-radius:10px; font-weight:650; min-height:42px;}
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  border-radius:10px; background:#f8fafc !important; color:#172033 !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {color:#64748b !important;}
.stButton>button, .stDownloadButton>button {
  border-radius:10px; font-weight:650; min-height:42px;
  border:1px solid rgba(148,163,184,.35);
}
.stButton>button[kind="primary"] {background:#dc4960 !important; color:#fff !important; border:0;}
.stButton>button:not([kind="primary"]), .stDownloadButton>button {
  background:#e8eef8 !important; color:#172033 !important;
}

.stTabs [data-baseweb="tab-list"] {gap:8px;}
.stTabs [data-baseweb="tab"] {background:rgba(23,35,59,.65); border-radius:9px 9px 0 0; padding:10px 17px;}
.stTabs [aria-selected="true"] {background:rgba(56,116,198,.25) !important;}
div[data-testid="stExpander"] {border:1px solid rgba(137,164,207,.16); border-radius:12px;}
section[data-testid="stSidebar"] {background:#101a2d; border-right:1px solid rgba(137,164,207,.15);}
hr {border-color:rgba(137,164,207,.16);}
</style>
""", unsafe_allow_html=True)

if "agent" not in st.session_state: st.session_state.agent = RepositoryAgent()
if "messages" not in st.session_state: st.session_state.messages = []
if "last_report" not in st.session_state: st.session_state.last_report = None
if "repo_url" not in st.session_state: st.session_state.repo_url = ""

agent = st.session_state.agent
report = st.session_state.last_report

with st.sidebar:
    st.markdown("## ◈ RepoInsight")
    st.caption("Autonomous repository analysis")
    st.markdown("---")
    st.markdown("**WORKSPACE STATUS**")
    if report:
        st.success("Analysis available")
        st.caption(f"Repository: {report.get('repository','—')}")
    else:
        st.info("Waiting for repository")
    st.markdown("---")
    st.markdown("**QUICK ACTIONS**")
    if st.button("↻ Reset workspace", use_container_width=True):
        agent.reset(); st.session_state.messages=[]; st.session_state.last_report=None; st.session_state.repo_url=""; st.rerun()
    if report:
        st.download_button("⇩ Download JSON report", data=json.dumps(report, indent=2, default=str), file_name="repository_analysis_report.json", mime="application/json", use_container_width=True)
        findings = report.get("findings", report.get("python_findings", []))
        if findings:
            st.download_button("⇩ Download findings CSV", data=pd.DataFrame(findings).to_csv(index=False), file_name="repository_findings.csv", mime="text/csv", use_container_width=True)
    st.markdown("---")
    st.caption("Runs locally. No LLM API key required.")
    st.caption("Use only repositories you are authorized to inspect.")

st.markdown("""
<div class="hero">
 <div class="eyebrow">AUTONOMOUS DEVELOPER TOOLING · LIVE WORKSPACE</div>
 <h1>GitHub Repository Analysis Agent</h1>
 <p>Plan tasks · Select tools · Inspect code · Reflect on results · Ask questions</p>
</div>
""", unsafe_allow_html=True)

# Repository launch panel
with st.container(border=True):
    a, b = st.columns([5,1.25], vertical_alignment="bottom")
    with a:
        repo_url = st.text_input("GitHub repository URL", value=st.session_state.repo_url, placeholder="https://github.com/psf/requests", label_visibility="visible")
    with b:
        run = st.button("▶ Analyse repository", type="primary", use_container_width=True)
    st.caption("Public GitHub repositories · Clone and static analysis · Python quality and security indicators")
    if run:
        st.session_state.repo_url = repo_url
        if not repo_url.strip():
            st.warning("Enter a GitHub repository URL to start.")
        else:
            with st.status("Agent workflow running…", expanded=True) as status:
                st.write("1 / Planner is decomposing the task")
                result = agent.analyse(repo_url.strip())
                if result.get("ok"):
                    st.session_state.last_report = result["report"]
                    status.update(label="Analysis completed", state="complete", expanded=False)
                    st.success("Repository analysis completed successfully.")
                else:
                    status.update(label="Analysis failed", state="error", expanded=True)
                    st.error(result.get("error", "Unknown analysis error"))
            st.rerun()

report = st.session_state.last_report
if report:
    findings = report.get("findings", report.get("python_findings", [])) or []
    severity = report.get("severity_counts", {}) or {}
    st.markdown(f"### Overview  <span class='small-muted'>/ {report.get('repository','Repository')}</span>", unsafe_allow_html=True)
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Files scanned", report.get("file_count",0))
    k2.metric("Languages", len(report.get("languages",{})))
    k3.metric("Python functions", report.get("python_function_count",0))
    k4.metric("Total findings", report.get("total_findings",len(findings)))
    k5.metric("Retries used", agent.state.get("retry_count",0))
    st.markdown(" ")
    tab_overview, tab_findings, tab_structure, tab_chat, tab_trace, tab_tools = st.tabs(["◫ Overview", "⚑ Findings", "⌘ Structure", "✳ Ask agent", "⇄ Execution trace", "⚙ Tools & state"])
    with tab_overview:
        left,right = st.columns([1.15,1])
        with left:
            st.markdown("#### Finding severity")
            sev_df = pd.DataFrame({"Severity":["Critical","High","Medium","Low"],"Count":[severity.get(x,0) for x in ["Critical","High","Medium","Low"]]}).set_index("Severity")
            st.bar_chart(sev_df, use_container_width=True, height=250)
        with right:
            st.markdown("#### Languages detected")
            langs = report.get("languages",{}) or {}
            if langs: st.bar_chart(pd.DataFrame({"Files":langs}), use_container_width=True, height=250)
            else: st.info("No language data available.")
        st.markdown("#### Agent summary")
        st.markdown(f"<div class='panel'>{report.get('summary','No summary available.')}</div>", unsafe_allow_html=True)
        reflection = report.get("reflection",{}) or {}
        st.markdown("#### Reflection check")
        if reflection.get("passed"): st.success("Reflection passed · Report consistency verified")
        else: st.warning("Reflection needs review · " + "; ".join(reflection.get("issues",[])))
    with tab_findings:
        st.markdown("#### Search and filter findings")
        f1,f2,f3 = st.columns([2,1,1])
        with f1: search = st.text_input("Search", placeholder="File, issue, category…", key="finding_search")
        with f2: severity_options = ["All"] + sorted({str(x.get("severity","Unknown")) for x in findings})
        with f2: sev_filter = st.selectbox("Severity", severity_options, key="finding_severity")
        with f3: category_options = ["All"] + sorted({str(x.get("category","Other")) for x in findings})
        with f3: cat_filter = st.selectbox("Category", category_options, key="finding_category")
        filtered = findings
        if sev_filter != "All": filtered = [x for x in filtered if str(x.get("severity","Unknown")) == sev_filter]
        if cat_filter != "All": filtered = [x for x in filtered if str(x.get("category","Other")) == cat_filter]
        if search: filtered = [x for x in filtered if search.lower() in json.dumps(x, default=str).lower()]
        st.caption(f"Showing {len(filtered)} of {len(findings)} findings")
        if filtered:
            df = pd.DataFrame(filtered)
            cols = [c for c in ["severity","category","file","line","issue","suggested_fix","item"] if c in df.columns]
            st.dataframe(df[cols] if cols else df, use_container_width=True, hide_index=True)
            st.download_button("Download filtered findings", pd.DataFrame(filtered).to_csv(index=False), "filtered_findings.csv", "text/csv")
        else: st.success("No findings match these filters.")
        st.caption("Static-analysis findings are potential issues for human review, not proof of exploitable vulnerabilities.")
    with tab_structure:
        s1,s2 = st.columns([1,1])
        with s1:
            st.markdown("#### Repository tree")
            st.code(report.get("tree","No tree available"), language="text")
        with s2:
            st.markdown("#### Dependencies")
            deps = report.get("dependencies",[]) or []
            if deps: st.dataframe(pd.DataFrame({"Dependency":deps}), use_container_width=True, hide_index=True)
            else: st.info("No common dependency manifest found.")
            st.markdown("#### Language distribution")
            st.json(report.get("languages",{}))
    with tab_chat:
        st.markdown("#### Chat with your repository")
        st.caption("Ask questions grounded in the latest analysis report. Short-term context is retained during this session.")
        chat_area = st.container(height=360, border=True)
        with chat_area:
            if not st.session_state.messages: st.info("Try: How many Python functions are there? Which files have security findings?")
            for item in st.session_state.messages:
                with st.chat_message(item["role"]): st.markdown(item["content"])
        q1,q2 = st.columns([5,1])
        with q1: question = st.text_input("Your question", placeholder="Ask about files, languages, findings…", key="agent_question")
        with q2:
            st.write("")
            send = st.button("Send ↗", use_container_width=True)
        if send and question.strip():
            st.session_state.messages.append({"role":"user","content":question.strip()})
            answer = agent.ask(question.strip())
            st.session_state.messages.append({"role":"assistant","content":answer})
            st.rerun()
        if st.button("Clear chat history"):
            st.session_state.messages=[]
            agent.history=[x for x in agent.history if x.get("role")=="system"]
            st.rerun()
    with tab_trace:
        trace = agent.trace
        t1,t2 = st.columns([2,1])
        with t1: trace_search = st.text_input("Find trace events", placeholder="Planner, ToolExecutor…")
        with t2: trace_status = st.selectbox("Status filter", ["All","success","info","warning","error"])
        visible = [(i,e) for i,e in enumerate(trace,1) if (trace_status=="All" or e.get("status")==trace_status) and (not trace_search or trace_search.lower() in (e.get("agent","")+e.get("message","")).lower())]
        st.caption(f"{len(visible)} matching events · {len(trace)} total events")
        for i,event in visible:
            with st.expander(f"{i:02d}  ·  {event.get('agent','System')}  ·  {event.get('status','info')}"):
                st.write(event.get("message",""))
                if event.get("details"): st.json(event["details"])
        if not trace: st.info("No execution events yet.")
    with tab_tools:
        x,y = st.columns(2)
        with x:
            st.markdown("#### Registered tools")
            for name,meta in agent.tools.descriptions().items():
                with st.expander(name.replace("_"," ").title()):
                    st.write(meta.get("description","")); st.caption("Tags: " + ", ".join(meta.get("tags",[])))
        with y:
            st.markdown("#### Workflow state")
            st.metric("Current node", agent.state.get("node","—"))
            st.metric("Workflow status", agent.state.get("status","—"))
            st.metric("Retry count", agent.state.get("retry_count",0))
            st.json(agent.state)
        st.markdown("#### Short-term memory")
        if agent.history:
            for item in agent.history:
                st.write(f"**{item.get('role','context').title()}:** {item.get('content','')}")
        else: st.info("No conversation history yet.")
else:
    st.markdown("### Your analysis workspace")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("<div class='panel'><div class='eyebrow'>01 · PLAN</div><h3>Task decomposition</h3><p class='small-muted'>Planner builds an ordered workflow for the repository request.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><div class='eyebrow'>02 · EXECUTE</div><h3>Tool orchestration</h3><p class='small-muted'>Selects and runs repository, file, structure and analysis tools.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='panel'><div class='eyebrow'>03 · REFLECT</div><h3>Validate results</h3><p class='small-muted'>Checks report completeness and applies available fallback handling.</p></div>", unsafe_allow_html=True)
    st.info("Enter a public GitHub repository URL above and select Analyse repository to populate the interactive dashboard.")

st.markdown("<div style='text-align:center;color:#71829e;font-size:11px;padding:28px 0 8px'>REPOINSIGHT · LOCAL AGENT WORKSPACE · NO LLM API KEY REQUIRED</div>", unsafe_allow_html=True)
