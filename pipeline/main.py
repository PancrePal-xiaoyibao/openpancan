"""
OpenPanCan Pipeline CLI Entry Point

Usage:
    python -m pipeline.main -v <vcf_file> -t <symptom_text> [-o output_dir] [--chromosomes 1-22]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from pipeline.runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenPanCan: Pancreatic Cancer Genomic Analysis Pipeline",
    )
    parser.add_argument(
        "-v", "--vcf", required=True,
        help="Path to input VCF file (somatic or germline variants)",
    )
    parser.add_argument(
        "-t", "--text", required=True,
        help="Clinical symptom / presentation text describing the patient",
    )
    parser.add_argument(
        "-o", "--output", default="outputs",
        help="Output directory for pipeline artifacts (default: outputs)",
    )
    parser.add_argument(
        "--chromosomes", default="1-22",
        help="Chromosomes to process (default: 1-22)",
    )

    args = parser.parse_args()

    vcf_path = Path(args.vcf)
    if not vcf_path.exists():
        print(f"Error: VCF file not found: {vcf_path}", file=sys.stderr)
        sys.exit(1)

    try:
        artifacts = asyncio.run(
            run_pipeline(
                vcf_path=str(vcf_path),
                symptom_text=args.text,
                output_dir=args.output,
                chromosomes=args.chromosomes,
            )
        )
        print("\n✅ Pipeline completed successfully!")
        for key, value in artifacts.items():
            if isinstance(value, str) and value:
                print(f"  {key}: {value}")
            elif isinstance(value, list) and value:
                print(f"  {key}: {len(value)} items")
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"\n❌ Pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
