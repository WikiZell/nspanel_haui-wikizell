---
title: Panel Torrents
description: qBittorrent live status and bandwidth history on the NSPanel
---

# Panel Torrents

## About

The Torrents panel shows current qBittorrent upload and download speeds, useful
torrent counters, and a recorder-backed bandwidth chart. It draws directly on
the existing full-screen display canvas, so installing this panel does not
require a new Nextion TFT firmware.

## How to configure

Add a **Torrents** panel in the panel editor and select the following entities:

- **Download speed entity** and **Upload speed entity** are required for the live values
  and history lines. Their values should use MB/s.
- **Total torrents entity**, **Seeding torrents entity**, **Errored torrents entity**, and
  **Paused torrents entity** are optional counters shown below the live values.

The default refresh settings are designed for a responsive display without
placing unnecessary load on Home Assistant:

- live values and counters: every 5 seconds
- recorder history chart: every 60 seconds
- chart period: 12 hours

Tap the panel to refresh both the live values and chart immediately. Swipe left
or right to navigate to another panel.

## Recorder requirements

Home Assistant's recorder must include the upload and download speed sensors.
If history is not yet available, the chart uses the sensors' current values and
starts filling with recorded data over time.
