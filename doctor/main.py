"""OpenPanCan Doctor – Health-check CLI for all pancreatic cancer analysis modules."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger("openpancan.doctor")

MODULE_REGISTRY: dict[str, str] = {
    "vep_service":      "modules.vep_service.src.vep_service.check",
    "phenotype_rag":    "modules.phenotype_rag.src.phenotype_rag.check",
    "phenotype_score":  "modules.phenotype_score.src.phenotype_score.check",
    "ppi_score":        "modules.ppi_score.src.ppi_score.check",
    "variant_rank":     "modules.variant_rank.src.variant_rank.check",
    "report":           "modules.report.src.report.check",
    "PanCancerSystem":  "modules.PanCancerSystem.backend.check",
}


@dataclass
class CheckResult:
    module: str
    status: str  # "ok" | "warning" | "error" | "skipped"
    message: str = ""


def worst_status(a: str, b: str) -> str:
    order = {"ok": 0, "warning": 1, "error": 2, "skipped": 3}
    return a if order.get(a, 9) >= order.get(b, 9) else b


def run_checks() -> list[CheckResult]:
    """Run all module health checks and return results."""
    results: list[CheckResult] = []
    for name, module_path in MODULE_REGISTRY.items():
        try:
            import importlib
            mod = importlib.import_module(module_path)
            fn: Callable = getattr(mod, "run_check", None)
            if fn is None:
                results.append(CheckResult(name, "error", "No run_check() function"))
                continue
            result_data = fn()
            if isinstance(result_data, dict):
                results.append(CheckResult(
                    name, result_data.get("status", "ok"),
                    result_data.get("message", ""),
                ))
            else:
                results.append(CheckResult(name, "ok", str(result_data)))
        except ModuleNotFoundError:
            results.append(CheckResult(name, "skipped", "Module not installed"))
        except Exception as exc:
            results.append(CheckResult(name, "error", str(exc)))
    return results


def format_report(results: list[CheckResult]) -> str:
    """Format check results as a readable report."""
    lines = ["=" * 60, "OpenPanCan Doctor – Module Health Check", "=" * 60]
    max_name = max((len(r.module) for r in results), default=0)
    all_ok = True
    for r in results:
        icon = {"ok": "✅", "warning": "⚠️", "error": "❌", "skipped": "⏭️"}.get(r.status, "❓")
        lines.append(f"  {icon} {r.module.ljust(max_name + 2)} {r.status.upper()}")
        if r.message:
            lines.append(f"      {r.message}")
        if r.status in ("error", "warning"):
            all_ok = False
    lines.append("=" * 60)
    lines.append(f"Overall: {'✅ ALL OK' if all_ok else '❌ ISSUES DETECTED'}")
    return "\n".join(lines)


def main() -> None:
    results = run_checks()
    print(format_report(results))
    overall = "error"
    for r in results:
        overall = worst_status(overall, r.status)
    raise SystemExit(0 if overall == "ok" else 1)


if __name__ == "__main__":
    main()
