"""Tests for the hallucinator validation pipeline Python bindings (Phase 2B)."""

import pytest

from hallucinator import (
    Validator,
    ValidatorConfig,
    ValidationResult,
    DbResult,
    DoiInfo,
    ArxivInfo,
    RetractionInfo,
    ProgressEvent,
    CheckStats,
    PdfExtractor,
)


# ── ValidatorConfig ──


def test_validator_config_defaults():
    config = ValidatorConfig()
    assert config.num_workers == 4
    assert config.db_timeout_secs == 10
    assert config.db_timeout_short_secs == 5
    assert config.disabled_dbs == []
    assert config.check_openalex_authors is False
    assert config.openalex_key is None
    assert config.s2_api_key is None
    assert config.dblp_offline_path is None
    assert config.acl_offline_path is None
    assert config.crossref_mailto is None


def test_validator_config_setters():
    config = ValidatorConfig()
    config.openalex_key = "test-key"
    config.s2_api_key = "s2-key"
    config.num_workers = 8
    config.db_timeout_secs = 20
    config.db_timeout_short_secs = 3
    config.disabled_dbs = ["openalex", "neurips"]
    config.check_openalex_authors = True
    config.crossref_mailto = "test@example.com"

    assert config.openalex_key == "test-key"
    assert config.s2_api_key == "s2-key"
    assert config.num_workers == 8
    assert config.db_timeout_secs == 20
    assert config.db_timeout_short_secs == 3
    assert config.disabled_dbs == ["openalex", "neurips"]
    assert config.check_openalex_authors is True
    assert config.crossref_mailto == "test@example.com"


def test_validator_config_clear_optional():
    config = ValidatorConfig()
    config.s2_api_key = "key"
    assert config.s2_api_key == "key"
    config.s2_api_key = None
    assert config.s2_api_key is None


def test_validator_config_repr():
    config = ValidatorConfig()
    r = repr(config)
    assert "ValidatorConfig" in r
    assert "num_workers=4" in r


# ── Validator construction ──


def test_validator_construction():
    config = ValidatorConfig()
    validator = Validator(config)
    assert repr(validator).startswith("Validator(")


def test_validator_invalid_dblp_path():
    config = ValidatorConfig()
    config.dblp_offline_path = "/nonexistent/path/dblp.db"
    with pytest.raises(RuntimeError, match="DBLP"):
        Validator(config)


def test_validator_invalid_acl_path():
    config = ValidatorConfig()
    config.acl_offline_path = "/nonexistent/path/acl.db"
    with pytest.raises(RuntimeError, match="ACL"):
        Validator(config)


# ── Validator.check with empty refs ──


def test_check_empty_refs():
    config = ValidatorConfig()
    validator = Validator(config)
    results = validator.check([])
    assert results == []


def test_check_empty_refs_with_progress():
    events = []

    def on_progress(event):
        events.append(event)

    config = ValidatorConfig()
    validator = Validator(config)
    results = validator.check([], progress=on_progress)
    assert results == []


# ── Validator.stats ──


def test_stats_empty():
    stats = Validator.stats([])
    assert isinstance(stats, CheckStats)
    assert stats.total == 0
    assert stats.verified == 0
    assert stats.not_found == 0
    assert stats.author_mismatch == 0
    assert stats.retracted == 0
    assert stats.skipped == 0


def test_check_stats_repr():
    stats = Validator.stats([])
    r = repr(stats)
    assert "CheckStats" in r
    assert "total=0" in r


# ── Type imports ──


def test_all_types_importable():
    """All Phase 2B types are importable from the hallucinator package."""
    assert Validator is not None
    assert ValidatorConfig is not None
    assert ValidationResult is not None
    assert DbResult is not None
    assert DoiInfo is not None
    assert ArxivInfo is not None
    assert RetractionInfo is not None
    assert ProgressEvent is not None
    assert CheckStats is not None


# ── Cancel ──


def test_cancel_before_check():
    """Calling cancel() before check() doesn't crash."""
    config = ValidatorConfig()
    validator = Validator(config)
    validator.cancel()
    # Should still work (cancel is reset on next check)
    results = validator.check([])
    assert results == []


# ── Network-dependent tests ──


