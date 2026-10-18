"""Streamlit front end for JobFit Agent. It calls the FastAPI back end."""

import html

import requests
import streamlit as st

# Address of the FastAPI back end
API_URL = "http://127.0.0.1:8000"

# Shown when the back end cannot be reached
BACKEND_DOWN_MESSAGE = "Start the back end first: uvicorn api:app --reload"

# Page names in the sidebar
PAGE_ANALYZE = "Analyze Resume"
PAGE_TRACKER = "My Tracker"
PAGE_ABOUT = "About"

# Page styles: colors, cards, buttons, tags and the score circle
PAGE_STYLE = """
<style>
.stApp {
    background: radial-gradient(circle at 85% 0%, #e6e3ff 0%, rgba(230,227,255,0) 40%),
                radial-gradient(circle at 0% 30%, #e3efff 0%, rgba(227,239,255,0) 35%), #f6f7fd;
}
/* Wide main area, centered on very wide screens, with tighter gaps */
.block-container { padding: 3.5rem 2rem 2rem 2rem; max-width: 1500px; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stVerticalBlock"] { gap: 0.75rem; }
h1, h2, h3, h4 { color: #1b1f3b; }
@media (max-width: 640px) { .block-container { padding: 1rem 0.75rem; } }

/* Dark navy sidebar, a little narrower */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #1c1f45 0%, #2a2160 100%); }
section[data-testid="stSidebar"][aria-expanded="true"] { width: 240px !important; min-width: 240px !important; }
[data-testid="stSidebar"] * { color: #e8e9ff; }
.brand-name { font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-bottom: 0; }
.brand-name span { color: #9d8bff; }
.brand-tagline { font-size: 0.85rem; color: #b9bce0; margin-top: 0; }
/* Sidebar menu buttons: left aligned, the current page in purple */
[class*="st-key-nav_"] button {
    background: transparent; border: none; border-radius: 10px; padding: 10px 14px; justify-content: flex-start;
}
[class*="st-key-nav_"] button:hover { background: rgba(255, 255, 255, 0.08); }
[class*="st-key-nav_"] button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%);
}
[class*="st-key-nav_"] button > div { justify-content: flex-start; width: 100%; }
[class*="st-key-nav_"] button p { font-size: 0.98rem; font-weight: 500; }

/* Hero banner */
.hero {
    background: linear-gradient(120deg, #ffffff 0%, #eef0ff 55%, #e5e0ff 100%);
    border: 1px solid #e3e5f5; border-radius: 18px; padding: 20px 28px; margin-bottom: 4px;
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px;
}
.hero-text { flex: 1 1 420px; }
.hero-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.hero-chip {
    background: #ffffff; border: 1px solid #e3e5f5; border-radius: 12px; padding: 8px 14px;
    font-size: 0.85rem; font-weight: 600; color: #4f46e5; box-shadow: 0 2px 8px rgba(40, 45, 110, 0.06);
}
.hero h1 { font-size: 2rem; margin: 0 0 4px 0; padding: 0; }
.hero h1 span { color: #6d4aff; }
.hero p { color: #4a4f6e; font-size: 1.02rem; margin: 0; }

/* White cards: every bordered container */
[class*="st-key-card_"] {
    background: #ffffff; border: 1px solid #e6e8f4 !important; border-radius: 16px;
    box-shadow: 0 4px 16px rgba(40, 45, 110, 0.06); padding: 16px 18px;
    box-sizing: border-box; max-width: 100%;
}
.card-head { display: flex; align-items: center; gap: 12px; }
.card-badge {
    flex: 0 0 36px; height: 36px; border-radius: 50%; color: #ffffff; font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6 0%, #4f46e5 100%);
    display: flex; align-items: center; justify-content: center;
}
.card-title { font-size: 1.05rem; font-weight: 700; color: #1b1f3b; margin: 0; }
.card-subtitle { font-size: 0.84rem; color: #6b7090; margin: 0; }
.section-label { font-size: 0.9rem; font-weight: 700; color: #1b1f3b; margin: 4px 0 6px 0; }
.score-note { font-size: 0.85rem; color: #4a4f6e; text-align: center; margin: 8px 0 0 0; }
.or-line { text-align: center; color: #9a9eb8; font-size: 0.8rem; margin: 0; }
.file-box {
    border: 1px solid #e6e8f4; background: #f8f9ff; border-radius: 12px;
    padding: 10px 14px; overflow-wrap: anywhere;
}
.file-box b { color: #1b1f3b; }
.file-ok { color: #1f9d55; font-size: 0.85rem; }
.file-wait { color: #6b7090; font-size: 0.85rem; }

/* Big gradient Analyze button */
.st-key-analyze_button button {
    background: linear-gradient(90deg, #8b5cf6 0%, #4f46e5 100%); color: #ffffff;
    border: none; border-radius: 12px; padding: 0.8rem 1rem; font-size: 1.05rem; font-weight: 700;
}
.st-key-analyze_button button:hover { filter: brightness(1.07); color: #ffffff; }
.st-key-analyze_button button p { font-size: 1.05rem; font-weight: 700; }

/* Score circle */
.score-ring {
    width: 130px; height: 130px; border-radius: 50%; margin: 4px auto 8px auto;
    display: flex; align-items: center; justify-content: center;
}
.score-inner {
    width: 102px; height: 102px; border-radius: 50%; background: #ffffff;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.score-number { font-size: 2rem; font-weight: 800; color: #1b1f3b; line-height: 1; }
.score-caption { font-size: 0.8rem; color: #6b7090; }
.score-badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
.stat-row { display: flex; gap: 8px; margin-top: 10px; }
.stat-box { flex: 1; border-radius: 10px; padding: 8px 10px; font-size: 0.8rem; }
.stat-box { text-align: center; }
.stat-box b { font-size: 1.3rem; display: block; }

/* Skill tags that wrap with even spacing */
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
    display: inline-block; padding: 4px 12px; border-radius: 999px;
    font-size: 0.85rem; font-weight: 500; overflow-wrap: anywhere;
}
.tag-green { background: #e7f7ee; color: #1b7a45; border: 1px solid #c4ebd4; }
.tag-red { background: #fdecee; color: #b4232f; border: 1px solid #f7cdd2; }
.empty-note { color: #9a9eb8; font-size: 0.85rem; }
</style>
"""


