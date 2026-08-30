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
