"""Security gates must not convert unavailable scans or unfixed HIGHs into PASS."""

import unittest
from scripts.ops.release_security import summarize


class SecurityTests(unittest.TestCase):
    def test_unfixed_high_blocks_release(self):
        report = {
            "Metadata": {"OS": {"Family": "debian", "Name": "13"}},
            "Results": [
                {
                    "Class": "os-pkgs",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "synthetic",
                            "PkgName": "probe",
                            "InstalledVersion": "1",
                            "Severity": "HIGH",
                        }
                    ],
                }
            ],
        }
        result = summarize(report)
        self.assertEqual(result["status"], "FAIL")
        self.assertIsNone(result["findings"][0]["fixed"])

    def test_unavailable_os_scan_does_not_pass(self):
        for report in ({}, {"Results": []}):
            with self.assertRaises(ValueError):
                summarize(report)

    def test_clean_executed_scan_has_limited_claim(self):
        report = {"Metadata": {"OS": {"Family": "debian", "Name": "13"}}, "Results": []}
        self.assertEqual(summarize(report)["status"], "PASS")
