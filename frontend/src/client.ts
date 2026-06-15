import type {
  ApiError,
  ChatRequest,
  ChatResponse,
  FeedbackRequest,
  FeedbackResponse,
  StreamChunk,
  TraceSummary,
  WorkflowRequest,
  WorkflowResponse,
} from "./types";

export class AgenticApiClient {
  constructor(private readonly baseUrl: string = "") {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });

    if (!response.ok) {
      let payload: ApiError | null = null;
      try {
        payload = (await response.json()) as ApiError;
      } catch {
        payload = null;
      }
      const message = payload?.error?.message ?? `Request failed (${response.status})`;
      throw new Error(message);
    }

    return (await response.json()) as T;
  }

  runWorkflow(body: WorkflowRequest): Promise<WorkflowResponse> {
    return this.request<WorkflowResponse>("/v1/workflow/run", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  chat(body: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>("/v1/chat", {
      method: "POST",
      body: JSON.stringify({ ...body, stream: false }),
    });
  }

  async *streamChat(body: ChatRequest): AsyncGenerator<StreamChunk> {
    const response = await fetch(`${this.baseUrl}/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...body, stream: true }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream failed (${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part
          .split("\n")
          .find((entry) => entry.startsWith("data: "));
        if (!line) {
          continue;
        }
        yield JSON.parse(line.slice(6)) as StreamChunk;
      }
    }
  }

  getTrace(traceId: string): Promise<TraceSummary> {
    return this.request<TraceSummary>(`/v1/observability/traces/${traceId}`);
  }

  submitFeedback(body: FeedbackRequest): Promise<FeedbackResponse> {
    return this.request<FeedbackResponse>("/v1/feedback", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }
}

export function mapStepLabel(step: string): string {
  const labels: Record<string, string> = {
    classify_intent: "Niyet analizi",
    retrieve_context: "Bilgi aranıyor",
    decide_action: "Aksiyon seçiliyor",
    request_human_approval: "Onay kontrolü",
    execute_tool: "İşlem yürütülüyor",
    final_answer: "Yanıt oluşturuluyor",
    audit_log: "Audit kaydı",
  };
  return labels[step] ?? step;
}
