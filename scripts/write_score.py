"""Collect gate results produced earlier in the CI job (as env vars set
by previous steps) and write a machine-readable score.json artifact,
which the grading-collector repository later reads via the GitHub API.

Env vars consumed (each is "0" for pass, non-zero for fail, unset = skipped):
  GATE_LINT_STATUS
  GATE_TESTS_STATUS
  GATE_COVERAGE_STATUS
  GATE_MIGRATIONS_STATUS
"""
import json
import os

GATES = {
    "lint": "GATE_LINT_STATUS",
    "tests": "GATE_TESTS_STATUS",
    "coverage": "GATE_COVERAGE_STATUS",
    "migrations": "GATE_MIGRATIONS_STATUS",
}


def gate_passed(env_var):
    value = os.environ.get(env_var)
    if value is None:
        return None
    return value.strip() == "0"


def main():
    gates = {name: gate_passed(var) for name, var in GATES.items()}
    evaluated = [v for v in gates.values() if v is not None]
    score_fraction = (sum(1 for v in evaluated if v) / len(evaluated)) if evaluated else 0.0

    result = {
        "lab": os.environ.get("LAB_NAME", "unknown"),
        "commit_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "gates": gates,
        "score_fraction": round(score_fraction, 4),
    }

    with open("score.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
