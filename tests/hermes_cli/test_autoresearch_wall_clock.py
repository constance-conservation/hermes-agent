from hermes_cli.autoresearch_wall_clock import (
    DEFAULT_OUTER_RUNTIME_SECONDS,
    extract_newest_autoresearch_block,
    parse_outer_runtime_seconds_from_text,
    resolve_autoresearch_wall_clock_seconds,
)


def test_default_resolve_matches_doc():
    assert DEFAULT_OUTER_RUNTIME_SECONDS == 600 * 60
    assert resolve_autoresearch_wall_clock_seconds("# empty\n") == DEFAULT_OUTER_RUNTIME_SECONDS


def test_parse_outer_runtime_hours():
    assert parse_outer_runtime_seconds_from_text(
        "Total outer runtime: 10 hours for the full loop."
    ) == 10 * 3600
    assert parse_outer_runtime_seconds_from_text(
        "outer runtime — 2 hours"
    ) == 2 * 3600


def test_parse_outer_runtime_minutes():
    assert parse_outer_runtime_seconds_from_text(
        "Wall-clock budget: 90 minutes"
    ) == 90 * 60


def test_parse_priority_outer_runtime_over_other_hours():
    # "200 hours" spurious vs "outer runtime ... 5 hours"
    text = """
    train.py may run 200 hours
    Total outer runtime for the Hermes loop: 5 hours
    """
    assert parse_outer_runtime_seconds_from_text(text) == 5 * 3600


def test_managed_block_extracted():
    src = """# x
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_START -->
old 1 hour
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_END -->
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_START -->
outer runtime 3 hours
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_END -->
"""
    block = extract_newest_autoresearch_block(src)
    assert "3 hours" in block
    assert "1 hour" not in block


def test_resolve_uses_newest_block():
    src = """<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_START -->
outer runtime 1 hours
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_END -->
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_START -->
outer runtime 4 hours
<!-- HERMES_AUTORESEARCH_INSTRUCTIONS_END -->
"""
    assert resolve_autoresearch_wall_clock_seconds(src) == 4 * 3600
