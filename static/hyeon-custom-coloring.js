/* Extra coloring sheets for Hyeon's coloring page.
   Files are converted to transparent contours and kept only on this device. */
(function () {
  'use strict';
  var picker = document.querySelector('.cl-picker-row');
  var canvas = document.getElementById('cl-canvas');
  if (!picker || !canvas || typeof CL_TEMPLATES === 'undefined') return;

  var KEY = 'hyeon-coloring-custom-sheets-v1';
  var MAX_SHEETS = 8;
  var stored = [];

  var style = document.createElement('style');
  style.textContent =
    '.cl-import-tools{display:none;gap:8px;align-items:center;justify-content:center;margin:4px auto 12px}' +
    '.cl-import-tools button{border:1px solid #e0d3de;border-radius:10px;background:#fff;padding:8px 10px;color:#834079;font-size:12px;font-weight:750;cursor:pointer}' +
    '.cl-import-tools span{color:#6d778b;font-size:12px}' +
    '.cl-pick.cl-custom{border-color:#e6cbe7;background:#fff8ff}' +
    '.cl-pick.cl-custom.on{border-color:#9c51ab;background:#fceaff}';
  document.head.appendChild(style);

  var tools = document.createElement('div');
  tools.className = 'cl-import-tools';
  tools.innerHTML = '<button type="button" id="cl-remove-sheet">이 도안 삭제</button>';
  var wrap = document.querySelector('.cl-canvas-wrap');
  wrap.parentNode.insertBefore(tools, wrap.nextSibling);


  // Full-screen tablet-first studio: only the template sidebar may scroll.
  document.body.classList.add('hyeon-coloring-fullscreen');
  var layoutStyle = document.createElement('style');
  layoutStyle.textContent = `
    body.hyeon-coloring-fullscreen {position:fixed;inset:0;width:100%;height:100dvh;overflow:hidden;overscroll-behavior:none}
    body.hyeon-coloring-fullscreen header,
    body.hyeon-coloring-fullscreen .hero,
    body.hyeon-coloring-fullscreen .fab-group {display:none!important}
    body.hyeon-coloring-fullscreen main.wrap {box-sizing:border-box;width:100%;max-width:none;height:100dvh;min-height:0;overflow:hidden;margin:0;padding:10px}
    .cl-studio {height:100%;min-height:0;max-width:1600px;margin:auto;display:grid;grid-template-columns:clamp(210px,26vw,290px) minmax(0,1fr);gap:12px}
    .cl-sidebar {min-height:0;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;background:#fff;border:1px solid #e4e9f0;border-radius:18px;padding:10px;touch-action:pan-y}
    .cl-sidebar .cl-picker-row {display:grid;grid-template-columns:repeat(auto-fill,minmax(65px,1fr));gap:7px;margin:0}
    .cl-sidebar .cl-pick {aspect-ratio:auto;height:73px;min-width:0;border-radius:12px;font-size:27px}
    .cl-sidebar .cl-pick span {font-size:11px;line-height:1.2;word-break:keep-all}
    .cl-workspace {min-height:0;min-width:0;background:#fff;border:1px solid #e4e9f0;border-radius:18px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:8px;overflow:hidden}
    .cl-workspace .hg-topbar {align-self:stretch;margin:0 0 6px;flex:0 0 auto}
    .cl-workspace .hg-btn {width:46px;height:46px;border-radius:12px;font-size:23px}
    .cl-workspace .cl-canvas-wrap {box-sizing:border-box;position:relative;flex:0 1 auto;width:min(100%,calc(100dvh - 165px));max-width:none;max-height:calc(100% - 60px);aspect-ratio:1 / 1;height:auto;margin:auto;border-radius:16px;overflow:hidden}
    .cl-workspace .cl-canvas {width:100%;height:100%;touch-action:none}
    .cl-control-footer {width:100%;flex:0 0 auto;min-height:48px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;padding-top:5px}
    .cl-control-footer .cl-palette {display:flex;gap:clamp(4px,0.7vw,10px);justify-content:center;flex-wrap:wrap;margin:0;max-height:100px;overflow-y:auto;overscroll-behavior:contain}
    .cl-control-footer .cl-swatch {width:clamp(32px,4.2vw,45px);height:clamp(32px,4.2vw,45px);flex:0 0 auto}
    .cl-control-footer .cl-import-tools {margin:0}
    @media(max-width:649px) {
      body.hyeon-coloring-fullscreen main.wrap {padding:5px}
      .cl-studio {display:flex;flex-direction:column;gap:5px}
      .cl-sidebar {flex:0 0 auto;min-height:0;overflow:visible;border-radius:12px;padding:4px;display:flex;flex-direction:column;gap:4px;touch-action:auto}
      .cl-sidebar .cl-picker-row {display:flex;flex-wrap:nowrap;gap:5px;overflow-x:auto;overflow-y:hidden;overscroll-behavior-x:contain;touch-action:pan-x;padding:1px 0 4px}
      .cl-sidebar .cl-pick {height:58px;min-width:66px;width:66px;flex:0 0 66px;font-size:22px}
      .cl-sidebar .cl-pick span {font-size:9px}
      .cl-workspace {flex:1 1 auto;padding:5px;border-radius:12px}
      .cl-workspace .hg-topbar {margin-bottom:2px}
      .cl-workspace .hg-btn {width:38px;height:38px;font-size:19px}
      .cl-workspace .cl-canvas-wrap {width:min(100%,calc(100dvh - 214px));max-height:calc(100% - 45px);border-radius:11px;margin:auto}
      .cl-control-footer {min-height:35px;padding-top:2px}
      .cl-control-footer .cl-swatch {width:31px;height:31px}
    }
    @media(max-height:540px) and (min-width:650px) {
      .cl-workspace .hg-topbar {margin:0}
      .cl-workspace .hg-btn {width:36px;height:36px;font-size:18px}
      .cl-workspace .cl-canvas-wrap {width:min(100%,calc(100dvh - 105px))}
      .cl-control-footer .cl-swatch {width:30px;height:30px}
    }
  `;
  document.head.appendChild(layoutStyle);
  var main = document.querySelector('main.wrap');
  var topbar = document.querySelector('.hg-topbar');
  var palette = document.querySelector('.cl-palette');
  var studio = document.createElement('div'); studio.className = 'cl-studio';
  var sidebar = document.createElement('aside'); sidebar.className = 'cl-sidebar';
  var workspace = document.createElement('section'); workspace.className = 'cl-workspace';
  var footer = document.createElement('div'); footer.className = 'cl-control-footer';
  sidebar.appendChild(picker);
  workspace.appendChild(topbar);
  workspace.appendChild(wrap);
  footer.appendChild(tools); footer.appendChild(palette);
  workspace.appendChild(footer);
  studio.appendChild(sidebar); studio.appendChild(workspace);
  main.appendChild(studio);

  // Canvas pixel backing must follow its visible size for accurate finger drawing.
  // Preserve existing painted strokes if the tablet rotates/resizes.
  function clSyncCanvasSize() {
    var size = Math.max(60, Math.floor(wrap.getBoundingClientRect().width - 4));
    if (!size || (canvas.width === size && canvas.height === size)) return;
    var previous = document.createElement('canvas');
    previous.width = canvas.width; previous.height = canvas.height;
    previous.getContext('2d').drawImage(canvas,0,0);
    if (clClipReady) { clCtx.restore(); clClipReady = false; }
    canvas.width = size; canvas.height = size;
    clCtx = canvas.getContext('2d', {willReadFrequently:true});
    clCtx.lineCap='round'; clCtx.lineJoin='round';
    clCtx.lineWidth = Math.max(18,Math.round(size * 0.064));
    clScale = size / CL_VB;
    if (previous.width && previous.height) clCtx.drawImage(previous,0,0,size,size);
    clApplyClip();
  }
  if (typeof ResizeObserver !== 'undefined') {
    var sizeObserver = new ResizeObserver(function () {clSyncCanvasSize();});
    sizeObserver.observe(wrap);
  }
  requestAnimationFrame(clSyncCanvasSize);

  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(stored.slice(-MAX_SHEETS))); }
    catch (err) { console.warn('Cannot keep more coloring sheets on this device', err); }
  }
  function addPicker(item) {
    if (!item || !item.id || !item.png || typeof item.png !== 'string' || item.png.indexOf('data:image/png;base64,') !== 0) return;
    if (CL_TEMPLATES.some(function (x) { return x.id === item.id; })) return;
    var sheet = {
      id: item.id,
      name: item.name || '내 도안',
      emoji: '🎀',
      svg: '<image href="' + item.png + '" x="0" y="0" width="300" height="300" />',
      regions: [{type:'rect',x:0,y:0,w:300,h:300}],
      isCustomSheet: true,
      contourPng: item.png
    };
    CL_TEMPLATES.push(sheet);
    var b = document.createElement('button');
    b.type = 'button';
    b.id = 'cl-pick-' + item.id;
    b.className = 'cl-pick cl-custom';
    var ico = document.createTextNode('🎀'), span = document.createElement('span');
    span.textContent = sheet.name;
    b.appendChild(ico); b.appendChild(span);
    b.addEventListener('click', function () { clSelect(item.id); });
    picker.appendChild(b);
  }
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (Array.isArray(saved)) stored = saved.slice(-MAX_SHEETS);
  } catch (err) { stored = []; }
  stored.forEach(addPicker);

  // All templates use the same freehand paintbrush; no bucket fill.
  // Imported silhouettes are drawn above the brush strokes as outlines.
  var originalSelect = clSelect;
  clSelect = function (id) {
    originalSelect(id);
    var canDelete = !!(clCurrent && clCurrent.isCustomSheet &&
                       clCurrent.allowDelete !== false);
    tools.style.display = canDelete ? 'flex' : 'none';
    var deleteButton = document.getElementById('cl-remove-sheet');
    if (deleteButton) deleteButton.style.display = canDelete ? '' : 'none';
  };

  document.getElementById('cl-remove-sheet').addEventListener('click', function () {
    if (!clCurrent || !clCurrent.isCustomSheet || clCurrent.allowDelete === false) return;
    var id = clCurrent.id;
    stored = stored.filter(function (x) {return x.id !== id;});
    var idx = CL_TEMPLATES.findIndex(function (x) { return x.id === id; });
    if (idx >= 0) CL_TEMPLATES.splice(idx,1);
    var node = document.getElementById('cl-pick-'+id);
    if (node) node.remove();
    persist();
    clSelect('cat');
  });

  // Initialize a permanent first template with the regular freehand brush.
  if (CL_TEMPLATES[0] && CL_TEMPLATES[0].isCustomSheet) clSelect(CL_TEMPLATES[0].id);
})();
