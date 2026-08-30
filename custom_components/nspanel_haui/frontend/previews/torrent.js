/**
 * NSPanel HAUI - Panel preview: qBittorrent bandwidth history.
 */
import { html } from '../lit-import.js';

export function renderTorrentPreview(_host, panel, _pIdx, _pt) {
  const hours = panel?.history_hours || 12;
  const download = '4,42 16,36 28,39 40,20 52,25 64,15 76,31 88,12 100,19';
  const upload = '4,45 16,44 28,40 40,42 52,35 64,38 76,30 88,36 100,28';
  return {
    content: html`
      <div style="display:flex;flex-direction:column;gap:3px;height:100%;padding:3px;color:#ddd;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:clamp(9px,2.2cqi,14px);">TORRENTS</strong>
          <span style="font-size:clamp(7px,1.7cqi,11px);color:#8f9aa3;">${hours}H</span>
        </div>
        <div style="display:flex;gap:10px;font-size:clamp(8px,1.9cqi,12px);font-weight:600;">
          <span style="color:#27d9ff;">D 0.00 MB/s</span>
          <span style="color:#58e65b;">U 0.15 MB/s</span>
        </div>
        <div style="font-size:clamp(6px,1.35cqi,9px);color:#8f9aa3;white-space:nowrap;">
          TOTAL 633 &nbsp; SEED 2 &nbsp; ERROR 0 &nbsp; PAUSED 604
        </div>
        <svg viewBox="0 0 104 50" preserveAspectRatio="none" style="width:100%;flex:1;min-height:0;">
          <g stroke="#26343e" stroke-width="0.5">
            <line x1="4" y1="12" x2="100" y2="12"/><line x1="4" y1="23" x2="100" y2="23"/>
            <line x1="4" y1="34" x2="100" y2="34"/><line x1="4" y1="45" x2="100" y2="45"/>
          </g>
          <polyline points="${download}" fill="none" stroke="#27d9ff" stroke-width="1.3"/>
          <polyline points="${upload}" fill="none" stroke="#58e65b" stroke-width="1.3"/>
        </svg>
      </div>`,
  };
}
