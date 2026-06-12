from ai_operator_controller.audio_recorder import summarize_audio_samples


def test_summarize_audio_samples_reports_safe_metadata_only():
    summary = summarize_audio_samples(
        [[0.0], [0.5], [-1.0], [1.0]],
        sample_rate=16000,
        dtype="float32",
    )

    assert summary.sample_rate == 16000
    assert summary.frame_count == 4
    assert summary.channel_count == 1
    assert summary.dtype == "float32"
    assert summary.duration_seconds == 0.00025
    assert round(summary.rms, 6) == 0.75
    assert summary.peak_abs == 1.0


def test_summarize_audio_samples_handles_empty_audio():
    summary = summarize_audio_samples([], sample_rate=16000, dtype="float32")

    assert summary.frame_count == 0
    assert summary.channel_count == 0
    assert summary.duration_seconds == 0
    assert summary.rms == 0
    assert summary.peak_abs == 0