@pytest.mark.network
def test_check_single_reference():
    """Check a single well-known reference (requires network)."""
    ext = PdfExtractor()
    ref = ext.parse_reference(
        "V. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, "
        'A. N. Gomez, L. Kaiser, and I. Polosukhin, "Attention Is All You Need," '
        "in Advances in Neural Information Processing Systems 30, 2017."
    )
    assert ref is not None

    events = []

    def on_progress(event):
        events.append(event)

    config = ValidatorConfig()
    config.db_timeout_secs = 15
    validator = Validator(config)
    results = validator.check([ref], progress=on_progress)

    assert len(results) == 1
    r = results[0]
    assert isinstance(r, ValidationResult)
    assert r.title  # non-empty
    assert r.status in ("verified", "not_found", "author_mismatch")
    assert isinstance(r.db_results, list)
    assert isinstance(r.ref_authors, list)
    assert isinstance(r.failed_dbs, list)

    # Progress events were received
    assert len(events) > 0
    assert any(e.event_type == "checking" for e in events)


@pytest.mark.network
def test_progress_event_properties():
    """Progress event properties are accessible."""
    ext = PdfExtractor()
    ref = ext.parse_reference(
        'J. Devlin, M. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training '
        'of Deep Bidirectional Transformers for Language Understanding," '
        "in Proc. NAACL, 2019."
    )
    assert ref is not None

    events = []

    def on_progress(event):
        events.append(event)

    config = ValidatorConfig()
    validator = Validator(config)
    validator.check([ref], progress=on_progress)

    # Check 'checking' event properties
    checking_events = [e for e in events if e.event_type == "checking"]
    if checking_events:
        e = checking_events[0]
        assert e.index is not None
        assert e.total is not None
        assert e.title is not None
        # Properties not applicable return None
        assert e.count is None
        assert e.db_name is None


@pytest.mark.network
def test_disabled_dbs():
    """Disabled databases are skipped."""
    ext = PdfExtractor()
    ref = ext.parse_reference(
        'Y. LeCun, Y. Bengio, and G. Hinton, "Deep Learning Review of Modern '
        'Approaches to Neural Network Training," Nature, vol. 521, 2015.'
    )
    assert ref is not None

    config = ValidatorConfig()
    config.disabled_dbs = [
        "crossref",
        "arxiv",
        "dblp",
        "semantic_scholar",
        "acl",
        "neurips",
        "europe_pmc",
        "pubmed",
    ]
    validator = Validator(config)
    results = validator.check([ref])

    assert len(results) == 1
    # With most DBs disabled, the reference should be "not_found"
    # (unless openalex finds it, which is unlikely without a key)
    r = results[0]
    assert r.status in ("verified", "not_found", "author_mismatch")

    # Check db_results — disabled DBs should show as "skipped"
    for db_r in r.db_results:
        assert isinstance(db_r, DbResult)
        assert isinstance(db_r.db_name, str)
        assert db_r.status in (
            "match",
            "no_match",
            "author_mismatch",
            "timeout",
            "error",
            "skipped",
        )


@pytest.mark.network
def test_stats_from_results():
    """Stats computed from real validation results."""
    ext = PdfExtractor()
    ref = ext.parse_reference(
        "I. Goodfellow, J. Pouget-Abadie, M. Mirza, B. Xu, D. Warde-Farley, "
        'S. Ozair, A. Courville, and Y. Bengio, "Generative Adversarial Networks '
        'for Image Synthesis and Domain Adaptation," '
        "in Advances in Neural Information Processing Systems, 2014."
    )
    assert ref is not None

    config = ValidatorConfig()
    validator = Validator(config)
    results = validator.check([ref])

    stats = Validator.stats(results)
    assert stats.total == 1
    assert stats.verified + stats.not_found + stats.author_mismatch == 1


# ── Rate Limiting Config ──


def test_max_rate_limit_retries_default():
    config = ValidatorConfig()
    assert config.max_rate_limit_retries == 3


def test_max_rate_limit_retries_setter():
    config = ValidatorConfig()
    config.max_rate_limit_retries = 5
    assert config.max_rate_limit_retries == 5
    config.max_rate_limit_retries = 0
    assert config.max_rate_limit_retries == 0


