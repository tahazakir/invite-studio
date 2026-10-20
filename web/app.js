const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const api = async (path, body) => {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
};

const FIELDS = [
  ["event_type", "Event", "select", ["wedding", "engagement", "anniversary", "birthday", "baby_shower"]],
  ["names", "Names", "text"],
  ["date", "Date", "date"],
  ["time", "Time", "time"],
  ["venue", "Venue", "text"],
  ["city", "City", "text"],
  ["headline", "Headline", "text"],
  ["age", "Age", "number"],
  ["rsvp", "RSVP", "text"],
  ["theme", "Theme", "select", []],
];
const THEME_LABEL = t => t.replace("-", " · ");

let THEMES = [];
let method = "finetuned";
let cur = null; // {id, text, order_date, model_fields, field_conf, threshold, fields}
let renderTimer = null;

// ---------- tabs ----------
$$(".tab").forEach(b => b.onclick = () => showTab(b.dataset.tab));
function showTab(name) {
  $$(".tab").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  $$(".view").forEach(v => v.classList.toggle("active", v.id === name));
  if (name === "queue") loadQueue();
  if (name === "monitor") loadStats();
}

$$("#method button").forEach(b => b.onclick = () => {
  method = b.dataset.m;
  $$("#method button").forEach(x => x.classList.toggle("on", x === b));
});

// ---------- form ----------
function buildForm() {
  const form = $("#form");
  form.innerHTML = "";
  for (const [key, label, type, opts] of FIELDS) {
    const row = document.createElement("div");
    row.className = "field";
    row.dataset.key = key;
    let input;
    if (type === "select") {
      input = document.createElement("select");
      for (const o of key === "theme" ? THEMES : opts) input.append(new Option(key === "theme" ? THEME_LABEL(o) : o.replace("_", " "), o));
    } else {
      input = document.createElement("input");
      input.type = type;
    }
    input.name = key;
    input.oninput = () => { row.classList.add("edited"); scheduleRender(); };
    row.innerHTML = `<label>${label}</label><div class="inp"></div>`;
    $(".inp", row).append(input);
    form.append(row);
  }
}

function fieldsToForm(f) {
  for (const [key] of FIELDS) {
    const el = $(`[name=${key}]`);
    let v = f[key];
    if (key === "names") v = (v || []).join(" & ");
    el.value = v ?? "";
    el.closest(".field").classList.remove("edited");
  }
}

function formToFields() {
  const f = {};
  for (const [key] of FIELDS) {
    const v = $(`[name=${key}]`).value.trim();
    if (key === "names") f.names = v ? v.split(/\s*&\s*/).filter(Boolean) : [];
    else if (key === "age") f.age = v ? parseInt(v, 10) : null;
    else f[key] = v || null;
  }
  return f;
}

function showConfidence(conf, threshold) {
  for (const [key] of FIELDS) {
    const row = $(`.field[data-key=${key}]`);
    $(".conf", row)?.remove();
    row.classList.remove("low");
    const c = conf?.[key];
    if (c === undefined) continue;
    const tag = document.createElement("span");
    tag.className = "conf " + (c >= threshold ? "hi" : c >= threshold * 0.6 ? "mid" : "lo");
    tag.textContent = Math.round(c * 100) + "%";
    tag.title = "Lowest token probability in this field";
    $(".inp", row).append(tag);
    if (c < threshold) row.classList.add("low");
  }
}

// ---------- rendering ----------
function showChecks(checks) {
  $("#checks").innerHTML = checks.map(c =>
    `<li class="${c.ok ? "ok" : "bad"}"><span class="ic">${c.ok ? "✓" : "✕"}</span><span>${c.check.replaceAll("_", " ")}${!c.ok && c.detail ? ` <span class="d">(${esc(c.detail)})</span>` : ""}</span></li>`
  ).join("");
}

function showDecision(route, reasons, minConf, threshold) {
  const d = $("#decision");
  d.className = "decision " + (route === "auto_approve" ? "ok" : "warn");
  const confTxt = minConf == null ? "Rule-based extractor: no model confidence" : `Least-confident field: ${Math.round(minConf * 100)}% (threshold ${Math.round(threshold * 100)}%)`;
  d.innerHTML = route === "auto_approve"
    ? `<strong>✓ Auto-approved</strong>Ready to print with no manual design work. <div class="hint">${confTxt}</div>`
    : `<strong>Needs review</strong>Sent to the review queue because:<ul>${reasons.map(r => `<li>${esc(r)}</li>`).join("")}</ul><div class="hint">${confTxt}</div>`;
}

