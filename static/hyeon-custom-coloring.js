/* Extra coloring sheets for Hyeon's coloring page.
   Files are converted to transparent contours and kept only on this device. */
(function () {
  'use strict';
  var picker = document.querySelector('.cl-picker-row');
  var canvas = document.getElementById('cl-canvas');
  if (!picker || !canvas || typeof CL_TEMPLATES === 'undefined') return;

  var KEY = 'hyeon-coloring-custom-sheets-v1';
  var MAX_SHEETS = 8, SIDE = 300;
  var stored = [];
  var contourPixels = null, fillCount = 0;
  var currentImageToken = 0;

  var style = document.createElement('style');
  style.textContent =
    '.cl-import-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}' +
    '.cl-import-button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 15px;border-radius:13px;background:#faeafa;border:2px solid #e8b6e4;color:#7d367d;font-size:14px;font-weight:850;cursor:pointer}' +
    '.cl-import-hint{font-size:12px;color:#6d778b;line-height:1.5}' +
    '.cl-import-tools{display:none;gap:8px;align-items:center;justify-content:center;margin:4px auto 12px}' +
    '.cl-import-tools button{border:1px solid #e0d3de;border-radius:10px;background:#fff;padding:8px 10px;color:#834079;font-size:12px;font-weight:750;cursor:pointer}' +
    '.cl-import-tools span{color:#6d778b;font-size:12px}' +
    '.cl-import-bar input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}' +
    '.cl-pick.cl-custom{border-color:#e6cbe7;background:#fff8ff}' +
    '.cl-pick.cl-custom.on{border-color:#9c51ab;background:#fceaff}';
  document.head.appendChild(style);

  var bar = document.createElement('div');
  bar.className = 'cl-import-bar';
  bar.innerHTML = '<label class="cl-import-button" for="cl-file-upload">🎀 티니핑 등 내 도안 추가</label>' +
      '<input id="cl-file-upload" type="file" accept="image/*" aria-label="색칠할 도안 선택">' +
      '<span class="cl-import-hint">휴대폰 사진에서 흑백 도안 선택 · 이 기기에만 보관</span>';
  picker.parentNode.insertBefore(bar, picker);

  var tools = document.createElement('div');
  tools.className = 'cl-import-tools';
  tools.innerHTML = '<span>그림 속 영역을 톡 눌러 색칠해요</span><button type="button" id="cl-remove-sheet">이 도안 삭제</button>';
  var wrap = document.querySelector('.cl-canvas-wrap');
  wrap.parentNode.insertBefore(tools, wrap.nextSibling);

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

  // The default templates remain unchanged. An imported image uses a separate
  // high-contrast alpha mask to support "tap an enclosed region to fill".
  var originalSelect = clSelect;
  clSelect = function (id) {
    originalSelect(id);
    fillCount = 0;
    contourPixels = null;
    currentImageToken++;
    var token = currentImageToken;
    var imported = clCurrent && clCurrent.isCustomSheet;
    tools.style.display = imported ? 'flex' : 'none';
    if (!imported) return;
    var img = new Image();
    img.onload = function () {
      if (token !== currentImageToken) return;
      var c = document.createElement('canvas');
      c.width = SIDE; c.height = SIDE;
      var ctx = c.getContext('2d', {willReadFrequently:true});
      ctx.drawImage(img, 0, 0, SIDE, SIDE);
      contourPixels = ctx.getImageData(0, 0, SIDE, SIDE).data;
    };
    img.src = clCurrent.contourPng;
  };

  document.getElementById('cl-file-upload').addEventListener('change', function (event) {
    var file = event.target.files && event.target.files[0];
    event.target.value = '';
    if (!file) return;
    if (!file.type || file.type.indexOf('image/') !== 0) {
      alert('그림 파일을 선택해 주세요.'); return;
    }
    var url = URL.createObjectURL(file), source = new Image();
    source.onerror = function () {
      URL.revokeObjectURL(url);
      alert('도안 이미지를 읽을 수 없어요. 다른 사진을 선택해 주세요.');
    };
    source.onload = function () {
      URL.revokeObjectURL(url);
      var c = document.createElement('canvas');
      c.width = SIDE; c.height = SIDE;
      var ctx = c.getContext('2d', {willReadFrequently:true});
      ctx.fillStyle = '#ffffff'; ctx.fillRect(0,0,SIDE,SIDE);
      var scale = Math.min((SIDE-14)/source.width, (SIDE-14)/source.height);
      var w = source.width*scale, h = source.height*scale;
      ctx.drawImage(source, (SIDE-w)/2, (SIDE-h)/2, w, h);
      var pixels = ctx.getImageData(0,0,SIDE,SIDE);
      var data = pixels.data;
      // Remove the white paper. Keep just dark contours on transparent pixels.
      for (var i=0;i<data.length;i+=4) {
        var lum = 0.2126*data[i] + 0.7152*data[i+1] + 0.0722*data[i+2];
        var alpha = Math.max(0,Math.min(255,(185-lum)*4));
        data[i]=28; data[i+1]=29; data[i+2]=39; data[i+3]=alpha;
      }
      ctx.putImageData(pixels,0,0);
      var name = (file.name || '내 도안').replace(/\.[^.]+$/,'').slice(0,12) || '내 도안';
      var item = {id:'sheet-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7),
                  name:name,png:c.toDataURL('image/png')};
      stored.push(item);
      while (stored.length > MAX_SHEETS) {
        var old = stored.shift();
        CL_TEMPLATES.splice(CL_TEMPLATES.findIndex(function(x){return x.id===old.id;}),1);
        var node = document.getElementById('cl-pick-'+old.id);
        if (node) node.remove();
      }
      persist();
      addPicker(item);
      clSelect(item.id);
    };
    source.src = url;
  });

  document.getElementById('cl-remove-sheet').addEventListener('click', function () {
    if (!clCurrent || !clCurrent.isCustomSheet) return;
    var id = clCurrent.id;
    stored = stored.filter(function (x) {return x.id !== id;});
    var idx = CL_TEMPLATES.findIndex(function (x) { return x.id === id; });
    if (idx >= 0) CL_TEMPLATES.splice(idx,1);
    var node = document.getElementById('cl-pick-'+id);
    if (node) node.remove();
    persist();
    clSelect('cat');
  });

  function floodAt(event) {
    if (!contourPixels || !clCtx) return;
    var rect = canvas.getBoundingClientRect();
    var x = Math.floor(((event.clientX-rect.left) / rect.width) * SIDE);
    var y = Math.floor(((event.clientY-rect.top) / rect.height) * SIDE);
    if (x<0 || y<0 || x>=SIDE || y>=SIDE) return;
    var start = y*SIDE+x;
    if (contourPixels[start*4+3] > 110) return;
    var visited = new Uint8Array(SIDE*SIDE);
    var queue = new Int32Array(SIDE*SIDE), head = 0, tail = 1;
    queue[0] = start; visited[start] = 1;
    var neighbors = [1,-1,SIDE,-SIDE];
    while (head < tail) {
      var at = queue[head++];
      var ax = at % SIDE;
      for (var n=0;n<4;n++) {
        if ((n===0 && ax===SIDE-1) || (n===1 && ax===0)) continue;
        var next = at + neighbors[n];
        if (next<0 || next>=SIDE*SIDE || visited[next]) continue;
        if (contourPixels[next*4+3] > 110) continue;
        visited[next] = 1;
        queue[tail++] = next;
      }
    }
    if (tail < 10) return;
    var rgb = clColor.replace('#','');
    var rr=parseInt(rgb.slice(0,2),16), gg=parseInt(rgb.slice(2,4),16), bb=parseInt(rgb.slice(4,6),16);
    var layer = document.createElement('canvas');
    layer.width=SIDE; layer.height=SIDE;
    var layerCtx=layer.getContext('2d');
    var paint=layerCtx.createImageData(SIDE,SIDE);
    for (var k=0;k<tail;k++) {
      var off=queue[k]*4;
      paint.data[off]=rr; paint.data[off+1]=gg; paint.data[off+2]=bb; paint.data[off+3]=255;
    }
    layerCtx.putImageData(paint,0,0);
    clCtx.drawImage(layer,0,0,canvas.width,canvas.height);
    if (++fillCount===5) clChime();
  }

  // Intercept events only when an imported sheet is active. This prevents the
  // original freehand brush from drawing over its "tap to fill" behavior.
  function captureStart(e) {
    if (!clCurrent || !clCurrent.isCustomSheet) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    var touch = e.touches && e.touches[0];
    floodAt(touch || e);
  }
  function captureRemaining(e) {
    if (!clCurrent || !clCurrent.isCustomSheet) return;
    e.preventDefault();
    e.stopImmediatePropagation();
  }
  ['mousedown','touchstart'].forEach(function (type) {
    canvas.addEventListener(type,captureStart,{capture:true,passive:false});
  });
  ['mousemove','mouseup','touchmove','touchend','touchcancel'].forEach(function (type) {
    canvas.addEventListener(type,captureRemaining,{capture:true,passive:false});
  });
})();