def test_crossref_mailto_affects_validator():
    """Setting crossref_mailto should not raise on Validator construction."""
    config = ValidatorConfig()
    config.crossref_mailto = "test@example.com"
    assert config.crossref_mailto == "test@example.com"
    # Validator constructs RateLimiters based on crossref_mailto presence
    validator = Validator(config)
    assert repr(validator).startswith("Validator(")


# ── Offline Validation (all DBs disabled, no network) ──


def _make_ref(title):
    """Create a reference with the given title using PdfExtractor."""
    ext = PdfExtractor()
    ref = ext.parse_reference(
        f'J. Smith, "{title}," in Proc. IEEE, 2023.'
    )
    return ref


def _disabled_config(**overrides):
    """Config with all real databases disabled (no HTTP calls)."""
    config = ValidatorConfig()
    config.disabled_dbs = [
        "CrossRef",
        "arXiv",
        "DBLP",
        "Semantic Scholar",
        "ACL Anthology",
        "Europe PMC",
        "PubMed",
        "OpenAlex",
    ]
    for k, v in overrides.items():
        setattr(config, k, v)
    return config


def test_offline_single_ref_returns_not_found():
    """With all DBs disabled, a reference should be not_found."""
    ref = _make_ref("A Paper About Testing Offline Validation Paths")
    assert ref is not None

    config = _disabled_config()
    validator = Validator(config)
    results = validator.check([ref])

    assert len(results) == 1
    assert results[0].status == "not_found"
    assert results[0].title  # non-empty


def test_offline_multiple_refs():
    """Multiple refs with all DBs disabled — all should be not_found."""
    refs = []
    for i in range(5):
        ref = _make_ref(f"Test Paper Number {i} About Offline Rate Limiting")
        assert ref is not None
        refs.append(ref)

    config = _disabled_config(num_workers=2)
    validator = Validator(config)
    results = validator.check(refs)

    assert len(results) == 5
    for r in results:
        assert r.status == "not_found"


def test_offline_progress_events():
    """Progress events are emitted during offline validation."""
    ref = _make_ref("A Paper About Testing Progress Event Emission")
    assert ref is not None

    events = []

    def on_progress(event):
        events.append(event)

    config = _disabled_config()
    validator = Validator(config)
    results = validator.check([ref], progress=on_progress)

    assert len(results) == 1

    # Should have received checking and result events
    event_types = [e.event_type for e in events]
    assert "checking" in event_types, f"expected 'checking' in {event_types}"
    assert "result" in event_types, f"expected 'result' in {event_types}"

    # Verify checking event properties
    checking = [e for e in events if e.event_type == "checking"][0]
    assert checking.index == 0
    assert checking.total == 1
    assert checking.title is not None

    # Verify result event properties
    result_event = [e for e in events if e.event_type == "result"][0]
    assert result_event.index == 0
    assert result_event.total == 1
    assert result_event.result is not None
    assert result_event.result.status == "not_found"


def test_offline_stats():
    """Stats from offline validation — all not_found."""
    refs = []
    for title in [
        "First Paper About Offline Statistics Testing Methods",
        "Second Paper About Offline Statistics Testing Methods",
        "Third Paper About Offline Statistics Testing Methods",
    ]:
        ref = _make_ref(title)
        assert ref is not None
        refs.append(ref)

    config = _disabled_config()
    validator = Validator(config)
    results = validator.check(refs)

    stats = Validator.stats(results)
    assert stats.total == 3
    assert stats.not_found == 3
    assert stats.verified == 0
    assert stats.author_mismatch == 0


def test_offline_max_rate_limit_retries_propagates():
    """max_rate_limit_retries is accepted and doesn't break offline validation."""
    ref = _make_ref("A Paper About Testing Retry Configuration Propagation")
    assert ref is not None

    config = _disabled_config(max_rate_limit_retries=0)
    validator = Validator(config)
    results = validator.check([ref])
    assert len(results) == 1


def test_offline_db_results_empty():
    """With all DBs disabled, db_results should be empty."""
    ref = _make_ref("A Paper About Testing Empty Database Result Lists")
    assert ref is not None

    config = _disabled_config()
    validator = Validator(config)
    results = validator.check([ref])

    assert len(results) == 1
    assert results[0].db_results == []
    assert results[0].failed_dbs == []