def error_text(response) -> str:
    """Get the error message from a back-end response."""
    try:
        return str(response.json()["detail"])
    except (ValueError, KeyError):
        return "Something went wrong in the back end. Please try again."


def call_jobfit(job_url: str, job_text: str, resume_file) -> dict:
    """Send the job and resume to POST /jobfit. Return the result or an error."""
    form_data = {"job_url": job_url, "job_text": job_text}
    files = {"resume": (resume_file.name, resume_file.getvalue(), "application/pdf")}
    try:
        response = requests.post(f"{API_URL}/jobfit", data=form_data, files=files, timeout=120)
    except requests.exceptions.ConnectionError:
        return {"error": BACKEND_DOWN_MESSAGE}
    except requests.exceptions.Timeout:
        return {"error": "The agent took too long to answer. Please try again."}

    if response.status_code != 200:
        return {"error": error_text(response)}
    return response.json()


def get_tracker_rows() -> list | None:
    """Get the saved jobs from GET /tracker. Return None if the back end is down."""
    try:
        response = requests.get(f"{API_URL}/tracker", timeout=10)
    except requests.exceptions.RequestException:
        return None
    if response.status_code != 200:
        return None
    return response.json()


def card_heading(title: str, subtitle: str, badge: str = "") -> None:
    """Show a bold card title with a short grey line under it, and an optional number badge."""
    badge_html = ""
    if badge != "":
        badge_html = f'<div class="card-badge">{badge}</div>'
    st.markdown(
        f'<div class="card-head">{badge_html}<div><p class="card-title">{title}</p>'
        f'<p class="card-subtitle">{subtitle}</p></div></div>',
        unsafe_allow_html=True,
    )