function setCanvas(svg) {
  const c = $("#canvas");
  c.classList.remove("empty", "busy");
  c.innerHTML = svg || "<p>Could not render this order.</p>";
  $("#dl").disabled = !svg;
}

function scheduleRender() {
  clearTimeout(renderTimer);
  renderTimer = setTimeout(rerender, 250);
}

async function rerender(theme) {
  if (!cur) return;
  const fields = formToFields();
  if (theme) { fields.theme = theme; $("[name=theme]").value = theme; $(".field[data-key=theme]").classList.add("edited"); }
  cur.fields = fields;
  const r = await api("/api/render", { fields, text: cur.text, order_date: cur.order_date });
  setCanvas(r.svg);
  showChecks(r.checks);
  markTheme(fields.theme);
  thumbs(fields);
}

async function thumbs(fields) {
  const box = $("#themes");
  const key = JSON.stringify({ ...fields, theme: null });
  if (box.dataset.key === key) return;
  box.dataset.key = key;
  box.innerHTML = THEMES.map(t => `<div class="theme" data-t="${t}"><div class="th"></div><span>${THEME_LABEL(t)}</span></div>`).join("");
  $$(".theme", box).forEach(el => el.onclick = () => rerender(el.dataset.t));
  markTheme(fields.theme);
  await Promise.all(THEMES.map(async t => {
    const r = await api("/api/render", { fields: { ...fields, theme: t } });
    const slot = $(`.theme[data-t="${t}"] .th`, box);
    if (slot && r.svg) slot.innerHTML = r.svg;
  }));
}

function markTheme(t) {
  $$(".theme").forEach(el => el.classList.toggle("sel", el.dataset.t === t));
}

// ---------- process an order ----------
async function processOrder() {
  const text = $("#otext").value.trim();
  if (!text) return;
  $("#go").disabled = true;
  $("#canvas").classList.add("busy");
  $("#status").textContent = method === "finetuned" ? "Running the fine-tuned model…" : "Running regex rules…";
  const t0 = performance.now();
  try {
    const r = await api("/api/process", { text, order_date: $("#odate").value, method });
    cur = { id: r.id, text, order_date: r.order_date, model_fields: r.model_fields, field_conf: r.field_conf, threshold: r.threshold, fields: r.model_fields };
    fieldsToForm(r.model_fields);
    showConfidence(r.field_conf, r.threshold);
    setCanvas(r.svg);
    showChecks(r.checks);
    showDecision(r.route, r.reasons, r.min_conf, r.threshold);
    $("#raw").textContent = r.raw ?? "(rules: no model output)";
    $("#approve").disabled = $("#correct").disabled = r.status !== "pending";
    $("#status").textContent = `Done in ${((performance.now() - t0) / 1000).toFixed(1)}s · order ${r.id}` + (r.status === "pending" ? " · added to review queue" : "");
    $("#themes").dataset.key = "";
    thumbs(r.model_fields);
    refreshCount();
  } catch (e) {
    $("#status").textContent = "Error: " + e.message;
  } finally {
    $("#go").disabled = false;
    $("#canvas").classList.remove("busy");
  }
}
$("#go").onclick = processOrder;

async function resolve() {
  if (!cur) return;
  const o = await api(`/api/orders/${cur.id}/resolve`, { fields: formToFields() });
  $("#status").textContent = o.status === "corrected"
    ? `Saved correction (${o.changed_fields.join(", ")}) to the retraining set.`
    : "Approved as extracted.";
  $("#approve").disabled = $("#correct").disabled = true;
  refreshCount();
}
$("#approve").onclick = resolve;
$("#correct").onclick = resolve;

$("#dl").onclick = () => {
  const svg = $("#canvas svg");
  if (!svg) return;
  const blob = new Blob([svg.outerHTML], { type: "image/svg+xml" });
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `invitation-${cur?.id || "draft"}.svg` });
  a.click();
  URL.revokeObjectURL(a.href);
};

// ---------- queue ----------
async function refreshCount() {
  const q = await api("/api/queue");
  $("#qcount").textContent = q.length;
  return q;
}

