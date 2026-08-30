from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

from ..abstract.component import Component
from ..abstract.haui_event import HAUIEvent
from ..abstract.haui_page import HAUIPage
from ..abstract.haui_panel import HAUIPanel
from ..mapping.descriptor import PageDescriptor, PageOption, _


class TorrentPage(HAUIPage):
    """Full-screen qBittorrent status and twelve-hour bandwidth chart."""

    DESCRIPTOR = PageDescriptor(
        type_key="torrent",
        page_name="blank",
        label=_("Torrents"),
        description=_("qBittorrent status with live speeds and bandwidth history."),
        options=[
            PageOption(
                key="download_entity",
                kind="item",
                domain="sensor",
                label=_("Download speed entity"),
                description=_("Sensor containing the current download speed in MB/s."),
                section=_("Entities"),
            ),
            PageOption(
                key="upload_entity",
                kind="item",
                domain="sensor",
                label=_("Upload speed entity"),
                description=_("Sensor containing the current upload speed in MB/s."),
                section=_("Entities"),
            ),
            PageOption(
                key="total_entity",
                kind="item",
                domain="sensor",
                label=_("Total torrents entity"),
                section=_("Entities"),
            ),
            PageOption(
                key="seeding_entity",
                kind="item",
                domain="sensor",
                label=_("Seeding torrents entity"),
                section=_("Entities"),
            ),
            PageOption(
                key="error_entity",
                kind="item",
                domain="sensor",
                label=_("Errored torrents entity"),
                section=_("Entities"),
            ),
            PageOption(
                key="paused_entity",
                kind="item",
                domain="sensor",
                label=_("Paused torrents entity"),
                section=_("Entities"),
            ),
            PageOption(
                key="history_hours",
                kind="int",
                default=12,
                label=_("History hours"),
                description=_("Number of hours shown in the bandwidth chart."),
                section=_("Refresh"),
            ),
            PageOption(
                key="live_refresh_seconds",
                kind="int",
                default=5,
                label=_("Live refresh interval"),
                description=_("Seconds between live speed and counter updates."),
                section=_("Refresh"),
            ),
            PageOption(
                key="chart_refresh_seconds",
                kind="int",
                default=60,
                label=_("Chart refresh interval"),
                description=_("Seconds between recorder history queries."),
                section=_("Refresh"),
            ),
        ],
        icon="mdi:chart-timeline-variant-shimmer",
        has_header=False,
    )

    COMPONENTS = HAUIPage.COMPONENTS.merge(h_blank=Component(1, "hBlank"))

    COLOR_BACKGROUND = 0
    COLOR_PANEL = 2113
    COLOR_GRID = 8452
    COLOR_MUTED = 31727
    COLOR_TEXT = 65535
    COLOR_DOWNLOAD = 2047
    COLOR_UPLOAD = 2016
    CHART_LEFT = 39
    CHART_TOP = 112
    CHART_RIGHT = 470
    CHART_BOTTOM = 263
    # Forty-eight points keep the graph detailed while bounding the serial
    # command batches sent to the original NSPanel display.
    SAMPLE_COUNT = 48

    def prepare(self) -> None:
        self._download_entity = ""
        self._upload_entity = ""
        self._counter_entities: dict[str, str] = {}
        self._history_hours = 12
        self._live_refresh_seconds = 5
        self._chart_refresh_seconds = 60
        self._live_timer: Any = None
        self._chart_timer: Any = None

    def start_panel(self, panel: HAUIPanel) -> None:
        self._download_entity = self._entity_id(panel.get("download_entity", ""))
        self._upload_entity = self._entity_id(panel.get("upload_entity", ""))
        self._counter_entities = {
            "TOTAL": self._entity_id(panel.get("total_entity", "")),
            "SEED": self._entity_id(panel.get("seeding_entity", "")),
            "ERROR": self._entity_id(panel.get("error_entity", "")),
            "PAUSED": self._entity_id(panel.get("paused_entity", "")),
        }
        self._history_hours = self._bounded_int(panel.get("history_hours", 12), 1, 48, 12)
        self._live_refresh_seconds = self._bounded_int(
            panel.get("live_refresh_seconds", 5), 2, 300, 5
        )
        self._chart_refresh_seconds = self._bounded_int(
            panel.get("chart_refresh_seconds", 60), 15, 3600, 60
        )
        self.on_release({self.COMPONENTS.h_blank: self.callback_refresh})
        self._live_timer = self.app.run_every(
            self._update_live, f"now+{self._live_refresh_seconds}", self._live_refresh_seconds
        )
        self._chart_timer = self.app.run_every(
            self._update_chart,
            f"now+{self._chart_refresh_seconds}",
            self._chart_refresh_seconds,
        )

    def render_panel(self, panel: HAUIPanel) -> None:
        self.send_cmd(f"cls {self.COLOR_BACKGROUND}")
        self._draw_static(panel.get_title("TORRENTS"))
        self._draw_live()
        self._draw_chart()

    def _stop_panel(self, panel: HAUIPanel) -> None:
        for attr in ("_live_timer", "_chart_timer"):
            handle = getattr(self, attr)
            if handle is not None:
                self.app.cancel_timer(handle)
                setattr(self, attr, None)

    def callback_refresh(self, event: HAUIEvent, component: tuple) -> None:
        if self.panel is not None:
            self._draw_live()
            self._draw_chart()

    def _update_live(self, _data: dict | None = None) -> None:
        if self.panel is not None:
            self._draw_live()

    def _update_chart(self, _data: dict | None = None) -> None:
        if self.panel is not None:
            self._draw_chart()

    def _draw_static(self, title: str) -> None:
        with self.rec_cmd:
            self.send_cmd(f"fill 0,0,480,106,{self.COLOR_PANEL}")
            self.send_cmd(self._xstr(12, 7, 456, 28, 2, self.COLOR_TEXT, self.COLOR_PANEL, title))
            self.send_cmd(f"line 10,40,470,40,{self.COLOR_GRID}")
            self.send_cmd(
                self._xstr(
                    12,
                    86,
                    300,
                    20,
                    1,
                    self.COLOR_MUTED,
                    self.COLOR_PANEL,
                    f"BANDWIDTH HISTORY ({self._history_hours}H)",
                )
            )
            self.send_cmd(
                self._xstr(
                    318,
                    86,
                    150,
                    20,
                    1,
                    self.COLOR_DOWNLOAD,
                    self.COLOR_PANEL,
                    "DOWN",
                    align=2,
                )
            )
            self.send_cmd(
                self._xstr(
                    405,
                    86,
                    63,
                    20,
                    1,
                    self.COLOR_UPLOAD,
                    self.COLOR_PANEL,
                    "UP",
                    align=2,
                )
            )

    def _draw_live(self) -> None:
        download = self._read_float(self._download_entity)
        upload = self._read_float(self._upload_entity)
        counters = [
            f"{label} {self._read_text(entity)}" for label, entity in self._counter_entities.items()
        ]
        with self.rec_cmd:
            self.send_cmd(f"fill 0,41,480,44,{self.COLOR_PANEL}")
            self.send_cmd(
                self._xstr(
                    12,
                    44,
                    210,
                    34,
                    2,
                    self.COLOR_DOWNLOAD,
                    self.COLOR_PANEL,
                    f"D {download:.2f} MB/s",
                )
            )
            self.send_cmd(
                self._xstr(
                    250,
                    44,
                    218,
                    34,
                    2,
                    self.COLOR_UPLOAD,
                    self.COLOR_PANEL,
                    f"U {upload:.2f} MB/s",
                    align=2,
                )
            )
            self.send_cmd(
                self._xstr(
                    12, 74, 456, 18, 1, self.COLOR_MUTED, self.COLOR_PANEL, "   ".join(counters)
                )
            )

    def _draw_chart(self) -> None:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=self._history_hours)
        entity_ids = [e for e in (self._download_entity, self._upload_entity) if e]
        history = self.app.get_history(entity_ids, start_time, end_time) if entity_ids else {}
        download = self._sample_series(
            history.get(self._download_entity, []), start_time.timestamp(), end_time.timestamp()
        )
        upload = self._sample_series(
            history.get(self._upload_entity, []), start_time.timestamp(), end_time.timestamp()
        )
        if not any(download):
            download = [self._read_float(self._download_entity)] * self.SAMPLE_COUNT
        if not any(upload):
            upload = [self._read_float(self._upload_entity)] * self.SAMPLE_COUNT
        scale = self._nice_scale(max(download + upload, default=0.0))

        with self.rec_cmd:
            # Clear every area touched by the dynamic chart.  The original
            # NSPanel Nextion display retains pixels between redraws, so only
            # clearing the plot rectangle leaves stale axis/footer glyphs.
            self.send_cmd(
                f"fill 0,{self.CHART_TOP - 8},{self.CHART_LEFT},"
                f"{self.CHART_BOTTOM - self.CHART_TOP + 17},{self.COLOR_BACKGROUND}"
            )
            self.send_cmd(
                f"fill {self.CHART_LEFT},{self.CHART_TOP},"
                f"{self.CHART_RIGHT - self.CHART_LEFT + 1},"
                f"{self.CHART_BOTTOM - self.CHART_TOP + 1},{self.COLOR_BACKGROUND}"
            )
            self.send_cmd(
                f"fill 0,{self.CHART_BOTTOM + 1},480,"
                f"{320 - self.CHART_BOTTOM - 1},{self.COLOR_BACKGROUND}"
            )
            for index in range(5):
                y = self.CHART_TOP + round(index * (self.CHART_BOTTOM - self.CHART_TOP) / 4)
                self.send_cmd(
                    f"line {self.CHART_LEFT},{y},{self.CHART_RIGHT},{y},{self.COLOR_GRID}"
                )
                label = self._format_scale(scale * (4 - index) / 4)
                self.send_cmd(
                    self._xstr(
                        0, y - 8, self.CHART_LEFT - 3, 16, 0, self.COLOR_MUTED, 0, label, align=2
                    )
                )
            self._draw_series(download, scale, self.COLOR_DOWNLOAD)
            self._draw_series(upload, scale, self.COLOR_UPLOAD)
            self.send_cmd(
                self._xstr(8, 270, 100, 18, 0, self.COLOR_MUTED, 0, f"-{self._history_hours}h")
            )
            self.send_cmd(self._xstr(211, 270, 60, 18, 0, self.COLOR_MUTED, 0, "now", align=1))
            self.send_cmd(self._xstr(340, 270, 128, 18, 0, self.COLOR_MUTED, 0, "MB/s", align=2))
            self.send_cmd(
                self._xstr(
                    8,
                    296,
                    460,
                    18,
                    0,
                    self.COLOR_MUTED,
                    0,
                    "Tap to refresh  |  Swipe to navigate",
                    align=1,
                )
            )

    def _draw_series(self, values: list[float], scale: float, color: int) -> None:
        width = self.CHART_RIGHT - self.CHART_LEFT
        height = self.CHART_BOTTOM - self.CHART_TOP
        points = [
            (
                self.CHART_LEFT + round(index * width / (len(values) - 1)),
                self.CHART_BOTTOM - round(min(value, scale) * height / scale),
            )
            for index, value in enumerate(values)
        ]
        for (x1, y1), (x2, y2) in zip(points, points[1:], strict=False):
            self.send_cmd(f"line {x1},{y1},{x2},{y2},{color}")

    def _sample_series(
        self, points: list[tuple[float, str]], start_ts: float, end_ts: float
    ) -> list[float]:
        parsed = sorted(
            (
                (timestamp, value)
                for timestamp, state in points
                if (value := self._parse_float(state)) is not None
            ),
            key=lambda point: point[0],
        )
        if not parsed:
            return [0.0] * self.SAMPLE_COUNT
        sampled: list[float] = []
        cursor = 0
        value = parsed[0][1]
        for index in range(self.SAMPLE_COUNT):
            target = start_ts + (end_ts - start_ts) * index / (self.SAMPLE_COUNT - 1)
            while cursor + 1 < len(parsed) and parsed[cursor + 1][0] <= target:
                cursor += 1
                value = parsed[cursor][1]
            sampled.append(value)
        return sampled

    def _read_float(self, entity_id: str) -> float:
        parsed = self._parse_float(self.app.get_entity_state(entity_id)) if entity_id else None
        return parsed if parsed is not None else 0.0

    def _read_text(self, entity_id: str) -> str:
        state = self.app.get_entity_state(entity_id) if entity_id else None
        return "-" if state in (None, "unknown", "unavailable") else str(state)

    @staticmethod
    def _parse_float(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, parsed) if math.isfinite(parsed) else None

    @staticmethod
    def _nice_scale(value: float) -> float:
        if value <= 0:
            return 0.1
        target = value * 1.1
        magnitude = 10 ** math.floor(math.log10(target))
        normalized = target / magnitude
        step = 1 if normalized <= 1 else 2 if normalized <= 2 else 5 if normalized <= 5 else 10
        return step * magnitude

    @staticmethod
    def _format_scale(value: float) -> str:
        if value == 0:
            return "0"
        if value < 1:
            return f"{value:.2f}".rstrip("0").rstrip(".")
        if value < 10:
            return f"{value:.1f}".rstrip("0").rstrip(".")
        return f"{value:.0f}"

    @staticmethod
    def _entity_id(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("entity_id", value.get("item", "")))
        return str(value or "")

    @staticmethod
    def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
        try:
            return max(minimum, min(maximum, int(value)))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _xstr(
        x: int,
        y: int,
        width: int,
        height: int,
        font: int,
        text_color: int,
        back_color: int,
        text: str,
        align: int = 0,
    ) -> str:
        safe = str(text).replace('"', "'").replace("\\", "/")[:80]
        # sta=1 is solid-color mode.  sta=0 is crop-image mode and copies
        # pixels from the page background, which produces corrupted text
        # boxes on the runtime-drawn blank canvas after repeated refreshes.
        return (
            f'xstr {x},{y},{width},{height},{font},{text_color},{back_color},{align},1,1,"{safe}"'
        )