def skill_tags(skills: list[str], color: str, empty_message: str) -> str:
    """Build HTML for a row of skill tags in the given color ("green" or "red")."""
    if len(skills) == 0:
        return f'<span class="empty-note">{empty_message}</span>'
    tags_html = ""
    for skill in skills:
        tags_html += f'<span class="tag tag-{color}">{html.escape(skill)}</span>'
    return f'<div class="tag-list">{tags_html}</div>'


def score_colors(score: int) -> tuple[str, str, str, str]:
    """Pick a label, text color, soft background and short note for a match score."""
    if score >= 70:
        return "Strong Match", "#1b7a45", "#e7f7ee", "Your resume covers most of what this job asks for."
    if score >= 40:
        return "Fair Match", "#a15c00", "#fff1dc", "You have relevant skills, but some key areas need work."
    return "Low Match", "#b4232f", "#fdecee", "Many of the required skills are not on your resume yet."


def nav_button(page_name: str, key: str) -> None:
    """Show one sidebar menu button. The current page is shown in purple."""
    button_type = "secondary"
    if st.session_state.get("page", PAGE_ANALYZE) == page_name:
        button_type = "primary"
    if st.button(page_name, key=key, type=button_type, width="stretch"):
        st.session_state["page"] = page_name
        st.rerun()


def show_sidebar() -> str:
    """Show the brand and the page menu in the sidebar. Return the chosen page."""
    with st.sidebar:
        st.markdown(
            '<p class="brand-name">JobFit <span>Agent</span></p>'
            '<p class="brand-tagline">Smart Resume Analyzer</p>',
            unsafe_allow_html=True,
        )
        nav_button(PAGE_ANALYZE, "nav_analyze")
        nav_button(PAGE_TRACKER, "nav_tracker")
        nav_button(PAGE_ABOUT, "nav_about")
        st.divider()
        st.caption("Upload your resume, compare it with a job and get a tailored cover letter.")
    return st.session_state.get("page", PAGE_ANALYZE)


def show_hero() -> None:
    """Show the page heading and subtitle."""
    st.markdown(
        '<div class="hero"><div class="hero-text"><h1>Analyze Your Resume with <span>AI</span></h1>'
        "<p>Give a job link or paste the job description, upload your resume, and get "
        "your match score, missing skills and a tailored cover letter.</p></div>"
        '<div class="hero-chips"><span class="hero-chip">Analyze</span><span class="hero-chip">Match</span>'
        '<span class="hero-chip">Cover Letter</span><span class="hero-chip">Track</span></div></div>',
        unsafe_allow_html=True,
    )


def show_job_card() -> None:
    """Card 1: the job link and the pasted job description."""
    with st.container(border=True, key="card_job", height="stretch"):
        card_heading("Job Details", "Give a job link OR paste the job description. One of them is enough.", "1")
        st.text_input("Job link", key="job_url", placeholder="https://jobs.lever.co/...")
        st.markdown('<p class="or-line">OR</p>', unsafe_allow_html=True)
        st.text_area(
            "Paste job description (use this if the link does not work)",
            key="job_text",
            height=130,
            placeholder="Paste the complete job description here...",
        )


def show_resume_card() -> None:
    """Card 2: the PDF upload with the file name, size and status."""
    with st.container(border=True, key="card_resume", height="stretch"):
        card_heading("Your Resume", "Upload your resume as a PDF file.", "2")
        resume_file = st.file_uploader("Your resume (PDF)", type=["pdf"], key="resume_file")
        if resume_file is None:
            status_html = '<span class="file-wait">No file selected yet.</span>'
        else:
            size_kb = resume_file.size / 1024
            status_html = (
                f"<b>{html.escape(resume_file.name)}</b><br>"
                f'<span class="file-wait">{size_kb:.1f} KB</span> &nbsp; '
                '<span class="file-ok">Ready to analyze</span>'
            )
        st.markdown(f'<div class="file-box">{status_html}</div>', unsafe_allow_html=True)


