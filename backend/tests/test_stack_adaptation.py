import pytest
from backend.app.services.job_analyzer import detect_target_stack
from backend.app.services.project_framing import build_stack_experience_framing_instructions


def test_detect_target_stack_java():
    jd = "We are hiring a Senior Java Developer with Spring Boot 3.3, Microservices, and PostgreSQL."
    assert detect_target_stack(jd) == "java"


def test_detect_target_stack_node():
    jd = "Looking for a Full Stack Engineer with Node.js, React, TypeScript, and Express."
    assert detect_target_stack(jd) == "node"


def test_detect_target_stack_python():
    jd = "Hiring an AI Engineer with Python, FastAPI, PyTorch, and LangChain."
    assert detect_target_stack(jd) == "python"


def test_detect_target_stack_manual_override():
    jd = "We are hiring a Senior Java Developer with Spring Boot."
    # Manual override forces node
    assert detect_target_stack(jd, user_override="node") == "node"


def test_cognizant_java_guardrail_present():
    instructions = build_stack_experience_framing_instructions("node")
    assert "COGNIZANT EXPERIENCE GUARDRAIL" in instructions
    assert "Cognizant MUST remain Java-focused" in instructions
    assert "NEVER replace Java with Node.js or Python" in instructions


def test_usf_stack_adaptation_instructions():
    node_instructions = build_stack_experience_framing_instructions("node")
    assert "Node.js, TypeScript, React" in node_instructions

    java_instructions = build_stack_experience_framing_instructions("java")
    assert "Java, Spring Boot" in java_instructions

    python_instructions = build_stack_experience_framing_instructions("python")
    assert "Python, FastAPI" in python_instructions
