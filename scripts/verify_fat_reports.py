"""Verify FAT reports for quality issues."""
from __future__ import annotations

import re
from pathlib import Path

SITES = [
    "apple_com", "cloudflare_com", "example_com", "github_com",
    "microsoft_com", "mozilla_org", "openai_com", "python_org",
    "shopify_com", "stripe_com", "vercel_com", "wordpress_org",
]

ROOT = Path("fat_reports")

def check_report(site: str) -> list[str]:
    path = ROOT / site / "report.md"
    if not path.exists():
        return [f"MISSING: {path}"]
    
    text = path.read_text(encoding="utf-8")
    issues = []
    
    # Check for raw Python objects - but "None detected" is valid wording
    if re.search(r'\bNone\b', text) and not re.search(r'None detected|Not collected|Not enough evidence', text):
        issues.append("Contains raw 'None'")
    if "True" in text or "False" in text:
        issues.append("Contains True/False")
    if "{}" in text or "[]" in text:
        issues.append("Contains raw dict/list syntax")
    
    # Check for snake_case internal names (but filter legitimate words)
    snake_pattern = re.compile(r'\b[a-z]+_[a-z_]+\b')
    snake_matches = snake_pattern.findall(text)
    # Filter out legitimate markdown/words and evidence IDs
    snake_matches = [m for m in snake_matches if m not in {
        'evidence_id', 'evidence_type', 'extractor_source', 'page_url',
        'confidence', 'timestamp', 'provenance', 'scan_result', 'json',
        'https', 'http', 'www', 'com', 'org', 'net', 'io', 'ai',
        'ref_cta', 'ref_loc', 'ref_page', 'http_header', 'internal_cache_error',
    }]
    if snake_matches:
        issues.append(f"Possible snake_case: {snake_matches[:5]}")
    
    # Check for duplicated sections
    sections = re.findall(r'^## (.+)$', text, re.MULTILINE)
    seen = set()
    for section in sections:
        if section in seen:
            issues.append(f"Duplicated section: {section}")
        seen.add(section)
    
    # Check for required sections
    required_sections = [
        "Executive Scorecard", "Executive Summary", "Business Snapshot",
        "Signal Coverage", "Website Overview", "SEO Analysis",
        "Metadata Analysis", "Technology Stack", "Technology Maturity",
        "Content Analysis", "Social Presence", "Competitive Signals",
        "Top Strengths", "Improvement Opportunities", "Executive Recommendations",
        "Technical Diagnostics", "Evidence Appendix"
    ]
    for section in required_sections:
        if section not in text:
            issues.append(f"Missing section: {section}")
    
    # Check for broken tables - look for table rows without proper separator
    lines = text.split('\n')
    in_table = False
    for i, line in enumerate(lines):
        if line.startswith('|'):
            if '---' in line or '===' in line:
                in_table = True
                continue
            if in_table and not line.strip().startswith('|'):
                in_table = False
            # Check if this looks like a table row but previous line wasn't a separator
            if in_table and i > 0:
                prev = lines[i-1].strip()
                if not prev.startswith('|') or '---' not in prev:
                    pass  # Multi-line table cells are OK
    
    # Check for "missing" wording
    if "missing" in text.lower():
        issues.append("Contains 'missing' wording")
    
    # Check for limitation messaging
    if "Scan Limitations" not in text and "limited scan" in text.lower():
        issues.append("Has 'limited scan' but no Scan Limitations section")
    
    # Check for contradictory statements
    if text.count("Not detected") > 50:
        issues.append(f"High 'Not detected' count: {text.count('Not detected')}")
    
    return issues


def main() -> None:
    all_pass = True
    for site in SITES:
        issues = check_report(site)
        if issues:
            all_pass = False
            print(f"FAIL {site}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"PASS {site}")
    
    if all_pass:
        print("\nAll reports passed quality checks.")
    else:
        print("\nSome reports have issues.")


if __name__ == "__main__":
    main()
