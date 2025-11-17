from biotoolsllmannotate.cli.run import validate_biotools_payload


def test_validate_payload_local_mode():
    # Minimal valid entries for local validation path
    payload = [
        {"name": "toolA", "description": "desc", "homepage": "http://example.com"},
        {"name": "toolB", "description": "desc", "homepage": "http://example.org"},
    ]

    class DummyLogger:
        def info(self, *a, **kw):
            pass

        def warning(self, *a, **kw):
            pass

        def error(self, *a, **kw):
            pass

    logger = DummyLogger()
    valid, errs = validate_biotools_payload(
        payload, logger, payload_type="Test payload", use_api=False
    )
    assert len(valid) == 2
    assert errs == []
