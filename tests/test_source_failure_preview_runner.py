from diagnostics.run_source_failure_preview import CASES


def test_source_failure_cases_are_pinned_https_urls():
    assert [name for name, _ in CASES] == ["manifest-404", "manifest-oversized"]
    assert all(url.startswith("https://raw.githubusercontent.com/") for _, url in CASES)
    assert all("c28700ffda3067384c096da00f72e73be1959ec2" in url for _, url in CASES)
