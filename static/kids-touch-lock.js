/* Native page zoom is disabled; game-local pinch handlers still receive events. */
'use strict';
(()=>{
 if(window.__kidsPageZoomLocked)return;
 window.__kidsPageZoomLocked=true;
 const prevent=e=>{if(e.cancelable)e.preventDefault()};
 // iPad/iPhone Safari's native page gesture. Do not stop propagation: canvas
 // touch/pointer handlers must continue receiving their own pinch coordinates.
 ['gesturestart','gesturechange','gestureend'].forEach(type=>
  document.addEventListener(type,prevent,{passive:false}));
 document.addEventListener('touchmove',e=>{
  if(e.touches&&e.touches.length>1)prevent(e);
 },{passive:false});
 document.addEventListener('dblclick',prevent,{passive:false});
 document.addEventListener('wheel',e=>{
  if(e.ctrlKey)prevent(e);
 },{passive:false});
})();
