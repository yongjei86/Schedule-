const fs=require('fs'),vm=require('vm'),assert=require('assert');
const elements={};
class E {
 constructor(tag='div'){this.tag=tag;this.children=[];this.style={};this.dataset={};this.attrs={};this.events={};this.value='';this.textContent='';this.disabled=false;this._classes=new Set();this.classList={add:(s)=>this._classes.add(s),remove:(s)=>this._classes.delete(s),toggle:(s,v)=>{v=v===undefined?!this._classes.has(s):v;v?this._classes.add(s):this._classes.delete(s);return v}}}
 append(...items){this.children.push(...items)}
 replaceChildren(...items){this.children=items}
 setAttribute(k,v){this.attrs[k]=v}
 set innerHTML(v){this.html=v;this.svg=new E('svg')}
 get innerHTML(){return this.html||''}
 querySelector(s){return s==='svg'?this.svg:null}
 addEventListener(k,f){this.events[k]=f}
 getBoundingClientRect(){return {left:0,top:0,width:600,height:800}}
 setPointerCapture(){}
 getContext(){return new Proxy({},{get:(o,k)=>o[k]||(o[k]=()=>{})})}
 toDataURL(){return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg=='}
 click(){return this.onclick?.()}
}
const get=id=>elements[id]||(elements[id]=new E(id==='paint'?'canvas':'div'));
const tabs=['studio','wardrobe','runway','looks'].map(view=>{const e=new E('button');e.dataset.view=view;return e});
const modelTabs=['girl','boy'].map(model=>{const e=new E('button');e.dataset.model=model;return e});
const local=new Map();let data={items:[],state:{active:'girl',models:{girl:{name:'지유의 여자 모델',outfit:{},location:'closet'},boy:{name:'지유의 남자 모델',outfit:{},location:'closet'}},gallery:[]}};
const context={window:{addEventListener(){}},document:{body:new E('body'),getElementById:get,createElement:t=>new E(t),querySelector:()=>({content:'token'}),querySelectorAll:s=>s==='[data-view]'?tabs:s==='[data-model]'?modelTabs:s==='#rgb-controls input'?get('rgb-controls').children.flatMap(l=>l.children.filter(e=>e instanceof E)):[]},console,Math,Date,JSON,Map,Set,Promise,innerWidth:1024,crypto:{randomUUID:()=> 'test-look-1'},localStorage:{getItem:k=>local.get(k)||null,setItem:(k,v)=>local.set(k,v),removeItem:k=>local.delete(k)},setTimeout:()=>1,clearTimeout(){},confirm:()=>true,
 fetch:async(url,opts)=>{if(!opts?.body)return {ok:true,json:async()=>JSON.parse(JSON.stringify(data))};const d=JSON.parse(opts.body);if(url.endsWith('/item')){const id=d.id||String(data.items.length+1).padStart(24,'0');data.items=[...data.items.filter(i=>i.id!==id),{...d,id,updated:'2026-10-18'}];return {ok:true,json:async()=>({id})}}data.state=d;return {ok:true,json:async()=>({ok:true})}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/static/riley-fashion-art.js','utf8'),context);vm.runInContext(fs.readFileSync(__dirname+'/static/riley-fashion.js','utf8'),context);
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 await tick();assert.equal(get('save-status').textContent,'새 디자인');
 get('paint').onpointerdown({pointerId:1,clientX:100,clientY:220,preventDefault(){}});
 get('paint').onpointermove({pointerId:1,clientX:270,clientY:290,preventDefault(){}});
 get('paint').onpointerup({pointerId:1});
 await get('wear').onclick();
 assert.ok(data.state.models.girl.outfit.top);assert.equal(data.items[0].strokes.length,1);
 await get('categories').children.find(b=>b.textContent==='하의').onclick();
 await get('templates').children[0].onclick();await get('wear').onclick();
 assert.ok(data.state.models.girl.outfit.top&&data.state.models.girl.outfit.bottom,'layering');
 const outfit=JSON.stringify(data.state.models.girl.outfit);
 await get('send-runway').onclick();assert.equal(data.state.models.girl.location,'runway');assert.equal(get('runway-models').children.length,1);
 const runway=get('runway-models').children[0];assert.equal(runway.children[0].children[0].children.length,2,'front and back views');
 runway.children[0].onclick();
 const back=get('runway-models').children[0].children.at(-1);assert.ok(back.textContent.includes('옷장'));await back.onclick();
 assert.equal(data.state.models.girl.location,'closet');assert.equal(JSON.stringify(data.state.models.girl.outfit),outfit,'return retains outfit');
 await get('send-runway').onclick();assert.equal(get('runway-models').children.length,1,'no duplicate runway resident');
 await tabs[0].onclick();await get('save-look').onclick();assert.equal(data.state.gallery.length,1);
 const look=JSON.stringify(data.state.gallery[0].model.outfit);assert.notEqual(look,outfit,'gallery gets immutable garment copies');
 await tabs[3].onclick();assert.equal(get('looks-grid').children.length,1);
 assert.equal(context.window.FashionArt.templates.length,16);
 console.log('PASS: drawing, layered dressing, front/back runway, return without losing clothes, no duplicate models, immutable look gallery');
})().catch(e=>{console.error(e);process.exitCode=1});
