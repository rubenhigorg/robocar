/* health-badge.js — badge flotante del ESTADO DEL ENTORNO, en todas las paginas.
   Se auto-inyecta (arriba-centro), se conecta solo a rosbridge y muestra el escenario activo
   y si esta sano. Clic -> entornos.html (detalle con todos los checks).
   Uso: <script src="health-badge.js"></script> antes de </body>. */
(function(){
  const HOST = location.hostname || "robocar.local";
  const b = document.createElement("a");
  b.id = "rc-health";
  b.href = "entornos.html";
  b.title = "estado del entorno (clic para el detalle)";
  b.textContent = "⚪ …";
  b.style.cssText =
    "position:fixed;top:6px;left:50%;transform:translateX(-50%);z-index:99999;" +
    "font:700 12px ui-monospace,Menlo,Consolas,monospace;padding:.22rem .7rem;border-radius:20px;" +
    "border:1px solid #26323f;background:rgba(11,15,22,.88);color:#93a1b2;text-decoration:none;" +
    "white-space:nowrap;box-shadow:0 2px 10px rgba(0,0,0,.4);-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)";
  function mount(){ if(document.body && !document.getElementById("rc-health")) document.body.appendChild(b); }
  if(document.body) mount(); else addEventListener("DOMContentLoaded", mount);

  function set(txt, col){ b.textContent = txt; b.style.color = col; b.style.borderColor = col; }
  let ws=null;
  function conn(){
    try{ ws = new WebSocket(`ws://${HOST}:9090`); }catch(e){ setTimeout(conn,2000); return; }
    ws.onopen = ()=> ws.send(JSON.stringify({op:"subscribe", topic:"/robocar/health", type:"std_msgs/msg/String"}));
    ws.onclose = ()=>{ set("⚪ sin conexión", "#5c6a7c"); setTimeout(conn,2000); };
    ws.onerror = ()=>{ try{ ws.close(); }catch(e){} };
    ws.onmessage = (ev)=>{ let d; try{ d=JSON.parse(ev.data); }catch(e){ return; }
      if(d.op==="publish" && d.topic==="/robocar/health"){
        try{ const h=JSON.parse(d.msg.data);
          const none = h.scenario==="NINGUNO";
          set((none?"⚪ ":(h.ok?"🟢 ":"🔴 ")) + (h.summary||h.scenario||""),
              none?"#93a1b2":(h.ok?"#39c07f":"#e05a5a"));
        }catch(e){}
      } };
  }
  conn();
})();
