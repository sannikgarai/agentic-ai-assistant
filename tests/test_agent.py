import pytest


def test_agent_modules_import():
    from app.agent import (
        agent,
        planner,
        task_decomposer,
        state,
        workflow,
        supervisor,
    )

    modules = [
        agent,
        planner,
        task_decomposer,
        state,
        workflow,
        supervisor,
    ]

    for module in modules:
        assert module is not None


def test_agent_module_has_content():
    from app.agent import agent

    public_items = [
        name
        for name in dir(agent)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0


def test_planner_module_imports():
    from app.agent import planner

    assert planner is not None


def test_task_decomposer_module_imports():
    from app.agent import task_decomposer

    assert task_decomposer is not None


def test_state_module_imports():
    from app.agent import state

    assert state is not None


def test_workflow_module_imports():
    from app.agent import workflow

    assert workflow is not None


def test_supervisor_module_imports():
    from app.agent import supervisor

    assert supervisor is not None


def test_agent_tools_registry_imports():
    from app.tools import registry

    assert registry is not None


def test_agent_rag_tool_imports():
    from app.tools import rag_tool

    assert rag_tool is not None


def test_agent_search_tool_imports():
    from app.tools import search_tool

    assert search_tool is not None


def test_agent_document_tool_imports():
    from app.tools import document_tool

    assert document_tool is not None


def test_agent_verification_tool_imports():
    from app.tools import verification_tool

    assert verification_tool is not None


def test_agent_application_tool_imports():
    from app.tools import application_tool

    assert application_tool is not None


def test_agent_notification_tool_imports():
    from app.tools import notification_tool

    assert notification_tool is not None


def test_agent_state_can_be_inspected():
    from app.agent import state

    public_items = [
        name
        for name in dir(state)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0