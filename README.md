AgentFlow – Resumable Agent System for Stock Analysis
Overview

AgentFlow is a production-style agent orchestration system that answers natural-language stock analysis questions using explicit planning, deterministic execution, validation, and persistent state.

This project is not a simple “LLM with tools” demo.
It demonstrates how to build a real agent system with:

structured planning

multi-step execution

validation and retry

resumable state

clear separation between random (LLM) and deterministic (code) components

The system is designed to be debuggable, testable, and restartable, mirroring patterns used in real-world agent platforms.

Architecture

The agent is implemented as a graph-based state machine (LangGraph-style):

router → planner(LLM) → executor → router → answer → critic → router → END

Core Nodes
Node	Responsibility
Planner	Uses an LLM (Gemini) to generate a structured execution plan (JSON)
Router	Central controller that decides which node runs next
Executor	Deterministically executes runtime tools based on the plan
Answer	LLM-generated natural language explanation from computed results
Critic	Validates the answer and triggers retries if needed

The router enables looping, retries, and resumption without hardcoding execution order.

AgentState (Single Source of Truth)

All execution context is stored in a structured AgentState, including:

run_id – unique identifier for resumable runs

query – user query

plans – list of planned actions

next_plan_index – current execution step

next_node – routing decision

data – artifact pointers (paths to stored data)

execution_result – computed metrics

call_stack – execution trace

execution_status – human-readable log

draft_answer / final_answer

critic_result

mode – execution mode (gemini or hack)

State is the only mechanism for control flow and persistence.

Planner vs Executor (Key Design Choice)
Planner (LLM)

Outputs symbolic actions with parameters:

{
  "action": "plan_calculate_return",
  "params": { "ticker": "AAPL", "period": "1y" }
}


Never touches runtime data

Responsible only for deciding what should be done

Executor (Python)

Maps planner actions to real functions via a registry

Executes deterministically

Handles all data loading, computation, and artifact generation

This separation avoids hallucinated tool calls and keeps execution reliable.

Tools
Planner-facing (symbolic)

plan_get_stock_price(ticker, period)

plan_calculate_return(ticker, period)

plan_calculate_vol(ticker, period)

plan_plot(ticker)

Runtime tools

Fetch price data (yfinance)

Compute return and volatility

Generate plots

Save artifacts to disk

Planner actions are validated before execution.

Validation & Retry
Plan validation

Before execution, generated plans are checked for:

valid action names

required parameters

correct execution order (e.g. load data before compute)

valid period formats

Invalid plans trigger replanning.

Answer validation (Critic)

A critic LLM evaluates the generated answer and returns:

{
  "critic_result": {
    "status": "ok" | "retry",
    "reason": "..."
  }
}


If rejected, the system loops back to the answer node.

Persistence & Resumability (v3 feature)

Every run has a run_id

State is checkpointed to:

data/<run_id>/state.json


Large objects (price data, plots) are stored as artifacts:

Parquet for price series

PNG for charts

AgentState stores paths, not raw objects

This allows:

crash recovery

pause & resume

deterministic replay

long-running workflows

Execution Modes
mode="gemini"

Uses Gemini for planner, answer, and critic

Full agent behavior

mode="test"

Bypasses LLMs with deterministic outputs

Used for debugging, testing, and system validation

This prevent LLM variability from blocking system development.

Debugging & Observability

The system is designed to surface agent behavior explicitly:

call_stack – records node execution order

execution_status – human-readable trace

nsteps – execution counter

Persistent checkpoints for inspection

Debugging focuses on state transitions, not call stacks.


Why This Project Matters

This project demonstrates:

agent orchestration (not just tool calling)

explicit control flow via state

separation of planning and execution

handling of LLM unreliability

resumable execution

real-world debugging patterns

It reflects how production agent systems are built, not tutorial examples.



Possible Extensions (Optional)

Database-backed checkpoints (Redis / SQLite)

Evaluation harness & metrics

Intent-level planning

Multi-agent supervisor/worker pattern


Summary

AgentFlow is a reusable agent-system skeleton demonstrating how to build reliable, resumable, and debuggable LLM-driven workflows.

It emphasizes engineering discipline over prompt tricks — exactly what real agent systems require.