"""Regression test: the tracker must save the same match score that compare_skills calculated.

Run with: python test_tracker_score.py
No OpenAI call is made. The tools are called the same way the agent calls them.
"""

import asyncio
import importlib.util
import json
import os
import shutil
import sys
import tempfile

from agents.tool_context import ToolContext

import tools

# Which agent file to test (default: agent.py next to this file)
AGENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent.py")
if len(sys.argv) > 1:
    AGENT_FILE = sys.argv[1]
spec = importlib.util.spec_from_file_location("agent_under_test", AGENT_FILE)
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

# The wrong number the model passed in the bug report
WRONG_MODEL_SCORE = 2


def call_tool(tool, run_data: dict, arguments: dict) -> str:
    """Call one agent tool the same way the SDK does during a run."""
    arguments_text = json.dumps(arguments)
    tool_context = ToolContext(
        context=run_data, tool_name=tool.name, tool_call_id="test", tool_arguments=arguments_text
    )
    return asyncio.run(tool.on_invoke_tool(tool_context, arguments_text))


def model_save_arguments(company: str, job_title: str) -> dict:
    """Build save_to_tracker arguments like the model did: with a wrong score, if the tool accepts one."""
    arguments = {"company": company, "job_title": job_title}
    tool_inputs = agent.save_to_tracker.params_json_schema["properties"]
    if "match_score" in tool_inputs:
        arguments["match_score"] = WRONG_MODEL_SCORE
    if "missing_skills" in tool_inputs:
        arguments["missing_skills"] = []
    return arguments


def use_temp_tracker() -> str:
    """Point the tracker at a new empty temp file and return its path."""
    temp_folder = tempfile.mkdtemp()
    tools.TRACKER_FILE = os.path.join(temp_folder, "tracker.json")
    return tools.TRACKER_FILE


def check_score_saved(job_skills: list[str], resume_skills: list[str], expected_score: int) -> None:
    """Compare, save and answer for one analysis. All three scores must be the expected one."""
    use_temp_tracker()
    run_data = {}

    comparison = json.loads(call_tool(agent.compare_skills, run_data, {"job_skills": job_skills, "resume_skills": resume_skills}))
    assert comparison["match_score"] == expected_score, comparison

    call_tool(agent.save_to_tracker, run_data, model_save_arguments("TestCo", f"Role {expected_score}"))
    saved_row = tools.load_tracker()[-1]
    assert saved_row["match_score"] == expected_score, f"tracker saved {saved_row['match_score']}, expected {expected_score}"
    assert saved_row["missing_skills"] == comparison["missing_skills"], saved_row

    # The final answer from the model also carried the wrong score
    model_answer = agent.JobFitResult(
        status="ok", message="Saved to tracker", company="TestCo", job_title=f"Role {expected_score}",
        match_score=WRONG_MODEL_SCORE, matched_skills=[], missing_skills=[], cover_letter="Letter",
    )
    answer = agent.use_comparison(model_answer, run_data)
    assert answer.match_score == saved_row["match_score"], "response and tracker scores differ"
    print(f"PASS: score {expected_score} saved as {saved_row['match_score']}, response {answer.match_score}")


def test_score_100() -> None:
    check_score_saved(["Python", "SQL"], ["python", "SQL", "Excel"], 100)


def test_score_75() -> None:
    check_score_saved(["Python", "SQL", "Excel", "Tableau"], ["Python", "SQL", "Excel"], 75)


def test_save_before_compare() -> None:
    """Without a compare_skills result, nothing is saved."""
    tracker_path = use_temp_tracker()
    message = call_tool(agent.save_to_tracker, {}, model_save_arguments("TestCo", "No Compare"))
    assert not os.path.exists(tracker_path), message
    print(f"PASS: save before compare is refused ({message})")


def test_existing_records_readable() -> None:
    """Old tracker rows still load, and a new save keeps them."""
    real_tracker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.json")
    tracker_path = use_temp_tracker()
    if os.path.exists(real_tracker):
        shutil.copy(real_tracker, tracker_path)
    old_rows = tools.load_tracker()
    for row in old_rows:
        for field in ["date", "company", "job_title", "match_score", "missing_skills"]:
            assert field in row, row

    run_data = {}
    call_tool(agent.compare_skills, run_data, {"job_skills": ["SQL"], "resume_skills": ["SQL"]})
    call_tool(agent.save_to_tracker, run_data, model_save_arguments("TestCo", "Keep Old Rows"))
    new_rows = tools.load_tracker()
    assert new_rows[:len(old_rows)] == old_rows
    assert len(new_rows) == len(old_rows) + 1
    print(f"PASS: {len(old_rows)} existing records readable and kept")


if __name__ == "__main__":
    test_score_100()
    test_score_75()
    test_save_before_compare()
    test_existing_records_readable()
    print("All tracker score tests passed.")
