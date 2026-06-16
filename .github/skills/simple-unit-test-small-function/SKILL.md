---
name: simple-unit-test-small-function
description: 'Create a simple unit test for a small function without changing production code. Prefer pytest style, with unittest-compatible patterns when needed.'
argument-hint: 'Provide function location, expected behavior, edge cases, and preferred test framework (pytest or unittest)'
---

# Simple Unit Test For Small Functions

## Outcome
Generate a minimal, readable unit test for a small function while preserving existing application code.

## Hard Rules
- Do not modify production/source code.
- Only create or edit test files.
- Prefer `pytest` syntax and fixtures.
- Support `unittest` style if the repository already standardizes on it or if requested.
- Keep tests simple, deterministic, and isolated.

## When To Use
- A function is small and mostly pure (single responsibility, predictable output).
- A quick regression test is needed before or after a bug fix.
- You want one focused test file update without refactoring source code.

## Procedure
1. Identify the target function and behavior.
- Read the function signature and return contract.
- Note expected behavior and 1-3 key edge cases.

2. Inspect existing test conventions.
- Prefer existing framework and naming patterns in the project.
- If no pattern exists, default to `pytest`.

3. Create/update test file only.
- Add tests in an appropriate file path (for example `test_<module>.py`).
- Import the function directly.
- Write one happy-path test first, then a small edge-case test if useful.

4. Keep assertions explicit.
- Use clear Arrange/Act/Assert flow.
- Assert exact outputs and expected exceptions.

5. Run tests and report scope.
- Execute targeted tests where possible.
- Confirm no source files were changed.

## Pytest-First Patterns
- Use plain test functions named `test_<behavior>`.
- Use `pytest.mark.parametrize` for compact input/output variants.
- Use `pytest.raises` for error paths.

## Unittest Compatibility Patterns
- Use `unittest.TestCase` only when the codebase standard requires it.
- Use `self.assertEqual`, `self.assertTrue`, and `self.assertRaises`.

## Quality Criteria
- Test validates behavior, not implementation details.
- Test file changes are minimal and focused.
- No production code edits.
- Naming clearly describes intent.
- Test passes locally (or failure reason is clearly stated).

## Completion Checklist
- Added or updated only test file(s).
- Covered at least one primary behavior.
- Covered at least one meaningful edge/error case when applicable.
- Preferred `pytest` unless project constraints required `unittest`.
- Verified test execution outcome.
