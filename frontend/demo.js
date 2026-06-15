const STEP_LABELS = {
  classify_intent: "Niyet analizi",
  retrieve_context: "Bilgi aranıyor",
  decide_action: "Aksiyon seçiliyor",
  request_human_approval: "Onay kontrolü",
  execute_tool: "İşlem yürütülüyor",
  final_answer: "Yanıt oluşturuluyor",
  audit_log: "Audit kaydı",
};

let els = {};
let state = {};
let cleanupFns = [];
let mountContainer = null;

const DEMO_HTML = `
  <div class="demo-layout">
    <div class="demo-header">
      <div class="mode-switch">
        <label><input type="radio" name="demo-mode" value="workflow" checked /> Workflow</label>
        <label><input type="radio" name="demo-mode" value="chat" /> Chat Stream</label>
      </div>
    </div>
    <div class="main-grid">
      <section class="panel chat-panel">
        <div id="demo-messages" class="messages" aria-live="polite"></div>
        <div id="demo-status-banner" class="status-banner hidden"></div>
        <form id="demo-composer" class="composer">
          <textarea id="demo-message-input" rows="3" placeholder="Örn: Şifre sıfırlama policy nedir? veya Hesabımdan 80000 TL transfer et" required></textarea>
          <div class="composer-actions">
            <button type="submit" id="demo-send-btn">Gönder</button>
            <button type="button" id="demo-retry-btn" class="secondary hidden">Tekrar dene</button>
          </div>
        </form>
        <div id="demo-feedback-bar" class="feedback-bar hidden">
          <span>Bu yanıt faydalı mıydı?</span>
          <button type="button" data-rating="positive">👍</button>
          <button type="button" data-rating="negative">👎</button>
        </div>
      </section>
      <aside class="panel side-panel">
        <section><h2>Agent Durumu</h2><ul id="demo-step-list" class="step-list"></ul></section>
        <section id="demo-approval-card" class="approval-card hidden">
          <h2>İnsan Onayı Gerekli</h2>
          <p id="demo-approval-summary"></p>
          <p class="meta">Approval ID: <code id="demo-approval-id"></code></p>
          <div class="approval-actions">
            <button id="demo-approve-btn" type="button">Onayla ve devam et</button>
            <button id="demo-reject-btn" type="button" class="secondary">İptal</button>
          </div>
        </section>
        <section><h2>Trace / Debug</h2><pre id="demo-trace-panel" class="trace-panel">Henüz trace yok.</pre></section>
      </aside>
    </div>
  </div>
`;

export function mountDemo(container) {
  if (!container) return;
  unmountDemo();
  mountContainer = container;
  container.innerHTML = DEMO_HTML;

  state = {
    mode: "workflow",
    userId: "demo-user",
    conversationId: crypto.randomUUID(),
    runId: null,
    approvalId: null,
    traceId: null,
    lastMessage: "",
    pendingApproval: null,
  };

  els = {
    messages: container.querySelector("#demo-messages"),
    composer: container.querySelector("#demo-composer"),
    input: container.querySelector("#demo-message-input"),
    sendBtn: container.querySelector("#demo-send-btn"),
    retryBtn: container.querySelector("#demo-retry-btn"),
    statusBanner: container.querySelector("#demo-status-banner"),
    stepList: container.querySelector("#demo-step-list"),
    approvalCard: container.querySelector("#demo-approval-card"),
    approvalSummary: container.querySelector("#demo-approval-summary"),
    approvalId: container.querySelector("#demo-approval-id"),
    approveBtn: container.querySelector("#demo-approve-btn"),
    rejectBtn: container.querySelector("#demo-reject-btn"),
    tracePanel: container.querySelector("#demo-trace-panel"),
    feedbackBar: container.querySelector("#demo-feedback-bar"),
    approvalModal: document.getElementById("approval-modal"),
    modalSummary: document.getElementById("modal-summary"),
    modalTool: document.getElementById("modal-tool"),
    modalApprovalId: document.getElementById("modal-approval-id"),
    modalApproveBtn: document.getElementById("modal-approve-btn"),
    modalCancelBtn: document.getElementById("modal-cancel-btn"),
  };

  bindDemoEvents();
  addBubble("system", "Hoş geldiniz. Workflow modunda policy/transfer senaryolarını deneyebilirsiniz.");
}

export function unmountDemo() {
  cleanupFns.forEach((fn) => fn());
  cleanupFns = [];
  hideApprovalUI();
  if (mountContainer) mountContainer.innerHTML = "";
  mountContainer = null;
}

function on(el, event, handler) {
  if (!el) return;
  el.addEventListener(event, handler);
  cleanupFns.push(() => el.removeEventListener(event, handler));
}

function bindDemoEvents() {
  mountContainer.querySelectorAll('input[name="demo-mode"]').forEach((input) => {
    on(input, "change", (event) => {
      state.mode = event.target.value;
      hideApprovalUI();
    });
  });

  on(els.composer, "submit", async (event) => {
    event.preventDefault();
    const message = els.input.value.trim();
    if (!message) return;
    state.lastMessage = message;
    addBubble("user", message);
    els.input.value = "";
    els.feedbackBar.classList.add("hidden");
    if (state.mode === "chat") await streamChat(message);
    else await runWorkflow(message);
  });

  on(els.retryBtn, "click", async () => {
    if (!state.lastMessage) return;
    if (state.mode === "chat") await streamChat(state.lastMessage);
    else await runWorkflow(state.lastMessage);
  });

  on(els.approveBtn, "click", approvePending);
  on(els.modalApproveBtn, "click", approvePending);
  on(els.rejectBtn, "click", rejectPending);
  on(els.modalCancelBtn, "click", rejectPending);

  els.feedbackBar.querySelectorAll("button[data-rating]").forEach((button) => {
    on(button, "click", async () => {
      try {
        await submitFeedback(button.dataset.rating);
      } catch (error) {
        setStatus(error.message, true);
      }
    });
  });
}

