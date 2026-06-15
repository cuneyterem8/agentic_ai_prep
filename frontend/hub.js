import { runLabAction, formatJson } from "./playground.js";
import { mountDemo, unmountDemo } from "./demo.js";

let hubData = null;
let currentView = "overview";

const els = {
  main: document.getElementById("main-content"),
  pageTitle: document.getElementById("page-title"),
  pageSubtitle: document.getElementById("page-subtitle"),
  stageNavList: document.getElementById("stage-nav-list"),
  sidebar: document.getElementById("sidebar"),
  sidebarToggle: document.getElementById("sidebar-toggle"),
};

async function loadHub() {
  const response = await fetch("/v1/learning-hub");
  if (!response.ok) {
    throw new Error("Learning hub yüklenemedi");
  }
  hubData = await response.json();
  renderStageNav();
  navigate("overview");
}

function renderStageNav() {
  els.stageNavList.innerHTML = "";
  for (const stage of hubData.stages) {
    const btn = document.createElement("button");
    btn.className = "nav-item";
    btn.dataset.view = `stage-${stage.id}`;
    btn.textContent = `${stage.id}. ${stage.title.replace(/^Aşama \d+ — /, "")}`;
    els.stageNavList.appendChild(btn);
  }
}

function setActiveNav(view) {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === view);
  });
}

function navigate(view) {
  currentView = view;
  setActiveNav(view);
  unmountDemo();

  if (view === "overview") {
    renderOverview();
    return;
  }
  if (view === "demo") {
    renderDemo();
    return;
  }
  if (view === "stage-15") {
    renderStage15();
    return;
  }
  if (view === "stage-16") {
    renderStage16();
    return;
  }
  const match = view.match(/^stage-(\d+)$/);
  if (match) {
    const stageId = Number(match[1]);
    const stage = hubData.stages.find((s) => s.id === stageId);
    if (stage) {
      renderStage(stage);
    }
  }
}

function renderOverview() {
  const o = hubData.overview;
  els.pageTitle.textContent = o.title;
  els.pageSubtitle.textContent = o.description;

  els.main.innerHTML = `
    <section class="panel">
      <h3>Temel Prensip</h3>
      <blockquote class="principle">${escapeHtml(o.key_principle)}</blockquote>
      <div class="stat-grid">
        <div class="stat-card"><span class="stat-num">${o.total_stages}</span><span class="stat-label">Aşama</span></div>
        <div class="stat-card"><span class="stat-num">${o.total_interview_questions}</span><span class="stat-label">Mülakat Sorusu</span></div>
        <div class="stat-card"><span class="stat-num">116+</span><span class="stat-label">pytest</span></div>
      </div>
      <h3>Hızlı Başlangıç</h3>
      <pre class="code-block">${o.quick_start.join("\n")}</pre>
      <h3>Aşama Haritası</h3>
      <div class="stage-grid">
        ${o.stage_index
          .map(
            (s) => `
          <button class="stage-card" data-goto="stage-${s.id}">
            <span class="stage-num">${s.id}</span>
            <span class="stage-name">${escapeHtml(s.title.replace(/^Aşama \d+ — /, ""))}</span>
          </button>`
          )
          .join("")}
      </div>
    </section>
  `;

  els.main.querySelectorAll("[data-goto]").forEach((btn) => {
    btn.addEventListener("click", () => navigate(btn.dataset.goto));
  });
}

