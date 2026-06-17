---
name: simple-unit-test-small-function
description: 'Create a simple unit test for a small function without changing production code. Prefer pytest style, with unittest-compatible patterns when needed.'
argument-hint: 'Provide function location, expected behavior, edge cases, and preferred test framework (pytest or unittest)'
---

# Simple Unit Test For Small Functions

## Outcome
Generate simple, readable, deterministic unit tests for Python code without changing production code.

## Hard Rules
- Do not modify production/source code.
- Only create or edit test files.
- Prefer `pytest` syntax and fixtures.
- Support `unittest` style if the repository already standardizes on it or if requested.
- Keep tests simple, deterministic, and isolated.
- Every test must follow Arrange / Act / Assert (AAA).
- Avoid nested functions inside tests.
- Keep one behavior per test.
- Use explicit assertions in every test (no implicit pass-only tests unless explicitly requested).

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
- If no pattern exists, default to `pytest` with class-based grouping.

3. Create/update test file only.
- Add tests in an appropriate file path (for example `test_<module>.py`).
- Group tests in classes by unit/function behavior (for example `class TestParseConfig:`).
- Import target symbols directly or module-level as project style dictates.
- Write one happy-path test first, then small focused edge/error tests.

4. Apply AAA structure consistently.
- Arrange: test data, mocks, fixtures, monkeypatch setup.
- Act: exactly one primary function call under test.
- Assert: explicit behavior checks (`assert`, `pytest.raises`, mock call assertions).

5. Keep logic simple.
- Prefer straightforward setup over abstraction.
- Avoid combining many scenarios in one test.
- Avoid clever loops, branching, or mini-frameworks in tests.
- Use helper fixtures/shared doubles only when they reduce duplication across multiple tests.
- Put reusable test doubles/fixtures in `conftest.py` (pytest) rather than nested/local helper functions.

6. Run tests and report scope.
- Execute targeted tests where possible.
- Confirm no source files were changed.

## Pytest-First Patterns
- Use test classes named `Test<FunctionOrBehavior>`.
- Use methods named `test_<specific_behavior>`.
- Duplicate method names across different classes are acceptable and both tests will run.
- Never duplicate test method names within the same class.
- Never duplicate module-level `test_*` function names in the same file.
- Avoid name collisions because Python redefinition can shadow earlier tests.
- Use `pytest.raises` for error paths.
- Use `monkeypatch` and `Mock` directly and explicitly.
- Use `pytest.mark.parametrize` only when it improves readability; avoid if it obscures AAA clarity.

## Unittest Compatibility Patterns
- Use `unittest.TestCase` only when the codebase standard requires it.
- Preserve AAA thinking even when using `self.assert*` methods.
- Keep each test method focused on one behavior.

## Quality Criteria
- Test validates behavior, not implementation details.
- Test file changes are minimal and focused.
- No production code edits.
- Naming clearly describes intent.
- Test structure is easy to scan in AAA order.
- No unnecessary complicated logic.
- Shared fixtures/doubles are reused appropriately instead of copied repeatedly.
- Test passes locally (or failure reason is clearly stated).

## Completion Checklist
- Added or updated only test file(s).
- Covered at least one primary behavior.
- Covered at least one meaningful edge/error case when applicable.
- Preferred `pytest` unless project constraints required `unittest`.
- Ensured AAA structure in each test.
- Ensured explicit assertions in each test.
- Ensured no nested functions inside tests.
- Ensured test logic remains simple and single-purpose.
- Ensured no duplicate test names in the same class or same module scope.
- Verified test execution outcome.

## Minimal AAA Template (Pytest)
```python
class TestFunctionName:
	def test_specific_behavior(self):
		# Arrange
		input_value = "example"

		# Act
		result = function_under_test(input_value)

		# Assert
		assert result == "expected"
```