def start_analysis() -> None:
    """Button click: check the inputs, then mark the analysis as running."""
    st.session_state["input_warning"] = ""
    job_url = st.session_state.get("job_url", "")
    job_text = st.session_state.get("job_text", "")
    if st.session_state.get("resume_file") is None:
        st.session_state["input_warning"] = "Please upload your resume as a PDF."
    elif job_url.strip() == "" and job_text.strip() == "":
        st.session_state["input_warning"] = "Please give a job link or paste the job description text."
    else:
        st.session_state["running"] = True


def show_analyze_button() -> None:
    """Show the Analyze button. It is disabled while the agent works, so it cannot be sent twice."""
    running = st.session_state.get("running", False)
    button_label = "Analyze My Resume"
    if running:
        button_label = "Analyzing..."
    st.button(
        button_label,
        type="primary",
        width="stretch",
        key="analyze_button",
        disabled=running,
        on_click=start_analysis,
    )
    if st.session_state.get("input_warning", "") != "":
        st.warning(st.session_state["input_warning"])


def run_analysis() -> None:
    """Call the back end once, keep the result, then reload the page."""
    # Clear the flag first, so the button comes back even if the call fails
    st.session_state["running"] = False
    with st.spinner("The agent is reading the job and your resume. This can take up to a minute..."):
        st.session_state["result"] = call_jobfit(
            st.session_state["job_url"], st.session_state["job_text"], st.session_state["resume_file"]
        )
    st.rerun()


def show_result(result: dict) -> None:
    """Show the agent's result as cards."""
    # Errors from the back end or the connection
    if "error" in result:
        st.error(result["error"])
        return

    # The agent could not finish, for example the link was blocked
    if result["status"] != "ok":
        st.warning(result["message"])
        return

    # One row: score, skills and the wide cover letter
    card_heading("Analysis Results", "How your profile matches the job requirements.")
    score_column, skills_column, letter_column = st.columns([1, 1.2, 1.8], gap="small")
    with score_column:
        show_score_card(result)
    with skills_column:
        show_skills_card(result)
    with letter_column:
        show_cover_letter(result)
    st.info(result["message"])


def tracker_row_matches(row: dict, search_text: str) -> bool:
    """Return True if the search text is in the company, job title or missing skills."""
    if search_text == "":
        return True
    searchable = f"{row.get('company', '')} {row.get('job_title', '')} {row.get('missing_skills', '')}"
    return search_text.lower() in searchable.lower()


def show_tracker_table(rows: list) -> None:
    """Show the tracker rows as a full-width table."""
    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        column_order=["date", "company", "job_title", "match_score", "missing_skills"],
        column_config={
            "date": st.column_config.TextColumn("Date", width="small"),
            "company": st.column_config.TextColumn("Company", width="medium"),
            "job_title": st.column_config.TextColumn("Job Title", width="medium"),
            "match_score": st.column_config.ProgressColumn(
                "Match Score", min_value=0, max_value=100, format="%d%%", width="small"
            ),
            "missing_skills": st.column_config.ListColumn("Missing Skills", width="large"),
        },
    )


def show_tracker() -> None:
    """Show the saved jobs from GET /tracker, with a search box."""
    with st.container(border=True, key="card_tracker"):
        # Heading on the left, search box on the right
        heading_column, search_column = st.columns([2, 1], vertical_alignment="center")
        with heading_column:
            card_heading("My Application Tracker", "All the jobs you have analyzed.")
        with search_column:
            search_text = st.text_input(
                "Search jobs", placeholder="Search company, job title or skill", label_visibility="collapsed"
            ).strip()

        rows = get_tracker_rows()
        if rows is None:
            st.error(BACKEND_DOWN_MESSAGE)
            return
        if len(rows) == 0:
            st.write("No saved jobs yet.")
            return

        # Keep only the rows that match the search box
        shown_rows = []
        for row in rows:
            if tracker_row_matches(row, search_text):
                shown_rows.append(row)
        st.caption(f"Showing {len(shown_rows)} of {len(rows)} saved jobs")
        show_tracker_table(shown_rows)


