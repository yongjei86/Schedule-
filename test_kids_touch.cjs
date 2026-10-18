const fs=require('fs'),vm=require('vm'),assert=require('assert');
const listeners={},context={window:{},document:{addEventListener:(name,fn,options)=>{listeners[name]={fn,options}}}};
vm.createContext(context);
const source=fs.readFileSync(__dirname+'/static/kids-touch-lock.js','utf8');
vm.runInContext(source,context);
for(const type of ['gesturestart','gesturechange','gestureend','dblclick']){
 let blocked=false,stopped=false;
 listeners[type].fn({cancelable:true,preventDefault(){blocked=true},stopPropagation(){stopped=true}});
 assert.ok(blocked);assert.ok(!stopped);assert.equal(listeners[type].options.passive,false);
}
for(const count of [1,2,3]){
 let blocked=false;
 listeners.touchmove.fn({cancelable:true,touches:Array(count).fill({}),preventDefault(){blocked=true}});
 assert.equal(blocked,count>1,'only page multi-touch is prevented');
}
for(const ctrlKey of [false,true]){
 let blocked=false;listeners.wheel.fn({cancelable:true,ctrlKey,preventDefault(){blocked=true}});assert.equal(blocked,ctrlKey);
}
vm.runInContext(source,context);
assert.ok(context.window.__kidsPageZoomLocked);
console.log('PASS: Safari page pinch and double-tap blocked, single-finger scrolling retained, event propagation retained for canvas gestures');