function renderStage(stage) {
  els.pageTitle.textContent = stage.title;
  els.pageSubtitle.textContent = stage.subtitle || "";

  const tabs = ["Özet", "Sınıflar", "Canlı Test", "Mülakat Q&A"];
  els.main.innerHTML = `
    <div class="tabs" role="tablist">
      ${tabs.map((t, i) => `<button class="tab ${i === 0 ? "active" : ""}" data-tab="${i}">${t}</button>`).join("")}
    </div>
    <div id="tab-content"></div>
  `;

  const tabContent = document.getElementById("tab-content");
  const renderTab = (idx) => {
    document.querySelectorAll(".tab").forEach((t, i) => t.classList.toggle("active", i === idx));
    if (idx === 0) tabContent.innerHTML = renderStageSummary(stage);
    else if (idx === 1) tabContent.innerHTML = renderClasses(stage);
    else if (idx === 2) tabContent.innerHTML = renderLab(stage);
    else tabContent.innerHTML = renderQA(stage.interview_qa || [], stage.title);
    bindLabButtons();
    bindAccordion();
  };

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => renderTab(Number(btn.dataset.tab)));
  });
  renderTab(0);
}

function renderStageSummary(stage) {
  return `
    <section class="panel">
      <p class="lead">${escapeHtml(stage.summary || "")}</p>
      <h3>Konular</h3>
      <ul class="tag-list">${(stage.topics || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
      ${stage.commands?.length ? `<h3>Komutlar</h3><pre class="code-block">${stage.commands.join("\n")}</pre>` : ""}
      ${stage.dod?.length ? `<h3>Definition of Done</h3><ul>${stage.dod.map((d) => `<li>${escapeHtml(d)}</li>`).join("")}</ul>` : ""}
      ${stage.failure_modes?.length ? `<h3>Failure Modes</h3><ul class="warn-list">${stage.failure_modes.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>` : ""}
      ${stage.doc_links?.length ? `<h3>Dokümanlar</h3><ul>${stage.doc_links.map((d) => `<li><code>${escapeHtml(d)}</code></li>`).join("")}</ul>` : ""}
    </section>
  `;
}

function renderClasses(stage) {
  const classes = stage.classes || [];
  if (!classes.length) return `<section class="panel"><p>Sınıf bilgisi yok.</p></section>`;
  return `
    <section class="panel class-list">
      ${classes
        .map(
          (c) => `
        <article class="class-card">
          <header>
            <code class="class-path">${escapeHtml(c.path)}</code>
            <h4>${escapeHtml(c.name)}</h4>
          </header>
          <p>${escapeHtml(c.purpose)}</p>
          <div class="symbols">
            ${(c.key_symbols || []).map((s) => `<span class="symbol-tag">${escapeHtml(s)}</span>`).join("")}
          </div>
          ${renderSymbolDetails(c.symbols_detail || [])}
        </article>`
        )
        .join("")}
    </section>
  `;
}

function renderSymbolDetails(details) {
  if (!details.length) return "";
  return `
    <div class="symbol-details">
      ${details
        .map(
          (item) => `
        <details class="symbol-detail">
          <summary>
            <span class="symbol-detail-chevron" aria-hidden="true">▶</span>
            <code>${escapeHtml(item.name)}</code>
            <span class="symbol-detail-hint">Python implementasyonu — tıkla</span>
          </summary>
          <div class="symbol-detail-body">
            <pre class="code-block symbol-code">${escapeHtml(item.code)}</pre>
            <h5>Nasıl kullanılır?</h5>
            <p class="symbol-usage">${escapeHtml(item.usage)}</p>
          </div>
        </details>`
        )
        .join("")}
    </div>
  `;
}

function renderLab(stage) {
  const actions = stage.lab_actions || [];
  return `
    <section class="panel lab-panel">
      <p class="meta">Aşağıdaki butonlar gerçek API'yi çağırır. Sonuç altta görünür.</p>
      ${actions.length ? actions.map((a) => renderLabAction(a)).join("") : "<p>Bu aşama için canlı test tanımlı değil.</p>"}
      <div class="lab-custom">
        <h3>Özel Prompt / Mesaj</h3>
        <textarea id="custom-prompt" rows="3" placeholder="Kendi mesajınızı yazın..."></textarea>
        <div class="lab-custom-actions">
          <button class="lab-btn" data-custom="classify">Classify</button>
          <button class="lab-btn" data-custom="workflow">Workflow</button>
          <button class="lab-btn" data-custom="rag">RAG Query</button>
          <button class="lab-btn" data-custom="chat">Chat</button>
        </div>
      </div>
      <div id="lab-result" class="lab-result hidden">
        <h3>Sonuç</h3>
        <pre id="lab-result-pre"></pre>
      </div>
    </section>
  `;
}

function renderLabAction(action) {
  return `
    <div class="lab-action">
      <div class="lab-action-header">
        <strong>${escapeHtml(action.label)}</strong>
        <button class="lab-btn primary" data-action-id="${escapeHtml(action.id)}">Çalıştır</button>
      </div>
      <p class="meta">${escapeHtml(action.description || action.type || "")}</p>
      ${action.endpoint ? `<code class="endpoint-badge">${escapeHtml(action.method || "GET")} ${escapeHtml(action.endpoint)}</code>` : ""}
      ${action.command ? `<pre class="code-inline">${escapeHtml(action.command)}</pre>` : ""}
    </div>
  `;
}

function renderQA(qaList, title) {
  if (!qaList.length) return `<section class="panel"><p>Mülakat sorusu yok.</p></section>`;
  return `
    <section class="panel qa-list">
      <p class="meta">${qaList.length} soru — ${escapeHtml(title)}</p>
      ${qaList
        .map(
          (qa, i) => `
        <details class="qa-card">
          <summary>
            <span class="qa-chevron" aria-hidden="true">▶</span>
            <span class="qa-num">S${i + 1}</span>
            <span class="qa-question">${escapeHtml(qa.question)}</span>
            <span class="qa-hint">Cevabı gör — tıkla</span>
          </summary>
          <div class="qa-body">
            <div class="qa-section"><h4>Cevap</h4><p>${escapeHtml(qa.answer)}</p></div>
            ${qa.deep_dive ? `<div class="qa-section"><h4>Derinleştirme</h4><p>${escapeHtml(qa.deep_dive)}</p></div>` : ""}
            ${qa.red_flags?.length ? `<div class="qa-section red"><h4>Kırmızı Bayraklar</h4><ul>${qa.red_flags.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul></div>` : ""}
            ${qa.strong_signals?.length ? `<div class="qa-section green"><h4>Güçlü Sinyaller</h4><ul>${qa.strong_signals.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul></div>` : ""}
            ${qa.tags?.length ? `<div class="qa-tags">${qa.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>` : ""}
          </div>
        </details>`
        )
        .join("")}
    </section>
  `;
}

function renderStage15() {
  const s = hubData.stage15;
  els.pageTitle.textContent = s.title;
  els.pageSubtitle.textContent = s.subtitle;

  els.main.innerHTML = `
    <div class="tabs" role="tablist">
      <button class="tab active" data-tab="0">STAR Hikayeleri</button>
      <button class="tab" data-tab="1">Mülakat Q&A</button>
      <button class="tab" data-tab="2">İlkeler</button>
    </div>
    <div id="tab-content"></div>
  `;

  const tabContent = document.getElementById("tab-content");
  const renderTab = (idx) => {
    document.querySelectorAll(".tab").forEach((t, i) => t.classList.toggle("active", i === idx));
    if (idx === 0) {
      tabContent.innerHTML = `
        <section class="panel story-list">
          ${(s.stories || [])
            .map(
              (story) => `
            <article class="story-card">
              <h3>${escapeHtml(story.title)}</h3>
              <div class="star-grid">
                <div><h4>Situation</h4><p>${escapeHtml(story.situation)}</p></div>
                <div><h4>Task</h4><p>${escapeHtml(story.task)}</p></div>
                <div><h4>Action</h4><p>${escapeHtml(story.action)}</p></div>
                <div><h4>Result</h4><p>${escapeHtml(story.result)}</p></div>
                <div class="full"><h4>Technical Depth</h4><p>${escapeHtml(story.technical_depth)}</p></div>
                <div class="full"><h4>Reflection</h4><p>${escapeHtml(story.reflection)}</p></div>
              </div>
            </article>`
            )
            .join("")}
        </section>`;
    } else if (idx === 1) {
      tabContent.innerHTML = renderQA(s.interview_qa || [], s.title);
    } else {
      tabContent.innerHTML = `
        <section class="panel">
          <ul class="principle-list">${(s.principles || []).map((p) => `<li>${escapeHtml(p)}</li>`).join("")}</ul>
        </section>`;
    }
    bindAccordion();
  };

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => renderTab(Number(btn.dataset.tab)));
  });
  renderTab(0);
}

