---
name: clean-code-small-functions
description: 'Refactor code for clean readability with small, single-purpose functions. Use when functions are long, hard to scan, deeply nested, or mixing responsibilities.'
argument-hint: 'Target files/functions and any constraints (language, style, max length)'
---

# Clean Code With Small Functions

## Outcome
Produce readable, testable code by splitting large functions into small, focused units with clear names and shallow control flow.

## When To Use
- A function is hard to explain in one sentence.
- A function mixes parsing, business rules, I/O, and formatting.
- A function has deep nesting or many condition branches.
- Reviews mention readability or maintainability concerns.

## Procedure
1. Define intent and constraints.
- Identify the target file/function, language, and non-negotiables (public API, performance, behavior).

2. Baseline behavior before refactor.
- Read tests and call sites.
- If tests are missing, note key input/output cases to preserve.

3. Find extraction boundaries.
- Mark logical chunks: validation, transformation, decision logic, side effects, serialization.
- Extract one responsibility at a time into a named helper.

4. Apply branching logic during extraction.
- If a block is pure computation, extract to a pure function and return values.
- If a block performs side effects, isolate side effects behind thin boundary functions.
- If conditional logic is deeply nested, use guard clauses or early returns.
- If names are vague, rename to domain terms that reveal intent.

5. Keep abstraction levels consistent.
- A single function should not mix high-level workflow and low-level implementation details.
- Move low-level details to helpers and keep the top function readable as a sequence of steps.

6. Validate and tighten.
- Run tests/lint where available.
- Ensure behavior is unchanged and readability improved.

## Quality Criteria
- Function does one thing and can be described with a single verb phrase.
- Preferred length is small (target <= 15-20 logical lines where practical).
- Nesting depth is low (target <= 2 levels where practical).
- Names are specific and domain-oriented.
- Side effects are explicit and localized.
- Repeated logic is extracted once.
- Public APIs remain stable unless explicitly requested.

## Completion Checklist
- Refactor preserves behavior for known cases.
- New helpers are cohesive and clearly named.
- Main function reads top-down as a simple workflow.
- Tests pass, or missing-test risk is clearly documented.
