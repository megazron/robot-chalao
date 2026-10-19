// Robot Chalao playground: editor + a Pyodide worker running the real package.
(async function () {
  const $ = (id) => document.getElementById(id);
  const manifest = await (await fetch("manifest.json")).json();

  // ---- syntax highlighting (mirrors the VS Code grammar) ----
  const kw = "maano|rakh|agar|toh|warna|khatam|bas|jab|tak|karo|har|mein|kaam|wapas|de|dikhao|bol|koshish|try|galti|hone|par|import|ruko_loop|tod";
  const verbs = "robot|jodo|chhodo|namespace|param|ghar|jao|seedha|pakdo|speed|planner|rukawat|attach|detach|kahan|hai|kya|IK|FK|nikalo|named|aage|peeche|chalo|ghumo|ruk|map|load|localize|yahan|waypoints|follow|banao|save|obstacle|nazdeek|camera|dekho|photo|lo|object|dhundo|lidar|depth|imu|dabav|padho|battery|kitni|AprilTag|ArUco|TF|pucho|se|sun|bolo|sewa|bulao|action|bhejo|progress|nodes|topics|record|shuru|band|launch|urdf|joint|ko|pe|le|controller|switch|torque|on|off|simulation|gazebo|spawn|rviz|kholo|workspace|limit|deadline|udaan|bharo|utro|height|meter|degree|rad|second|minute|ms|set|get|frame|sehat|theek|warning|kharaab|do";
  CodeMirror.defineSimpleMode("robotchalao", {
    start: [
      { regex: /#.*/, token: "comment" },
      { regex: /"(?:[^\\"]|\\.)*"?/, token: "string" },
      { regex: /\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b|\.\d+\b/, token: "number" },
      { regex: new RegExp("\\b(?:" + kw + ")\\b"), token: "keyword" },
      { regex: /\b(?:sach|jhooth|aur|ya|nahi)\b/, token: "atom" },
      { regex: /\b(?:pose|twist|joints)(?=\s*\()/, token: "type" },
      { regex: new RegExp("\\b(?:" + verbs + ")\\b"), token: "builtin" },
      { regex: /==|!=|<=|>=|[<>+\-*\/%=]/, token: "operator" },
    ],
    meta: { lineComment: "#" },
  });
  const editor = CodeMirror.fromTextArea($("code"), { mode: "robotchalao", theme: "hud", lineNumbers: true, indentUnit: 2, tabSize: 2, lineWrapping: true });
  const cfgEditor = CodeMirror.fromTextArea($("cfg"), { mode: "yaml", theme: "hud", lineNumbers: true, indentUnit: 2, tabSize: 2 });
  const config = await (await fetch("examples/chalao.yaml")).text();
  cfgEditor.setValue(config);

  // ---- examples + shared links ----
  const sel = $("example");
  for (const ex of manifest.examples) sel.add(new Option(ex.title, ex.file));
  async function loadExample(file) { editor.setValue(await (await fetch("examples/" + file)).text()); }
  function fromHash() {
    const m = location.hash.match(/^#code=(.+)$/);
    if (!m) return null;
    try { return decodeURIComponent(escape(atob(m[1].replace(/-/g, "+").replace(/_/g, "/")))); } catch { return null; }
  }
  const shared = fromHash();
  if (shared !== null) { sel.add(new Option("Shared program", ""), 0); sel.value = ""; editor.setValue(shared); }
  else await loadExample(manifest.examples[0].file);
  sel.onchange = () => sel.value && loadExample(sel.value);
  $("share").onclick = async () => {
    const b64 = btoa(unescape(encodeURIComponent(editor.getValue()))).replace(/\+/g, "-").replace(/\//g, "_");
    const url = location.href.split("#")[0] + "#code=" + b64;
    history.replaceState(null, "", url);
    try { await navigator.clipboard.writeText(url); setStatus("link copied", "ok"); } catch { setStatus("link is in the address bar", "ok"); }
  };

  // ---- tabs ----
  const tabs = document.querySelectorAll("[data-tab]");
  function show(name) {
    tabs.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.tab === name)));
    document.querySelectorAll("[data-pane]").forEach((p) => (p.hidden = p.dataset.pane !== name));
    if (name === "cfg") cfgEditor.refresh();
    if (name === "py") transpile();
  }
  tabs.forEach((t) => (t.onclick = () => show(t.dataset.tab)));

  // ---- the worker ----
  let worker, seq = 0;
  const pending = new Map();
  function setStatus(msg, cls) { const s = $("status"); s.textContent = msg; s.className = "status " + (cls || ""); }
  function startWorker() {
    worker = new Worker("worker.js");
    worker.onmessage = (e) => {
      const m = e.data;
      if (m.type === "ready") {
        $("ver").textContent = "v" + m.version + " · playground";
        $("run").disabled = false; $("run").textContent = "▶ Chalao";
        setStatus("ready: Python " + "+ robot_chalao " + m.version + " loaded in your browser", "ok");
        if (!ran) { ran = true; run(); }
      } else if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
      else if (m.type === "error") setStatus("failed to load: " + m.message, "bad");
    };
    worker.postMessage({ type: "boot", wheel: manifest.wheel });
  }
  let ran = false;
  function call(argv) {
    return new Promise((resolve) => {
      const id = ++seq;
      pending.set(id, resolve);
      worker.postMessage({ type: "run", id, argv, code: editor.getValue(), config: cfgEditor.getValue() });
    });
  }

  function render(el, text) {
    el.textContent = "";
    for (const line of text.replace(/\n$/, "").split("\n")) {
      const span = document.createElement("span");
      span.className = line.startsWith("[nakli]") ? "sim" : /^(Bhai|  -->|\s+\d+ \|)/.test(line) ? "err" : "";
      span.textContent = line + "\n";
      el.appendChild(span);
    }
  }

  let killer;
  async function run() {
    if ($("run").disabled) return;
    show("out");
    $("run").disabled = true; $("stop").hidden = false;
    setStatus("running…");
    const t0 = performance.now();
    // a runaway loop can't be interrupted inside Python; Stop restarts the worker
    killer = setTimeout(() => setStatus("still running… press Stop if it loops forever", "bad"), 4000);
    const r = await call(["run", "prog.rc", "--simulate"]);
    clearTimeout(killer);
    $("run").disabled = false; $("stop").hidden = true;
    if (r.type === "error") { render($("out"), r.message); setStatus("internal error", "bad"); return; }
    render($("out"), r.out || "(no output)");
    const ms = Math.round(performance.now() - t0);
    setStatus(r.rc === 0 ? `ok · ${ms} ms · exit 0` : `exit ${r.rc}: see the message above`, r.rc === 0 ? "ok" : "bad");
  }
  async function transpile() {
    if (!worker || $("run").disabled) { $("py").textContent = "(Python is still loading…)"; return; }
    const r = await call(["transpile", "prog.rc"]);
    render($("py"), r.out || r.message || "");
  }
  $("run").onclick = run;
  $("stop").onclick = () => {
    worker.terminate(); pending.clear(); clearTimeout(killer);
    $("stop").hidden = true; $("run").textContent = "Restarting…";
    render($("out"), "Stopped. (Program was still running: a loop without an end?)");
    setStatus("restarting Python…");
    startWorker();
  };
  document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); } });

  // ---- cheat sheet ----
  for (const [code, what] of manifest.cheats) {
    const b = document.createElement("button");
    b.className = "chip";
    b.innerHTML = "<code></code><span></span>";
    b.querySelector("code").textContent = code;
    b.querySelector("span").textContent = what;
    b.onclick = () => { const d = editor.getDoc(); d.replaceRange(code + "\n", { line: d.lastLine() + 1, ch: 0 }); editor.focus(); };
    $("chips").appendChild(b);
  }

  startWorker();
})();
