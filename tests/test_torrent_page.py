"""Tests for the runtime-drawn torrent bandwidth panel."""

from __future__ import annotations

from nspanel_haui.haui.page.torrent import TorrentPage
from nspanel_haui.haui.utils.page import get_page_class_for_panel, get_page_id_for_panel


def _page() -> TorrentPage:
    page = TorrentPage.__new__(TorrentPage)
    page.SAMPLE_COUNT = 5
    return page


def test_sample_series_uses_last_known_value() -> None:
    page = _page()
    sampled = page._sample_series(
        [(0.0, "1"), (5.0, "3"), (10.0, "2")],
        0.0,
        10.0,
    )
    assert sampled == [1.0, 1.0, 3.0, 3.0, 2.0]


def test_sample_series_ignores_invalid_and_negative_states() -> None:
    page = _page()
    sampled = page._sample_series(
        [(0.0, "unavailable"), (3.0, "-4"), (8.0, "0.25")],
        0.0,
        10.0,
    )
    assert sampled == [0.0, 0.0, 0.0, 0.0, 0.25]


def test_nice_scale_leaves_chart_headroom() -> None:
    assert TorrentPage._nice_scale(0.0) == 0.1
    assert TorrentPage._nice_scale(0.15) == 0.2
    assert TorrentPage._nice_scale(4.8) == 10


def test_xstr_sanitizes_nextion_string() -> None:
    command = TorrentPage._xstr(0, 0, 100, 20, 1, 65535, 0, 'A "quote" \\ path')
    assert "\"A 'quote' / path\"" in command
    assert ',0,0,1,1,"' in command


def test_torrent_panel_reuses_blank_canvas_without_replacing_blank_page() -> None:
    assert get_page_class_for_panel("torrent") is TorrentPage
    assert get_page_id_for_panel("torrent") == 1
    assert get_page_id_for_panel("blank") == 1


def test_torrent_chart_command_budget_fits_original_nextion_buffer() -> None:
    # Two series use SAMPLE_COUNT - 1 line commands each.  The chart also
    # sends three clears, five grid lines, five labels and three footer labels.
    command_count = 2 * (TorrentPage.SAMPLE_COUNT - 1) + 16
    assert command_count <= 64
    assert TorrentPage.CHART_CHUNK_SIZE <= 6
    assert TorrentPage.CHART_CHUNK_DELAY >= 0.2


def test_torrent_layout_stays_inside_original_nspanel_bezel() -> None:
    assert TorrentPage.SAFE_LEFT >= 20
    assert TorrentPage.SAFE_RIGHT <= 448
    assert TorrentPage.CHART_LEFT >= TorrentPage.SAFE_LEFT + 24
    assert TorrentPage.CHART_RIGHT <= TorrentPage.SAFE_RIGHT


def test_chart_commands_are_paced_in_small_chunks() -> None:
    page = _page()
    page.CHART_CHUNK_SIZE = 2
    page.CHART_CHUNK_DELAY = 0.25
    page._chart_chunk_timers = []
    sent: list[list[str]] = []
    scheduled: list[tuple[object, float]] = []

    class FakeApp:
        def run_in(self, callback: object, delay: float) -> str:
            scheduled.append((callback, delay))
            return f"timer-{len(scheduled)}"

        def cancel_timer(self, _handle: str) -> None:
            pass

    page.app = FakeApp()  # type: ignore[assignment]
    page.send_cmds = sent.append  # type: ignore[method-assign]

    page._queue_chart_commands(["a", "b", "c", "d", "e"])

    assert sent == [["a", "b"]]
    assert [delay for _, delay in scheduled] == [0.25, 0.5]
    assert page._chart_chunk_timers == ["timer-1", "timer-2"]