function renderStage16() {
  const s = hubData.stage16;
  els.pageTitle.textContent = s.title;
  els.pageSubtitle.textContent = `${s.total_questions} soru — ${s.subtitle}`;

  els.main.innerHTML = `
    <div class="tabs" role="tablist">
      <button class="tab active" data-tab="0">Prova Akışı</button>
      <button class="tab" data-tab="1">Tüm Sorular (${s.total_questions})</button>
      <button class="tab" data-tab="2">Canlı Kod</button>
      <button class="tab" data-tab="3">System Design</button>
    </div>
    <div id="tab-content"></div>
  `;

  const tabContent = document.getElementById("tab-content");
  const renderTab = (idx) => {
    document.querySelectorAll(".tab").forEach((t, i) => t.classList.toggle("active", i === idx));
    if (idx === 0) {
      tabContent.innerHTML = `
        <section class="panel">
          <h3>Açılış Pitch (10 dk)</h3>
          <blockquote class="principle">${escapeHtml(s.opening_pitch)}</blockquote>
          <h3>Simülasyon Takvimi</h3>
          <table class="schedule-table">
            <thead><tr><th>#</th><th>Alan</th><th>Süre</th><th>Zorluk</th><th>Odak</th></tr></thead>
            <tbody>
              ${(s.simulation_schedule || [])
                .map(
                  (r) => `
                <tr>
                  <td>${r.order}</td>
                  <td>${escapeHtml(r.area)}</td>
                  <td>${r.duration_min} dk</td>
                  <td><span class="difficulty">${escapeHtml(r.difficulty)}</span></td>
                  <td>${escapeHtml(r.focus)}</td>
                </tr>`
                )
                .join("")}
            </tbody>
          </table>
          <h3>Başarı Kriterleri</h3>
          <ul>${(s.success_criteria || []).map((c) => `<li>${escapeHtml(c)}</li>`).join("")}</ul>
          <h3>Mülakatta Sorabileceklerin</h3>
          <ul>${(s.questions_to_ask_interviewer || []).map((q) => `<li>${escapeHtml(q)}</li>`).join("")}</ul>
        </section>`;
    } else if (idx === 1) {
      const grouped = {};
      for (const qa of s.all_interview_qa || []) {
        const key = qa.stage_id;
        if (!grouped[key]) grouped[key] = { title: qa.stage_title, items: [] };
        grouped[key].items.push(qa);
      }
      tabContent.innerHTML = `
        <section class="panel">
          <div class="qa-filter">
            <input type="search" id="qa-search" placeholder="Soru ara..." />
          </div>
          <div id="all-qa-list">
            ${Object.entries(grouped)
              .sort(([a], [b]) => Number(a) - Number(b))
              .map(
                ([id, g]) => `
              <div class="qa-group" data-stage="${id}">
                <h3>Aşama ${id}: ${escapeHtml(g.title.replace(/^Aşama \d+ — /, ""))}</h3>
                ${renderQA(g.items, g.title)}
              </div>`
              )
              .join("")}
          </div>
        </section>`;
      const search = document.getElementById("qa-search");
      if (search) {
        search.addEventListener("input", () => {
          const q = search.value.toLowerCase();
          document.querySelectorAll(".qa-card").forEach((card) => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(q) ? "" : "none";
          });
        });
      }
      bindAccordion();
    } else if (idx === 2) {
      tabContent.innerHTML = `
        <section class="panel">
          ${(s.live_coding_prompts || [])
            .map(
              (lc) => `
            <article class="lc-card">
              <h4>${escapeHtml(lc.prompt)}</h4>
              <p><strong>Beklenen:</strong> ${escapeHtml(lc.expected_approach)}</p>
              <p><strong>Proje referansı:</strong> <code>${escapeHtml(lc.project_reference)}</code></p>
            </article>`
            )
            .join("")}
        </section>`;
    } else {
      const sd = s.system_design_prompt || {};
      tabContent.innerHTML = `
        <section class="panel">
          <h3>${escapeHtml(sd.question || "")}</h3>
          <ol>${(sd.answer_skeleton || []).map((a) => `<li>${escapeHtml(a)}</li>`).join("")}</ol>
          <p>Doküman: <code>${escapeHtml(sd.doc_reference || "")}</code></p>
        </section>`;
    }
    bindAccordion();
  };

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => renderTab(Number(btn.dataset.tab)));
  });
  renderTab(0);
}

