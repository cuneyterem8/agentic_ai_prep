export type WorkflowStatus =
  | "running"
  | "awaiting_approval"
  | "completed"
  | "blocked"
  | "failed";

export interface WorkflowRequest {
  user_id: string;
  conversation_id: string;
  message: string;
  tenant_id?: string;
  user_role?: "customer" | "support_agent" | "admin";
  approval_granted?: boolean;
  approval_id?: string | null;
  run_id?: string | null;
}

export interface TraceTimelineItem {
  name: string;
  kind: string;
  latency_ms: number;
  status: string;
  model?: string;
}

export interface TraceSummary {
  trace_id: string;
  status: string;
  total_latency_ms: number;
  timeline: TraceTimelineItem[];
  llm_calls: number;
  total_tokens: number;
  estimated_cost_usd: number;
  prompt_version: string;
}

export interface WorkflowResponse {
  run_id: string;
  conversation_id: string;
  status: WorkflowStatus;
  final_answer: string;
  needs_human_approval: boolean;
  approval_id?: string | null;
  selected_tool?: string | null;
  steps_completed: string[];
  trace_id?: string | null;
  trace_summary?: TraceSummary | null;
}

export interface ChatRequest {
  user_id: string;
  conversation_id: string;
  message: string;
  stream?: boolean;
}

export interface ChatResponse {
  conversation_id: string;
  message: string;
  model: string;
}

export interface StreamChunk {
  token: string;
  done?: boolean;
  conversation_id?: string;
}

export interface FeedbackRequest {
  user_id: string;
  conversation_id: string;
  rating: "positive" | "negative";
  comment?: string;
  trace_id?: string | null;
  run_id?: string | null;
  message_preview?: string;
}

export interface FeedbackResponse {
  feedback_id: string;
  timestamp: string;
  rating: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    correlation_id?: string;
  };
}
