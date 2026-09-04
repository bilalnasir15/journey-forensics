from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# ============================================================
# DAY 11 — FULL REGRESSION
# ============================================================


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

ANALYTICS_DIR = (
    PROJECT_ROOT / "analytics"
)


# ============================================================
# BRICK ORDER
# ============================================================


BRICKS = [
    "check_day11_brick11_1.py",
    "check_day11_brick11_2.py",
    "check_day11_brick11_3.py",
    "check_day11_brick11_4.py",
    "check_day11_brick11_5.py",
    "check_day11_brick11_6.py",
    "check_day11_brick11_7.py",
    "check_day11_brick11_8.py",
    "check_day11_brick11_9.py",
    "check_day11_brick11_10.py",
    "check_day11_brick11_11.py",
]


# ============================================================
# RESULT MODEL
# ============================================================


class BrickResult:

    def __init__(
        self,
        name: str,
        return_code: int,
        output: str,
    ) -> None:

        self.name = name

        self.return_code = (
            return_code
        )

        self.output = output

    @property
    def passed(self) -> bool:

        return (
            self.return_code == 0
            and
            self._contains_pass_marker()
        )

    def _contains_pass_marker(
        self,
    ) -> bool:

        return (
            "PASSED"
            in self.output.upper()
        )


# ============================================================
# RUN ONE BRICK
# ============================================================


def run_brick(
    script_name: str,
) -> BrickResult:

    script_path = (
        ANALYTICS_DIR
        / script_name
    )

    if not script_path.exists():

        return BrickResult(
            name=script_name,
            return_code=1,
            output=(
                f"Validator file not found: "
                f"{script_path}"
            ),
        )

    try:

        completed = (
            subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                ],
                cwd=str(
                    PROJECT_ROOT
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        )

        output = (
            completed.stdout
            + "\n"
            + completed.stderr
        )

        return BrickResult(
            name=script_name,
            return_code=(
                completed.returncode
            ),
            output=output,
        )

    except Exception as exc:

        return BrickResult(
            name=script_name,
            return_code=1,
            output=str(exc),
        )


# ============================================================
# EXTRACT SUMMARY
# ============================================================


def extract_line(
    output: str,
    prefix: str,
) -> str:

    for line in output.splitlines():

        if line.strip().startswith(
            prefix
        ):

            return line.strip()

    return prefix + " N/A"


# ============================================================
# MAIN
# ============================================================


def main() -> int:

    print()
    print("=" * 72)
    print(
        "DAY 11 — FULL REGRESSION"
    )
    print("=" * 72)

    print(
        f"Project root: {PROJECT_ROOT}"
    )

    print(
        f"Validators: {len(BRICKS)}"
    )

    print()

    results: list[
        BrickResult
    ] = []

    # --------------------------------------------------------
    # Execute every brick
    # --------------------------------------------------------

    for index, brick in enumerate(
        BRICKS,
        start=1,
    ):

        print(
            f"[{index:02d}/{len(BRICKS):02d}] "
            f"Running {brick}"
        )

        result = run_brick(
            brick
        )

        results.append(
            result
        )

        if result.passed:

            print(
                f"    STATUS: PASS"
            )

        else:

            print(
                f"    STATUS: FAIL"
            )

        total_line = extract_line(
            result.output,
            "Total checks:",
        )

        passed_line = extract_line(
            result.output,
            "Passed:",
        )

        failed_line = extract_line(
            result.output,
            "Failed:",
        )

        rate_line = extract_line(
            result.output,
            "Pass rate:",
        )

        print(
            f"    {total_line}"
        )

        print(
            f"    {passed_line}"
        )

        print(
            f"    {failed_line}"
        )

        print(
            f"    {rate_line}"
        )

        print()

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    passed_bricks = sum(
        1
        for result
        in results
        if result.passed
    )

    failed_bricks = (
        len(results)
        - passed_bricks
    )

    print("=" * 72)
    print(
        "DAY 11 — FULL REGRESSION SUMMARY"
    )
    print("=" * 72)

    for index, result in enumerate(
        results,
        start=1,
    ):

        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"{index:02d}. "
            f"{result.name:<38} "
            f"{status}"
        )

    print()

    print(
        f"Total bricks: {len(results)}"
    )

    print(
        f"Passed bricks: {passed_bricks}"
    )

    print(
        f"Failed bricks: {failed_bricks}"
    )

    regression_rate = (
        passed_bricks
        /
        len(results)
        *
        100
        if results
        else 0.0
    )

    print(
        f"Regression pass rate: "
        f"{regression_rate:.2f}%"
    )

    print()

    # ========================================================
    # FAILURE DIAGNOSTICS
    # ========================================================

    failed_results = [
        result
        for result
        in results
        if not result.passed
    ]

    if failed_results:

        print("=" * 72)
        print(
            "FAILED BRICK DETAILS"
        )
        print("=" * 72)

        for result in failed_results:

            print()
            print(
                f"--- {result.name} ---"
            )

            print(
                result.output
            )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    print()

    if failed_bricks == 0:

        print("=" * 72)
        print(
            "DAY 11 — FULL REGRESSION PASSED"
        )
        print("=" * 72)

        print(
            "All Day 11 validators from 11.1 through "
            "11.11 passed successfully."
        )

        return 0

    print("=" * 72)
    print(
        "DAY 11 — FULL REGRESSION FAILED"
    )
    print("=" * 72)

    print(
        "One or more Day 11 validators failed."
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================


if __name__ == "__main__":

    sys.exit(
        main()
    )