function renderDemo() {
  els.pageTitle.textContent = "Agent Demo UI";
  els.pageSubtitle.textContent = "Workflow + Chat Stream + Onay + Trace + Feedback";
  els.main.innerHTML = `<div id="demo-mount"></div>`;
  mountDemo(document.getElementById("demo-mount"));
}

function getCurrentStage() {
  const match = currentView.match(/^stage-(\d+)$/);
  if (!match || !hubData) return null;
  return hubData.stages.find((s) => s.id === Number(match[1]));
}

function bindLabButtons() {
  const stage = getCurrentStage();
  if (!stage) return;

  document.querySelectorAll("[data-action-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const action = stage.lab_actions.find((a) => a.id === btn.dataset.actionId);
      if (action) await executeLab(action, btn);
    });
  });

  document.querySelectorAll("[data-custom]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const prompt = document.getElementById("custom-prompt")?.value?.trim();
      if (!prompt) return;
      const type = btn.dataset.custom;
      let action;
      if (type === "classify") {
        action = {
          type: "api_post",
          endpoint: "/v1/classify",
          method: "POST",
          body: { user_id: "hub-user", conversation_id: crypto.randomUUID(), message: prompt },
        };
      } else if (type === "workflow") {
        action = {
          type: "api_post",
          endpoint: "/v1/workflow/run",
          method: "POST",
          body: { user_id: "hub-user", conversation_id: crypto.randomUUID(), message: prompt },
        };
      } else if (type === "rag") {
        action = {
          type: "api_post",
          endpoint: "/v1/rag/query",
          method: "POST",
          body: { user_id: "hub-user", question: prompt, top_k: 3 },
        };
      } else {
        action = {
          type: "api_post",
          endpoint: "/v1/chat",
          method: "POST",
          body: { user_id: "hub-user", conversation_id: crypto.randomUUID(), message: prompt, stream: false },
        };
      }
      await executeLab(action, btn);
    });
  });
}

async function executeLab(action, btn) {
  const resultEl = document.getElementById("lab-result");
  const pre = document.getElementById("lab-result-pre");
  if (!resultEl || !pre) return;

  btn.disabled = true;
  resultEl.classList.remove("hidden");
  pre.textContent = "Çalışıyor...";

  try {
    const result = await runLabAction(action);
    pre.textContent = formatJson(result);
  } catch (err) {
    pre.textContent = `Hata: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

function bindAccordion() {
  /* details/summary native */
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

document.getElementById("sidebar-nav").addEventListener("click", (e) => {
  const btn = e.target.closest(".nav-item");
  if (btn?.dataset.view) navigate(btn.dataset.view);
});

els.sidebarToggle.addEventListener("click", () => {
  els.sidebar.classList.toggle("collapsed");
});

loadHub().catch((err) => {
  els.main.innerHTML = `<section class="panel error">Hub yüklenemedi: ${escapeHtml(err.message)}</section>`;
});
