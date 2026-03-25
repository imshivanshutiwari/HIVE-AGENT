"""Security vulnerability scanner using bandit."""
import logging
import json
import subprocess
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SecurityIssue:
    filepath: str
    line: int
    severity: str   # "HIGH", "MEDIUM", "LOW"
    confidence: str
    test_id: str
    test_name: str
    description: str
    cwe: str = ""


@dataclass
class SecurityScanResult:
    filepath: str
    issues: List[SecurityIssue] = field(default_factory=list)
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_error: Optional[str] = None


class SecurityScanner:
    """Run bandit security scans on Python files."""

    def scan_file(self, filepath: str) -> SecurityScanResult:
        result = SecurityScanResult(filepath=filepath)
        try:
            proc = subprocess.run(
                ["bandit", "-f", "json", "-q", filepath],
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = proc.stdout
            if not output.strip():
                return result

            data = json.loads(output)
            for issue in data.get("results", []):
                si = SecurityIssue(
                    filepath=filepath,
                    line=issue.get("line_number", 0),
                    severity=issue.get("issue_severity", "LOW"),
                    confidence=issue.get("issue_confidence", "LOW"),
                    test_id=issue.get("test_id", ""),
                    test_name=issue.get("test_name", ""),
                    description=issue.get("issue_text", ""),
                    cwe=str(issue.get("issue_cwe", {}).get("id", "")),
                )
                result.issues.append(si)

            result.high_count = sum(1 for i in result.issues if i.severity == "HIGH")
            result.medium_count = sum(1 for i in result.issues if i.severity == "MEDIUM")
            result.low_count = sum(1 for i in result.issues if i.severity == "LOW")

        except subprocess.TimeoutExpired:
            result.scan_error = "Scan timed out"
        except (json.JSONDecodeError, FileNotFoundError) as e:
            result.scan_error = str(e)

        return result

    def scan_directory(self, dirpath: str) -> List[SecurityScanResult]:
        results = []
        for root, dirs, files in os.walk(dirpath):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    results.append(self.scan_file(filepath))
        return results

    def summarize(self, results: List[SecurityScanResult]) -> Dict[str, Any]:
        all_issues = [i for r in results for i in r.issues]
        from collections import Counter
        cwe_counts = Counter(i.cwe for i in all_issues if i.cwe)
        return {
            "total_files_scanned": len(results),
            "total_issues": len(all_issues),
            "high": sum(r.high_count for r in results),
            "medium": sum(r.medium_count for r in results),
            "low": sum(r.low_count for r in results),
            "top_cwes": dict(cwe_counts.most_common(5)),
            "files_with_issues": sum(1 for r in results if r.issues),
        }
