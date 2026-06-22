from ai_operator_controller.dictation_quality import assess_dictation_quality


def test_quality_report_allows_short_high_confidence_send():
    report = assess_dictation_quality(
        raw_text="please send this send",
        clean_text="please send this",
        final_text="please send this",
        requested_send=True,
        output_target="paste",
        transcription_confidence=0.92,
    )

    assert report.confidence == "high"
    assert report.output_allowed is True
    assert report.review_required is False
    assert report.send_allowed is True
    assert report.reasons == ()


def test_quality_report_blocks_low_confidence_auto_send():
    report = assess_dictation_quality(
        raw_text="please send this send",
        clean_text="please send this",
        final_text="please send this",
        requested_send=True,
        output_target="paste",
        transcription_confidence=0.3,
    )

    assert report.confidence == "low"
    assert report.output_allowed is True
    assert report.review_required is True
    assert report.send_allowed is False
    assert "low_transcription_confidence" in report.reasons


def test_quality_report_blocks_long_auto_send():
    long_text = " ".join(["word"] * 50)

    report = assess_dictation_quality(
        raw_text=f"{long_text} send",
        clean_text=long_text,
        final_text=long_text,
        requested_send=True,
        output_target="paste",
        review_long_text_chars=120,
    )

    assert report.confidence == "medium"
    assert report.output_allowed is True
    assert report.review_required is True
    assert report.send_allowed is False
    assert "long_text" in report.reasons


def test_quality_report_blocks_large_postprocess_change():
    report = assess_dictation_quality(
        raw_text="plain local dictation send",
        clean_text="plain local dictation",
        final_text="completely different generated sentence",
        requested_send=True,
        output_target="paste",
        max_postprocess_change_ratio=0.25,
    )

    assert report.confidence == "medium"
    assert report.output_allowed is True
    assert report.review_required is True
    assert report.send_allowed is False
    assert "large_postprocess_change" in report.reasons


def test_quality_report_blocks_prompt_leak_output():
    prompt = (
        "Russian technical dictation for AI workspaces. Preserve terms. "
        "Use natural Russian punctuation."
    )

    report = assess_dictation_quality(
        raw_text="Use natural Russian punctuation.",
        clean_text="Use natural Russian punctuation.",
        final_text="Use natural Russian punctuation.",
        requested_send=False,
        output_target="paste",
        transcription_confidence=0.95,
        blocked_output_phrases=(prompt,),
    )

    assert report.confidence == "low"
    assert report.output_allowed is False
    assert report.send_allowed is False
    assert "blocked_transcript_phrase" in report.reasons


def test_quality_report_blocks_low_input_signal_output():
    report = assess_dictation_quality(
        raw_text="hello from silence",
        clean_text="hello from silence",
        final_text="hello from silence",
        requested_send=False,
        output_target="paste",
        transcription_confidence=0.92,
        low_input_signal=True,
    )

    assert report.confidence == "low"
    assert report.output_allowed is False
    assert report.send_allowed is False
    assert "low_input_signal" in report.reasons