async function loadQueue() {
  const q = await refreshCount();
  const list = $("#qlist");
  if (!q.length) { list.innerHTML = `<p class="empty-q">Nothing waiting. Every processed order was approved.</p>`; return; }
  list.innerHTML = q.map(o => `
    <div class="qitem">
      <div><p>${esc(o.text)}</p><div class="why">${o.reasons.map(esc).join(" · ")}</div></div>
      <button class="ghost" data-id="${o.id}">Open</button>
    </div>`).join("");
  $$(".qitem button", list).forEach(b => b.onclick = () => openOrder(b.dataset.id));
}

async function openOrder(id) {
  const o = await api(`/api/orders/${id}`);
  showTab("studio");
  $("#otext").value = o.text;
  $("#odate").value = o.order_date;
  cur = { id: o.id, text: o.text, order_date: o.order_date, model_fields: o.model_fields, field_conf: o.field_conf, threshold: (await api("/api/stats")).threshold };
  fieldsToForm(o.model_fields);
  showConfidence(o.field_conf, cur.threshold);
  setCanvas(o.svg);
  showChecks(o.checks);
  showDecision(o.route, o.reasons, o.min_conf, cur.threshold);
  $("#approve").disabled = $("#correct").disabled = false;
  $("#status").textContent = `Reviewing order ${o.id}`;
  $("#themes").dataset.key = "";
  thumbs(o.model_fields);
}

// ---------- monitoring ----------
async function loadStats() {
  const s = await api("/api/stats");
  const pct = (a, b) => b ? Math.round(100 * a / b) + "%" : "–";
  $("#kpis").innerHTML = [
    [s.total, "orders processed"],
    [pct(s.auto_approved, s.total), "auto-approved"],
    [s.pending, "waiting for review"],
    [s.corrected, "corrected by a human"],
    [s.corrections_logged, "examples queued for retraining"],
  ].map(([v, l]) => `<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join("");

  const max = Math.max(1, ...s.confidence_hist);
  $("#hist").innerHTML = s.confidence_hist.map((n, i) =>
    `<div class="${(i + 1) / 10 <= s.threshold ? "below" : ""}" style="height:${(n / max) * 100}%"><em>${n || ""}</em></div>`).join("");
  $("#hist").insertAdjacentHTML("afterend", "");
  if (!$(".histx")) $("#hist").insertAdjacentHTML("afterend", `<div class="histx"><span>0%</span><span>50%</span><span>100%</span></div>`);

  const bars = (obj) => {
    const e = Object.entries(obj);
    if (!e.length) return `<p class="hint">None yet.</p>`;
    const m = Math.max(...e.map(x => x[1]));
    return e.map(([k, v]) => `<div class="bar"><span>${k.replaceAll("_", " ")}</span><i style="width:${(v / m) * 100}%"></i><span>${v}</span></div>`).join("");
  };
  $("#fails").innerHTML = bars(s.check_failures);
  $("#fixed").innerHTML = bars(s.corrected_fields);

  if (s.eval) {
    const p = v => v == null ? "–" : (v * 100).toFixed(1) + "%";
    const rows = Object.entries(s.eval).filter(([k]) => k !== "threshold");
    $("#evaltbl").innerHTML = `<table><tr><th>method / test set</th><th>n</th><th>full order exact</th><th>names</th><th>auto-approved</th><th>approved accuracy</th></tr>` +
      rows.map(([k, v]) => `<tr><td>${k.replace("test_", "")}</td><td class="num">${v.n}</td><td class="num">${p(v.order_exact)}</td><td class="num">${p(v.fields.names)}</td><td class="num">${p(v.policy.auto_approve_rate)}</td><td class="num">${p(v.policy.approved_accuracy)}</td></tr>`).join("") +
      `</table><p class="hint">"heldout" uses order wordings the model never saw in training. Threshold ${Math.round(s.eval.threshold * 100)}%.</p>`;
  } else {
    $("#evaltbl").innerHTML = `<p class="hint">Run <code>scripts/evaluate.py</code> to fill this in.</p>`;
  }
}

function esc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

// ---------- boot ----------
(async () => {
  $("#odate").value = new Date().toISOString().slice(0, 10);
  THEMES = (await api("/api/library")).themes;
  buildForm();
  const samples = await api("/api/samples");
  for (const [i, s] of samples.entries()) $("#samples").append(new Option(s.text.replace(/\s+/g, " ").slice(0, 70) + "…", i));
  $("#samples").onchange = e => {
    const s = samples[e.target.value];
    if (!s) return;
    $("#otext").value = s.text;
    $("#odate").value = s.order_date;
  };
  refreshCount();
})();