function addBubble(role, text) {
  const node = document.createElement("div");
  node.className = `bubble ${role}`;
  node.textContent = text;
  els.messages.appendChild(node);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function setStatus(text, isError = false) {
  if (!text) {
    els.statusBanner.classList.add("hidden");
    return;
  }
  els.statusBanner.textContent = text;
  els.statusBanner.classList.toggle("error", isError);
  els.statusBanner.classList.remove("hidden");
}

function renderSteps(steps = []) {
  els.stepList.innerHTML = "";
  for (const step of steps) {
    const li = document.createElement("li");
    li.className = "done";
    li.textContent = STEP_LABELS[step] ?? step;
    els.stepList.appendChild(li);
  }
}

function renderTrace(summary) {
  els.tracePanel.textContent = summary ? JSON.stringify(summary, null, 2) : "Henüz trace yok.";
}

function showApprovalUI(result) {
  const tool = result.selected_tool ?? "high-risk action";
  const summary = `Seçilen işlem: ${tool}. Devam etmek için onay gerekli.`;
  state.pendingApproval = result;
  els.approvalSummary.textContent = summary;
  els.approvalId.textContent = result.approval_id ?? "-";
  els.approvalCard.classList.remove("hidden");
  els.modalSummary.textContent = summary;
  els.modalTool.textContent = tool;
  els.modalApprovalId.textContent = result.approval_id ?? "-";
  els.approvalModal.classList.remove("hidden");
}

function hideApprovalUI() {
  state.pendingApproval = null;
  if (els.approvalCard) els.approvalCard.classList.add("hidden");
  if (els.approvalModal) els.approvalModal.classList.add("hidden");
}

async function api(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let message = `İstek başarısız (${response.status})`;
    try {
      const payload = await response.json();
      message = payload?.error?.message ?? message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return response.json();
}

async function runWorkflow(message, { approvalGranted = false } = {}) {
  setStatus("Agent çalışıyor...");
  els.sendBtn.disabled = true;
  try {
    const result = await api("/v1/workflow/run", {
      user_id: state.userId,
      conversation_id: state.conversationId,
      message,
      approval_granted: approvalGranted,
      approval_id: state.approvalId,
      run_id: approvalGranted ? state.runId : null,
    });
    state.runId = result.run_id;
    state.approvalId = result.approval_id;
    state.traceId = result.trace_id;
    els.retryBtn.classList.add("hidden");
    renderSteps(result.steps_completed);
    renderTrace(result.trace_summary);
    if (result.needs_human_approval && result.status === "awaiting_approval") {
      addBubble("system", "Onay bekleniyor...");
      showApprovalUI(result);
      setStatus("Yüksek riskli işlem için insan onayı gerekiyor.");
      return;
    }
    hideApprovalUI();
    addBubble("assistant", result.final_answer);
    setStatus(`Durum: ${result.status}`);
    els.feedbackBar.classList.remove("hidden");
  } catch (error) {
    setStatus(error.message, true);
    els.retryBtn.classList.remove("hidden");
    addBubble("system", `Hata: ${error.message}`);
  } finally {
    els.sendBtn.disabled = false;
  }
}

async function streamChat(message) {
  setStatus("Streaming yanıt alınıyor...");
  els.sendBtn.disabled = true;
  const assistantBubble = document.createElement("div");
  assistantBubble.className = "bubble assistant";
  els.messages.appendChild(assistantBubble);
  try {
    const response = await fetch("/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.userId,
        conversation_id: state.conversationId,
        message,
        stream: true,
      }),
    });
    if (!response.ok || !response.body) throw new Error(`Stream başarısız (${response.status})`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.split("\n").find((entry) => entry.startsWith("data: "));
        if (!line) continue;
        const chunk = JSON.parse(line.slice(6));
        if (chunk.token) {
          assistantBubble.textContent += chunk.token;
          els.messages.scrollTop = els.messages.scrollHeight;
        }
      }
    }
    els.retryBtn.classList.add("hidden");
    setStatus("Streaming tamamlandı.");
    els.feedbackBar.classList.remove("hidden");
  } catch (error) {
    assistantBubble.textContent = `Hata: ${error.message}`;
    setStatus(error.message, true);
    els.retryBtn.classList.remove("hidden");
  } finally {
    els.sendBtn.disabled = false;
  }
}

async function submitFeedback(rating) {
  await api("/v1/feedback", {
    user_id: state.userId,
    conversation_id: state.conversationId,
    rating,
    trace_id: state.traceId,
    run_id: state.runId,
    message_preview: state.lastMessage,
  });
  setStatus(`Geri bildirim kaydedildi (${rating}).`);
}

async function approvePending() {
  if (!state.pendingApproval || !state.lastMessage) return;
  hideApprovalUI();
  await runWorkflow(state.lastMessage, { approvalGranted: true });
}

function rejectPending() {
  hideApprovalUI();
  setStatus("İşlem kullanıcı tarafından iptal edildi.");
  addBubble("system", "Onay verilmedi. İşlem iptal edildi.");
}