def show_about() -> None:
    """Show a short description of the app."""
    with st.container(border=True, key="card_about"):
        card_heading("About JobFit Agent", "How the agent helps you apply for a job.")
        st.markdown(
            "1. Reads the job post (from the link or the pasted text) and picks the must-have skills.\n"
            "2. Reads your resume PDF and picks your skills.\n"
            "3. Compares them to get a match score and the missing skills.\n"
            "4. Writes a short cover letter using only facts from your resume.\n"
            "5. Saves the job to your tracker."
        )
        st.caption("Built with the OpenAI Agents SDK, FastAPI and Streamlit.")


def show_score_card(result: dict) -> None:
    """Show the match score in a circle with the matched and missing counts."""
    score = result["match_score"]
    label, text_color, soft_color, note = score_colors(score)
    matched_count = len(result["matched_skills"])
    missing_count = len(result["missing_skills"])
    ring_style = f"background: conic-gradient({text_color} {score * 3.6}deg, #e6e8f4 0deg);"
    with st.container(border=True, key="card_score"):
        card_heading("Your Match Score", f"{matched_count} of {matched_count + missing_count} job skills found.")
        st.markdown(
            f'<div class="score-ring" style="{ring_style}"><div class="score-inner">'
            f'<span class="score-number">{score}%</span><span class="score-caption">Match Score</span>'
            f'</div></div><div style="text-align:center"><span class="score-badge" '
            f'style="color:{text_color};background:{soft_color}">{label}</span></div>'
            f'<p class="score-note">{note}</p>'
            f'<div class="stat-row"><div class="stat-box" style="background:#e7f7ee;color:#1b7a45">'
            f"<b>{matched_count}</b>Matched</div>"
            f'<div class="stat-box" style="background:#fdecee;color:#b4232f">'
            f"<b>{missing_count}</b>Missing</div>"
            f'<div class="stat-box" style="background:#eef0ff;color:#4f46e5">'
            f"<b>{matched_count + missing_count}</b>Total</div></div>",
            unsafe_allow_html=True,
        )


def show_skills_card(result: dict) -> None:
    """Show matched skills as green tags and missing skills as red tags in one card."""
    matched_html = skill_tags(result["matched_skills"], "green", "No matching skills found in your resume.")
    missing_html = skill_tags(result["missing_skills"], "red", "No missing skills. Your resume covers them all.")
    with st.container(border=True, key="card_skills"):
        card_heading("Skills Analysis", "Skills the job asks for, compared with your resume.")
        st.markdown(
            f'<p class="section-label">Matched skills</p>{matched_html}'
            f'<p class="section-label" style="margin-top:14px">Skills to develop</p>{missing_html}',
            unsafe_allow_html=True,
        )


def show_cover_letter(result: dict) -> None:
    """Show the cover letter with copy and download actions."""
    with st.container(border=True, key="card_letter"):
        subtitle = "Copy it with the icon at the top right of the letter, or download it."
        if result["job_title"] != "":
            subtitle = f"For {html.escape(result['job_title'])}. " + subtitle
        card_heading("Tailored Cover Letter", subtitle)
        st.code(result["cover_letter"], language=None, wrap_lines=True, height=280)
        st.download_button(
            "Download cover letter (.txt)",
            data=result["cover_letter"],
            file_name="cover_letter.txt",
            mime="text/plain",
            width="stretch",
        )


# ----- Page -----
st.set_page_config(page_title="JobFit Agent", layout="wide")
st.markdown(PAGE_STYLE, unsafe_allow_html=True)
page = show_sidebar()

if page == PAGE_ANALYZE:
    show_hero()
    job_column, resume_column = st.columns(2)
    with job_column:
        show_job_card()
    with resume_column:
        show_resume_card()
    show_analyze_button()
    if st.session_state.get("running", False):
        run_analysis()

    # Keep showing the last result when the page reloads
    if "result" in st.session_state:
        show_result(st.session_state["result"])
    show_tracker()
elif page == PAGE_TRACKER:
    show_tracker()
else:
    show_about()
