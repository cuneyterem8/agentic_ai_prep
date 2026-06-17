"""Learning hub Aşama 0-13 — symbols_detail kayıtları."""

from textwrap import dedent

SYMBOLS_DETAIL_BY_PATH: dict[str, list[dict]] = {
    # --- Stage 0: Common foundation ---
    "src/common/config.py": [
        {
            "name": "Settings",
            "code": dedent("""\
                class Settings(BaseSettings):
                    model_config = SettingsConfigDict(
                        env_file=".env", env_file_encoding="utf-8", extra="ignore"
                    )
                    openai_api_key: SecretStr | None = None
                    llm_provider: Literal["mock", "openai"] = "mock"
                    database_url: str = "sqlite:///./data/app.db"
                    app_env: Literal["development", "staging", "production"] = "development"
            """).strip(),
            "usage": (
                "Pydantic Settings ile tüm ortam değişkenlerini tek noktada toplar. "
                "LLM sağlayıcısı, API anahtarı, veritabanı URL'si ve log seviyesi buradan okunur. "
                "FastAPI uygulaması başlarken `get_settings()` ile bu sınıf kullanılır."
            ),
        },
        {
            "name": "get_settings()",
            "code": dedent("""\
                @lru_cache
                def get_settings() -> Settings:
                    return Settings()
            """).strip(),
            "usage": (
                "`lru_cache` ile ayarlar uygulama ömrü boyunca bir kez yüklenir. "
                "Factory, bootstrap ve healthcheck gibi modüller bu fonksiyonu çağırarak "
                "aynı Settings örneğini paylaşır; testlerde cache temizlenebilir."
            ),
        },
    ],
    "src/common/logging.py": [
        {
            "name": "StructuredFormatter",
            "code": dedent("""\
                class StructuredFormatter(logging.Formatter):
                    def format(self, record: logging.LogRecord) -> str:
                        payload = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "level": record.levelname,
                            "logger": record.name,
                            "message": record.getMessage(),
                        }
                        if correlation_id := get_correlation_id():
                            payload["correlation_id"] = correlation_id
                        return json.dumps(payload, ensure_ascii=False)
            """).strip(),
            "usage": (
                "Log satırlarını JSON formatında üretir; CloudWatch veya ELK gibi sistemlerde "
                "kolayca parse edilir. `correlation_id`, `trace_id`, `latency_ms` gibi extra "
                "alanlar varsa payload'a eklenir."
            ),
        },
        {
            "name": "set_correlation_id()",
            "code": dedent("""\
                correlation_id_var: ContextVar[str | None] = ContextVar(
                    "correlation_id", default=None
                )

                def set_correlation_id(correlation_id: str | None) -> None:
                    correlation_id_var.set(correlation_id)
            """).strip(),
            "usage": (
                "ContextVar ile istek bazlı correlation ID taşır. FastAPI middleware "
                "`X-Correlation-ID` header'ını okuyup set eder; LLM çağrıları ve audit "
                "logları aynı ID ile ilişkilendirilir."
            ),
        },
    ],
    "src/common/health.py": [
        {
            "name": "healthcheck()",
            "code": dedent("""\
                def healthcheck(settings: Settings | None = None) -> dict[str, str | bool]:
                    cfg = settings or get_settings()
                    has_api_key = cfg.openai_api_key is not None and bool(
                        cfg.openai_api_key.get_secret_value().strip()
                    )
                    return {
                        "status": "ok",
                        "app_name": cfg.app_name,
                        "llm_provider": cfg.llm_provider,
                        "openai_configured": has_api_key,
                        "database_url": cfg.database_url.split("://", 1)[0],
                    }
            """).strip(),
            "usage": (
                "`/health` endpoint'inin çekirdeğidir; uygulama ayakta mı ve OpenAI "
                "yapılandırılmış mı bilgisini döner. Dockerfile HEALTHCHECK ve CI smoke "
                "testi bu fonksiyonun HTTP karşılığını kullanır."
            ),
        },
    ],
    "src/common/errors.py": [
        {
            "name": "AppError",
            "code": dedent("""\
                class AppError(Exception):
                    \"\"\"Base application error.\"\"\"

                class TransientError(AppError):
                    \"\"\"Retryable error — network blip, timeout, rate limit.\"\"\"

                class LLMTimeoutError(TransientError):
                    \"\"\"LLM call exceeded timeout.\"\"\"
            """).strip(),
            "usage": (
                "Uygulama genelinde hata hiyerarşisinin köküdür. `TransientError` "
                "alt sınıfları retry katmanında yeniden denenebilir; `ValidationError` "
                "ve `AuthorizationError` ise retry edilmez."
            ),
        },
        {
            "name": "ValidationError",
            "code": dedent("""\
                class ValidationError(AppError):
                    \"\"\"Input or output validation failed — do not retry.\"\"\"

                class AuthorizationError(AppError):
                    \"\"\"Auth failure — do not retry.\"\"\"
            """).strip(),
            "usage": (
                "Structured output parse hataları ve policy reddi bu sınıflarla yükseltilir. "
                "Exception handler'lar `AuthorizationError` için 403, diğer `AppError` "
                "türleri için 500 döner."
            ),
        },
    ],
    # --- Stage 1: LLM layer ---
    "src/llm/base.py": [
        {
            "name": "Message",
            "code": dedent("""\
                class MessageRole(str, Enum):
                    SYSTEM = "system"
                    USER = "user"
                    ASSISTANT = "assistant"

                class Message(BaseModel):
                    role: MessageRole
                    content: str
            """).strip(),
            "usage": (
                "Tüm LLM sağlayıcıları bu mesaj modelini kullanır. Chat, classifier, "
                "RAG ve SQL analyst prompt'ları `list[Message]` olarak oluşturulur; "
                "provider-agnostic soyutlama sağlar."
            ),
        },
        {
            "name": "LLMClient",
            "code": dedent("""\
                class LLMClient(Protocol):
                    async def complete(self, messages: list[Message]) -> LLMResponse: ...
                    async def stream(self, messages: list[Message]) -> AsyncIterator[str]: ...
            """).strip(),
            "usage": (
                "Mock, OpenAI ve Fallback client'ların ortak arayüzüdür. Factory bu "
                "Protocol'e uygun nesne döner; `generate_chat_response` hangi sağlayıcı "
                "olduğunu bilmeden çalışır."
            ),
        },
    ],
    "src/llm/mock_client.py": [
        {
            "name": "MockLLMClient",
            "code": dedent("""\
                class MockLLMClient:
                    async def complete(self, messages: list[Message]) -> LLMResponse:
                        if _is_classification_prompt(messages):
                            content = _mock_classification(messages)
                        elif _is_sql_analyst_prompt(messages):
                            content = _mock_sql_generation(messages)
                        else:
                            content = self._default_content(messages)
                        return LLMResponse(content=content, model=self.model, ...)
            """).strip(),
            "usage": (
                "API anahtarı olmadan offline geliştirme ve test için deterministik yanıtlar "
                "üretir. System prompt içeriğine göre classification JSON, SQL veya genel "
                "chat cevabı döner; CI eval'leri bu client ile çalışır."
            ),
        },
        {
            "name": "_mock_classification()",
            "code": dedent("""\
                def _mock_classification(messages: list[Message]) -> str:
                    text = _extract_customer_message(last_user).lower()
                    if any(w in text for w in ("şikayet", "complaint")):
                        payload = {"intent": "complaint", "risk_level": "medium", ...}
                    elif any(w in text for w in ("transfer", "para gönder")):
                        payload = {"intent": "account_action", "risk_level": "high", ...}
                    return json.dumps(payload)
            """).strip(),
            "usage": (
                "Classifier chain'in beklediği JSON şemasını keyword eşleştirmesiyle "
                "simüle eder. Golden dataset eval'lerinde tutarlı intent/risk sonuçları "
                "alınmasını sağlar."
            ),
        },
    ],
    "src/common/retry.py": [
        {
            "name": "with_retry()",
            "code": dedent("""\
                async def with_retry(
                    operation: Callable[[], Awaitable[T]],
                    *, max_attempts: int = 3,
                    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
                ) -> T:
                    async for attempt in AsyncRetrying(
                        stop=stop_after_attempt(max_attempts),
                        wait=wait_exponential(min=0.1, max=1.0),
                        retry=retry_if_exception_type(retryable_exceptions),
                        reraise=True,
                    ):
                        with attempt:
                            return await operation()
            """).strip(),
            "usage": (
                "Tenacity ile geçici LLM hatalarında üstel backoff uygular. "
                "`generate_chat_response` bu wrapper'ı kullanır; validation ve "
                "authorization hataları retry edilmez."
            ),
        },
        {
            "name": "with_timeout()",
            "code": dedent("""\
                async def with_timeout(awaitable: Awaitable[T], timeout_seconds: float) -> T:
                    return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
            """).strip(),
            "usage": (
                "LLM çağrısına üst sınır koyar; süre aşımında `TimeoutError` fırlatılır "
                "ve service katmanı bunu `LLMTimeoutError`'a çevirir."
            ),
        },
    ],
    "src/llm/factory.py": [
        {
            "name": "create_llm_client()",
            "code": dedent("""\
                def create_llm_client(settings: Settings | None = None) -> LLMClient:
                    cfg = settings or get_settings()
                    if cfg.llm_provider == "openai" and _has_openai_api_key(cfg):
                        primary = OpenAIClient(api_key=..., model=cfg.openai_model)
                        fallback = OpenAIClient(api_key=..., model=cfg.openai_fallback_model)
                        return FallbackLLMClient(primary=primary, fallback=fallback)
                    return MockLLMClient(model=f"mock-{cfg.openai_model}")
            """).strip(),
            "usage": (
                "Dependency injection noktasıdır. OpenAI yapılandırılmışsa primary+fallback "
                "zinciri, aksi halde MockLLMClient döner. FastAPI `Depends(get_llm_client)` "
                "bu factory'yi kullanır."
            ),
        },
    ],
    "src/llm/service.py": [
        {
            "name": "generate_chat_response()",
            "code": dedent("""\
                async def generate_chat_response(
                    messages: list[Message], client: LLMClient, *,
                    timeout_seconds: float = 30.0, max_attempts: int = 3,
                ) -> LLMResponse:
                    response = await with_timeout(
                        with_retry(_call, max_attempts=max_attempts), timeout_seconds
                    )
                    get_metrics().record_llm_call(model=model, latency_ms=..., ...)
                    trace.record_llm_span(model=model, prompt_tokens=..., ...)
                    return response
            """).strip(),
            "usage": (
                "Provider-agnostic chat completion katmanıdır. Timeout, retry, metrics "
                "ve trace kaydı tek yerde toplanır. Classifier, RAG ve chat router'ları "
                "doğrudan bu fonksiyonu çağırır."
            ),
        },
    ],
    # --- Stage 2: API layer ---
    "src/api/main.py": [
        {
            "name": "app",
            "code": dedent("""\
                app = FastAPI(title=settings.app_name, version=settings.app_version)
                app.include_router(chat.router)
                app.include_router(workflow.router)
                app.include_router(learning_hub.router)
                # ...
                app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")
            """).strip(),
            "usage": (
                "FastAPI uygulamasının giriş noktasıdır. Tüm router'lar, exception handler'lar "
                "ve frontend static dosyaları burada birleştirilir. Uvicorn "
                "`src.api.main:app` ile bu nesneyi serve eder."
            ),
        },
        {
            "name": "correlation_id_middleware",
            "code": dedent("""\
                @app.middleware("http")
                async def correlation_id_middleware(request: Request, call_next):
                    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
                    set_correlation_id(correlation_id)
                    response = await call_next(request)
                    response.headers["X-Correlation-ID"] = correlation_id
                    return response
            """).strip(),
            "usage": (
                "Her HTTP isteğine benzersiz correlation ID atar. Structured loglar ve "
                "audit kayıtları bu ID ile zincirlenir; distributed trace debug'unda "
                "kritik bağlantı noktasıdır."
            ),
        },
    ],
    "src/api/routers/chat.py": [
        {
            "name": "chat()",
            "code": dedent("""\
                @router.post("/chat", response_model=ChatResponse)
                async def chat(body: ChatRequest, client: LLMClient = Depends(get_llm_client)):
                    messages = [Message(role=MessageRole.USER, content=body.message)]
                    if body.stream:
                        return StreamingResponse(_stream_tokens(client, messages, ...))
                    response = await generate_chat_response(messages, client)
                    return ChatResponse(conversation_id=..., message=response.content, ...)
            """).strip(),
            "usage": (
                "`POST /v1/chat` endpoint'idir. Stream modunda SSE token akışı, "
                "normal modda tam yanıt döner. Frontend `AgenticApiClient.chat()` "
                "ve `streamChat()` bu route'u kullanır."
            ),
        },
    ],
    "src/api/routers/agent.py": [
        {
            "name": "run_agent()",
            "code": dedent("""\
                @router.post("/agent/run", response_model=AgentRunResponse)
                async def run_agent(body: AgentRunRequest, client: LLMClient = Depends(...)):
                    prompt = f"Task: {body.task}\\nInput: {body.input}"
                    messages = [Message(role=MessageRole.USER, content=prompt)]
                    response = await generate_chat_response(messages, client)
                    return AgentRunResponse(status="completed", result=response.content, ...)
            """).strip(),
            "usage": (
                "Basit agent görev çalıştırma endpoint'idir. Task + input birleştirilerek "
                "LLM'e gönderilir; workflow'dan önceki minimal agent demo'sunu temsil eder."
            ),
        },
    ],
    "src/api/schemas.py": [
        {
            "name": "ChatRequest",
            "code": dedent("""\
                class ChatRequest(BaseModel):
                    user_id: str = Field(min_length=1, max_length=128)
                    conversation_id: str = Field(min_length=1, max_length=128)
                    message: str = Field(min_length=1, max_length=8000)
                    stream: bool = False
            """).strip(),
            "usage": (
                "Chat API istek şemasıdır. Pydantic validasyonu boş veya aşırı uzun "
                "mesajları 422 ile reddeder. OpenAPI docs'ta otomatik görünür."
            ),
        },
        {
            "name": "WorkflowRequest",
            "code": dedent("""\
                class WorkflowRequest(BaseModel):
                    user_id: str
                    conversation_id: str
                    message: str
                    tenant_id: str = "default"
                    user_role: UserRole = UserRole.CUSTOMER
                    approval_granted: bool = False
                    run_id: str | None = None
            """).strip(),
            "usage": (
                "Workflow endpoint'inin gövdesidir. Onay devamı için `approval_granted` "
                "ve checkpoint resume için `run_id` alanları taşınır; frontend workflow "
                "demo'su bu şemayı kullanır."
            ),
        },
    ],
    "src/api/exception_handlers.py": [
        {
            "name": "_error_response()",
            "code": dedent("""\
                def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
                    body = ErrorResponse(
                        error=ErrorDetail(
                            code=code, message=message,
                            correlation_id=get_correlation_id(),
                        )
                    )
                    return JSONResponse(status_code=status_code, content=body.model_dump())
            """).strip(),
            "usage": (
                "Tüm API hatalarını tutarlı JSON formatına çevirir. Frontend "
                "`AgenticApiClient` bu yapıdaki `error.message` alanını okuyarak "
                "kullanıcıya gösterir."
            ),
        },
        {
            "name": "llm_timeout_exception_handler",
            "code": dedent("""\
                async def llm_timeout_exception_handler(request, exc: LLMTimeoutError):
                    return _error_response(504, "llm_timeout", str(exc))
            """).strip(),
            "usage": (
                "LLM süre aşımını 504 Gateway Timeout olarak döner. Client tarafında "
                "retry veya kullanıcı bilgilendirmesi bu kod ile tetiklenebilir."
            ),
        },
    ],
    # --- Stage 3: Classification ---
    "src/llm/structured_output.py": [
        {
            "name": "IntentClassification",
            "code": dedent("""\
                class IntentClassification(BaseModel):
                    intent: IntentType
                    risk_level: RiskLevel
                    needs_human_approval: bool = Field(
                        description="True when action is risky and requires human approval."
                    )
            """).strip(),
            "usage": (
                "Classifier chain'in hedef Pydantic şemasıdır. LLM JSON çıktısı bu modele "
                "validate edilir; policy engine ve workflow bu alanları okur."
            ),
        },
        {
            "name": "parse_structured_output()",
            "code": dedent("""\
                def parse_structured_output(raw_text: str, model: type[T]) -> T:
                    candidate = extract_json_block(raw_text)
                    payload = json.loads(candidate)
                    return model.model_validate(payload)
            """).strip(),
            "usage": (
                "Ham LLM metninden JSON çıkarıp Pydantic modeline dönüştürür. "
                "Parse hatası `ValidationError` fırlatır; classifier repair loop'u "
                "bu hatayı yakalayarak yeniden dener."
            ),
        },
    ],
    "src/agents/classifier.py": [
        {
            "name": "classify_customer_message()",
            "code": dedent("""\
                async def classify_customer_message(
                    customer_message: str, client: LLMClient, *, max_repairs: int = 1,
                ) -> IntentClassification:
                    input_guardrail = validate_user_input(customer_message)
                    if input_guardrail.blocked:
                        return IntentClassification(intent=IntentType.UNKNOWN, ...)
                    response = await generate_chat_response(build_classification_messages(...), client)
                    try:
                        return parse_structured_output(response.content, IntentClassification)
                    except ValidationError:
                        # repair loop with build_repair_messages()
                        ...
            """).strip(),
            "usage": (
                "LangChain LCEL'e eşdeğer bağımsız classification chain'idir. "
                "Input guardrail → LLM → parse → repair akışını yönetir. "
                "`/v1/classify` ve workflow'un classify_intent node'u bunu çağırır."
            ),
        },
    ],
    "src/agents/callbacks.py": [
        {
            "name": "ChainCallbackHandler",
            "code": dedent("""\
                class ChainCallbackHandler:
                    def on_chain_start(self, chain: str, inputs: dict) -> None: ...
                    def on_llm_end(self, chain: str, *, latency_ms, model, tokens) -> None: ...
                    def on_parse_success(self, chain: str, output: dict) -> None: ...
                    def on_parse_error(self, chain: str, error: str, raw_output: str) -> None: ...
            """).strip(),
            "usage": (
                "LangSmith benzeri chain trace olaylarını bellekte toplar. "
                "Classifier repair döngüsünde parse başarı/hata olayları kaydedilir; "
                "debug ve eval analizi için kullanılır."
            ),
        },
    ],
    "src/agents/tools.py": [
        {
            "name": "KnowledgeSearchTool",
            "code": dedent("""\
                @dataclass
                class KnowledgeSearchTool:
                    name: str = "knowledge_search"
                    async def run(self, arguments: dict) -> ToolResult:
                        query = str(arguments.get("query", "")).strip()
                        return ToolResult(
                            tool_name=self.name, success=True,
                            output=f"Found policy snippets for: {query}",
                            metadata={"read_only": True},
                        )
            """).strip(),
            "usage": (
                "Düşük riskli read-only tool'dur. Policy engine müşteri rolüne bu "
                "tool'u otomatik izin verir; workflow knowledge_question intent'inde "
                "seçer."
            ),
        },
        {
            "name": "get_tool_registry()",
            "code": dedent("""\
                def get_tool_registry() -> dict[str, KnowledgeSearchTool | TransferMoneyTool]:
                    return {
                        "knowledge_search": KnowledgeSearchTool(),
                        "transfer_money": TransferMoneyTool(),
                    }
            """).strip(),
            "usage": (
                "Workflow ve tool execution service'in kullandığı tool sözlüğüdür. "
                "Yeni tool eklemek registry'ye kayıt + policy allowlist güncellemesi "
                "gerektirir."
            ),
        },
    ],
    "src/api/routers/classify.py": [
        {
            "name": "classify_message()",
            "code": dedent("""\
                @router.post("/classify", response_model=ClassifyResponse)
                async def classify_message(body: ClassifyRequest, client=Depends(get_llm_client)):
                    input_guardrail = validate_user_input(body.message)
                    if input_guardrail.blocked:
                        return ClassifyResponse(blocked=True, block_reasons=..., ...)
                    result = await classify_customer_message(body.message, client)
                    return ClassifyResponse(intent=result.intent.value, ...)
            """).strip(),
            "usage": (
                "Classification API endpoint'idir. Guardrail engeli ve classifier sonucunu "
                "tek response'ta birleştirir. Learning hub lab'ında intent demo'su "
                "bu route üzerinden çalışır."
            ),
        },
    ],
    # --- Stage 4: Workflow + ReAct ---
    "src/agents/react_loop.py": [
        {
            "name": "run_react_loop",
            "code": dedent("""\
                async def run_react_loop(*, user_query, user_id, max_steps=5) -> ReActResult:
                    state = {"query": user_query, "user_id": user_id, "steps": []}
                    for _ in range(max_steps):
                        decision = _decide_next_action(state)
                        if decision.action_type == "tool_call":
                            result = await registry[decision.tool_name].run(decision.tool_arguments)
                            decision.observation = result.output
                            state["steps"].append(decision)
                        elif decision.action_type == "final_answer":
                            return ReActResult(steps=state["steps"], final_answer=..., status="completed")
                        elif decision.action_type == "escalate":
                            return ReActResult(..., status="escalated")
            """).strip(),
            "usage": (
                "ReAct agent döngüsü: Observe→Think→Act. Mock deterministic karar verir; "
                "production'da LLM JSON decision + policy engine yetki kontrolü birlikte çalışır."
            ),
        },
    ],
    "src/agents/workflow.py": [
        {
            "name": "CustomerSupportWorkflow",
            "code": dedent("""\
                class CustomerSupportWorkflow:
                    async def run(
                        self, *, user_id, conversation_id, customer_message,
                        approval_granted=False, run_id=None, ...
                    ) -> WorkflowResult:
                        if run_id and run_id in _checkpoint_store:
                            state = from_checkpoint(_checkpoint_store[run_id])
                            return await self._resume_from_checkpoint(state, trace)
                        state = AgentState(user_id=..., customer_message=...)
                        return await self._execute_from_start(state, trace)
            """).strip(),
            "usage": (
                "LangGraph tarzı explicit node/edge workflow motorudur. "
                "classify → retrieve → decide → approve → execute → answer → audit "
                "adımlarını sırayla çalıştırır; checkpoint ile onay sonrası devam eder."
            ),
        },
    ],
    "src/agents/state.py": [
        {
            "name": "AgentState",
            "code": dedent("""\
                class AgentState(BaseModel):
                    run_id: str = Field(default_factory=lambda: str(uuid4()))
                    customer_message: str
                    classification: IntentClassification | None = None
                    selected_tool: str | None = None
                    needs_human_approval: bool = False
                    approval_granted: bool = False
                    status: WorkflowStatus = WorkflowStatus.RUNNING
                    steps_completed: list[str] = Field(default_factory=list)
            """).strip(),
            "usage": (
                "Workflow'un taşıdığı mutable durum modelidir. Her node bu state'i "
                "günceller; checkpoint serialize/deserialize için Pydantic model_dump "
                "kullanılır."
            ),
        },
        {
            "name": "WorkflowResult",
            "code": dedent("""\
                class WorkflowResult(BaseModel):
                    run_id: str
                    status: WorkflowStatus
                    final_answer: str
                    needs_human_approval: bool
                    steps_completed: list[str]
                    trace_id: str | None = None
                    trace_summary: TraceSummary | None = None
            """).strip(),
            "usage": (
                "Workflow tamamlandığında API'ye dönen sonuç modelidir. Frontend "
                "step timeline ve trace linkini bu yapıdan okur."
            ),
        },
    ],
    "src/agents/policies.py": [
        {
            "name": "evaluate_tool_permission()",
            "code": dedent("""\
                def evaluate_tool_permission(
                    *, user_id, tool_name, classification, user_role=UserRole.CUSTOMER,
                    approval_granted=False,
                ) -> PolicyResult:
                    if tool_name not in ALLOWED_TOOLS:
                        return PolicyResult(decision=PolicyDecision.DENY, ...)
                    if tool_name in HIGH_RISK_TOOLS and not approval_granted:
                        return PolicyResult(decision=PolicyDecision.REQUIRE_APPROVAL, ...)
                    return PolicyResult(decision=PolicyDecision.ALLOW, ...)
            """).strip(),
            "usage": (
                "Tool çalıştırma öncesi yetki kararını verir. Rol matrisi, intent "
                "ve onay durumuna göre ALLOW / REQUIRE_APPROVAL / DENY döner. "
                "Workflow decide_action ve execute_tool node'ları bu fonksiyonu kullanır."
            ),
        },
        {
            "name": "can_execute_tool()",
            "code": dedent("""\
                def can_execute_tool(
                    *, user_id, tool_name, classification, approval_granted, user_role=...,
                ) -> PolicyResult:
                    policy = evaluate_tool_permission(...)
                    if policy.decision == PolicyDecision.REQUIRE_APPROVAL and approval_granted:
                        return PolicyResult(decision=PolicyDecision.ALLOW, reason="Human approval granted")
                    return policy
            """).strip(),
            "usage": (
                "Onay verildikten sonra high-risk tool'un çalıştırılıp çalıştırılamayacağını "
                "doğrular. Case study transfer senaryosunda ikinci `workflow.run` çağrısı "
                "bu kontrolden geçer."
            ),
        },
    ],
    "src/agents/checkpoint.py": [
        {
            "name": "to_checkpoint()",
            "code": dedent("""\
                def to_checkpoint(state: AgentState) -> dict:
                    return state.model_dump()

                def from_checkpoint(payload: dict) -> AgentState:
                    return AgentState.model_validate(payload)
            """).strip(),
            "usage": (
                "AgentState'i dict'e çevirip geri yükler. Workflow in-memory "
                "`_checkpoint_store`'a yazar; onay bekleyen run'lar resume edilir."
            ),
        },
        {
            "name": "append_audit()",
            "code": dedent("""\
                def append_audit(state: AgentState, *, action, actor, risk_level=..., details=None):
                    state.audit_events.append(
                        AuditEvent(action=action, actor=actor, risk_level=risk_level, ...)
                    )
            """).strip(),
            "usage": (
                "Workflow state içindeki audit olay listesine kayıt ekler. "
                "Her node tamamlandığında veya policy reddi olduğunda çağrılır."
            ),
        },
    ],
    "src/api/routers/workflow.py": [
        {
            "name": "run_workflow()",
            "code": dedent("""\
                @router.post("/workflow/run", response_model=WorkflowResponse)
                async def run_workflow(body: WorkflowRequest, client=Depends(get_llm_client)):
                    stores = get_data_stores()
                    stores.message_repo.add_message(conversation_id=..., role="user", ...)
                    workflow = CustomerSupportWorkflow(client, tool_execution_service=...)
                    result = await workflow.run(user_id=..., approval_granted=body.approval_granted, ...)
                    return WorkflowResponse(status=result.status.value, trace_id=result.trace_id, ...)
            """).strip(),
            "usage": (
                "Ana workflow HTTP endpoint'idir. Mesajı DB'ye yazar, workflow'u "
                "başlatır ve trace özetiyle birlikte sonucu döner. Frontend demo "
                "ve case study entegrasyon testleri bu route'u kullanır."
            ),
        },
    ],
    # --- Stage 5: Production LLM ---
    "src/llm/openai_client.py": [
        {
            "name": "OpenAIClient",
            "code": dedent("""\
                class OpenAIClient:
                    async def complete(self, messages: list[Message]) -> LLMResponse:
                        response = await self._client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": m.role.value, "content": m.content} for m in messages],
                        )
                        return LLMResponse(content=choice.message.content or "", model=response.model, ...)
            """).strip(),
            "usage": (
                "Production OpenAI adapter'ıdır. API hatalarını `LLMProviderError` ve "
                "`LLMTimeoutError`'a map eder. Factory primary/fallback client olarak "
                "iki farklı model ile oluşturur."
            ),
        },
    ],
    "src/llm/fallback_client.py": [
        {
            "name": "FallbackLLMClient",
            "code": dedent("""\
                class FallbackLLMClient:
                    async def complete(self, messages: list[Message]) -> LLMResponse:
                        try:
                            return await self.primary.complete(messages)
                        except (LLMProviderError, LLMTimeoutError, TransientError) as exc:
                            logger.warning("llm_fallback_triggered", extra={...})
                            response = await self.fallback.complete(messages)
                            return LLMResponse(content=response.content, model=f"fallback:{response.model}", ...)
            """).strip(),
            "usage": (
                "Primary model başarısız olunca secondary modele geçer. gpt-4o → gpt-4o-mini "
                "fallback stratejisini uygular; model adına `fallback:` prefix eklenir."
            ),
        },
    ],
    "src/llm/tool_calling.py": [
        {
            "name": "parse_tool_calls_payload()",
            "code": dedent("""\
                def parse_tool_calls_payload(payload: dict) -> ParsedToolCalls:
                    message = choices[0].get("message") or {}
                    for raw in message.get("tool_calls") or []:
                        function = raw.get("function") or {}
                        arguments = json.loads(function.get("arguments", "{}"))
                        tool_calls.append(ToolCall(id=..., name=name, arguments=arguments))
                    return ParsedToolCalls(tool_calls=tool_calls, ...)
            """).strip(),
            "usage": (
                "OpenAI tool_calls JSON yapısını iç modellere parse eder. "
                "Gelecekte native function calling entegrasyonu için hazır katmandır."
            ),
        },
        {
            "name": "validate_tool_calls()",
            "code": dedent("""\
                def validate_tool_calls(parsed: ParsedToolCalls, *, allowed_tools: set[str]):
                    for call in parsed.tool_calls:
                        if call.name not in allowed_tools:
                            raise ValidationError(f"Tool '{call.name}' is not allowed")
                    return parsed
            """).strip(),
            "usage": (
                "LLM'in önerdiği tool'ların policy allowlist'te olup olmadığını kontrol eder. "
                "Bilinmeyen tool adı validation hatası fırlatır."
            ),
        },
    ],
    # --- Stage 6: RAG ---
    "src/rag/documents.py": [
        {
            "name": "default_banking_documents()",
            "code": dedent("""\
                def default_banking_documents() -> list[SourceDocument]:
                    return [
                        SourceDocument(id="doc-1", title="Password Reset Policy", content="..."),
                        SourceDocument(id="doc-3", title="Transfer Limits", content="..."),
                    ]
            """).strip(),
            "usage": (
                "Demo bilgi tabanı dokümanlarını döner. Şifre sıfırlama, şikayet SLA "
                "ve transfer limitleri gibi senaryolar bu içeriklerle test edilir."
            ),
        },
        {
            "name": "RetrievalResult",
            "code": dedent("""\
                class RetrievalResult(BaseModel):
                    chunk: Chunk
                    score: float
                    rank: int
            """).strip(),
            "usage": (
                "Retriever'ın döndürdüğü skorlu sonuç modelidir. RAG API response'unda "
                "kaynak chunk id ve relevance score bu yapıdan gelir."
            ),
        },
    ],
    "src/rag/retriever.py": [
        {
            "name": "VectorRetriever",
            "code": dedent("""\
                class VectorRetriever:
                    async def retrieve(self, query: str, *, top_k: int = 3) -> list:
                        hybrid_score = (0.7 * vector_score) + (0.3 * keyword_score)
                        scored.sort(key=lambda item: item[0], reverse=True)
                        return [RetrievalResult(chunk=chunk, score=..., rank=rank) ...]
            """).strip(),
            "usage": (
                "Vector + keyword hybrid arama yapar. Mock embedding ile cosine "
                "similarity hesaplanır; workflow retrieve_context node'u MockRetriever "
                "üzerinden bunu kullanır."
            ),
        },
        {
            "name": "KnowledgeBase.ingest()",
            "code": dedent("""\
                def ingest(self, documents: list[SourceDocument], *, chunk_size=120, overlap=30):
                    for document in documents:
                        parts = chunk_text(document.content, chunk_size=..., overlap=...)
                        self.chunks.append(Chunk(id=f"{document.id}-chunk-{index}", ...))
                        self.vectors.append(self.embedding_provider.embed(part))
            """).strip(),
            "usage": (
                "Dokümanları chunk'lara böler ve embedding index'ine ekler. "
                "Uygulama başlangıcında default banking docs otomatik ingest edilir."
            ),
        },
    ],
    "src/rag/service.py": [
        {
            "name": "answer_with_sources()",
            "code": dedent("""\
                async def answer_with_sources(question, client, *, retriever=None, top_k=3):
                    retrieved = await retriever.retrieve(question, top_k=top_k)
                    source_chunk_ids = [item.chunk.id for item in retrieved]
                    context = "\\n".join(f"[{item.chunk.id}] {item.chunk.content}" for item in retrieved)
                    response = await generate_chat_response(messages, client)
                    return GroundedAnswer(source_chunk_ids=source_chunk_ids, answer=response.content, ...)
            """).strip(),
            "usage": (
                "Retrieval-augmented generation akışını uygular. Önce chunk'ları bulur, "
                "sonra LLM'e context ile sorar. `/v1/rag/query` endpoint'i bu fonksiyonu çağırır."
            ),
        },
    ],
    "src/rag/evaluation.py": [
        {
            "name": "run_retrieval_evaluation()",
            "code": dedent("""\
                async def run_retrieval_evaluation(dataset, retriever=None, *, top_k=3):
                    for case in dataset:
                        retrieved_ids = [item.chunk.id for item in await retriever.retrieve(case.query)]
                        results.append(RetrievalEvalResult(
                            precision_at_k=precision_at_k(retrieved_ids, relevant, k=top_k),
                            recall_at_k=recall_at_k(retrieved_ids, relevant, k=top_k), ...
                        ))
                    return RetrievalEvalReport(mean_precision_at_k=..., mean_recall_at_k=...)
            """).strip(),
            "usage": (
                "Retrieval kalitesini precision@k ve recall@k ile ölçer. "
                "`GET /v1/rag/eval` endpoint'i default eval dataset ile bu raporu döner."
            ),
        },
    ],
    "src/api/routers/rag.py": [
        {
            "name": "rag_query()",
            "code": dedent("""\
                @router.post("/rag/query", response_model=RagQueryResponse)
                async def rag_query(body: RagQueryRequest, client=Depends(get_llm_client)):
                    result = await answer_with_sources(body.question, client, top_k=body.top_k)
                    return RagQueryResponse(source_chunk_ids=result.source_chunk_ids, answer=result.answer, ...)
            """).strip(),
            "usage": (
                "Grounded RAG sorgu endpoint'idir. Kaynak chunk'lar ve LLM cevabını "
                "birlikte döner; learning hub RAG lab'ında kullanılır."
            ),
        },
    ],
    "src/rag/preparation.py": [
        {
            "name": "prepare_documents()",
            "code": dedent("""\
                def prepare_documents(documents, *, chunk_size=120, overlap=30, strategy="fixed"):
                    for document in documents:
                        text = normalize_text(clean_text(document.content))
                        parts = chunk_by_words(text) if strategy == "words" else chunk_text(text, ...)
                        prepared.append(PreparedChunk(chunk_id=f"{document.id}-chunk-{index}", ...))
                    return prepared
            """).strip(),
            "usage": "RAG data prep: clean → normalize → chunk → metadata enrichment pipeline.",
        },
    ],
    "src/rag/pipeline.py": [
        {
            "name": "rag_pipeline()",
            "code": dedent("""\
                async def rag_pipeline(user_query, client, *, top_k=5, include_judge=True):
                    normalized = rewrite_query(user_query)
                    dense = await retriever.retrieve(normalized, top_k=top_k * 2)
                    reranked = rerank(normalized, dense, top_k=top_k)
                    context = build_context(reranked)
                    answer = await generate_chat_response(messages, client)
                    if include_judge:
                        result["eval"] = await judge_answer(question=..., context=context, answer=...)
                    return result
            """).strip(),
            "usage": "End-to-end RAG: rewrite → retrieve → rerank → context → generate → judge eval.",
        },
    ],
    "src/rag/reranker.py": [
        {
            "name": "rerank()",
            "code": dedent("""\
                def rerank(query, candidates, *, top_k=5):
                    for item in candidates:
                        joint_score = (0.6 * item.score) + (0.4 * keyword_overlap)
                    return sorted_results[:top_k]
            """).strip(),
            "usage": "Mock cross-encoder second-stage ranking after hybrid retriever.",
        },
    ],
    "src/rag/query_rewrite.py": [
        {
            "name": "rewrite_query()",
            "code": dedent("""\
                def rewrite_query(query: str) -> str:
                    for phrase, expansion in EXPANSION_MAP.items():
                        if phrase in query.lower():
                            query = f"{query} {expansion}"
                    return query
            """).strip(),
            "usage": "Acronym and shorthand expansion (KMH, FAST, kart kayıp) before retrieval.",
        },
    ],
    "src/evals/judge.py": [
        {
            "name": "judge_answer()",
            "code": dedent("""\
                async def judge_answer(*, question, context, answer, client=None) -> JudgeRubric:
                    return JudgeRubric(
                        groundedness=..., correctness=..., completeness=..., safety=..., reason="..."
                    )
            """).strip(),
            "usage": "LLM-as-a-Judge rubric scoring for RAG answers; GET /v1/evals/judge golden eval.",
        },
    ],
    "src/case_study/bank_chatbot.py": [
        {
            "name": "bank_chatbot()",
            "code": dedent("""\
                async def bank_chatbot(*, user_id, query, session, client):
                    if guardrail.blocked: return blocked_response
                    intent = _map_intent(classification.intent.value, query)
                    if not authorize_action(session, intent): return auth_required
                    if intent in ("general_faq",): return rag_answer
                    if intent == "money_transfer": return mfa_required_message
            """).strip(),
            "usage": "Bank chatbot reference flow: guardrails → intent → policy → RAG or secure API.",
        },
    ],
    # --- Stage 7: Data layer ---
    "src/data/models.py": [
        {
            "name": "ConversationORM",
            "code": dedent("""\
                class ConversationORM(Base):
                    __tablename__ = "conversations"
                    id: Mapped[str] = mapped_column(String(36), primary_key=True)
                    user_id: Mapped[str] = mapped_column(String(128), index=True)
                    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
                    messages: Mapped[list["MessageORM"]] = relationship(back_populates="conversation")
            """).strip(),
            "usage": (
                "SQLAlchemy ORM modeli; konuşma oturumlarını temsil eder. "
                "Workflow router yeni konuşma oluşturur ve mesajları bu tabloya bağlar."
            ),
        },
        {
            "name": "ToolCallORM",
            "code": dedent("""\
                class ToolCallORM(Base):
                    __tablename__ = "tool_calls"
                    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_tool_calls_idempotency_key"),)
                    tool_name: Mapped[str]
                    idempotency_key: Mapped[str]
                    status: Mapped[str] = mapped_column(default="pending")
            """).strip(),
            "usage": (
                "Tool çağrılarının kalıcı kaydıdır. Idempotency key unique constraint "
                "ile tekrarlayan isteklerin çift çalışması engellenir."
            ),
        },
    ],
    "src/data/repositories.py": [
        {
            "name": "MessageRepository",
            "code": dedent("""\
                class MessageRepository:
                    def add_message(self, *, conversation_id, role, content) -> MessageORM:
                        message = MessageORM(
                            conversation_id=conversation_id, role=role,
                            content=mask_pii(content),
                        )
                        session.add(message)
                        session.commit()
            """).strip(),
            "usage": (
                "Konuşma mesajlarını DB'ye yazar; içerik PII maskelenerek saklanır. "
                "Workflow endpoint her kullanıcı mesajını bu repo ile persist eder."
            ),
        },
        {
            "name": "AuditLogRepository",
            "code": dedent("""\
                class AuditLogRepository:
                    def append(self, *, actor, action, risk_level, details) -> AuditLogORM:
                        row = AuditLogORM(
                            actor=actor, action=action,
                            details_json=json.dumps(mask_mapping(details), ...),
                            correlation_id=get_correlation_id(),
                        )
            """).strip(),
            "usage": (
                "Compliance audit kayıtlarını kalıcı olarak yazar. Tool execution "
                "service ve security router bu repository'yi kullanır."
            ),
        },
    ],
    "src/data/tool_execution.py": [
        {
            "name": "ToolExecutionService",
            "code": dedent("""\
                class ToolExecutionService:
                    async def execute_tool(self, *, conversation_id, tool, tool_name, arguments,
                                           idempotency_key, approval_id, risk_level):
                        existing = self.tool_call_repo.get_by_idempotency_key(idempotency_key)
                        if existing and existing.status == "completed":
                            return ToolResult(..., metadata={"replayed": True}), True
                        result = await tool.run(arguments)
                        self.tool_call_repo.save_completed(...)
                        self.audit_repo.append(action="tool_call_completed", ...)
            """).strip(),
            "usage": (
                "Idempotent tool çalıştırma ve audit kaydı tek serviste toplanır. "
                "Workflow execute_tool node'u mock tool yerine bu servisi kullanır; "
                "aynı idempotency key ile tekrar çağrı replay döner."
            ),
        },
    ],
    "src/data/bootstrap.py": [
        {
            "name": "get_data_stores()",
            "code": dedent("""\
                @lru_cache
                def get_data_stores() -> DataStores:
                    settings = get_settings()
                    return build_data_stores(settings.database_url)

                @dataclass
                class DataStores:
                    conversation_repo: ConversationRepository
                    tool_execution_service: ToolExecutionService
                    audit_repo: AuditLogRepository
            """).strip(),
            "usage": (
                "Tüm repository ve servisleri tek pakette sunar. Router'lar "
                "`get_data_stores()` ile DB erişimini alır; testlerde farklı "
                "database_url ile override edilebilir."
            ),
        },
    ],
    "src/data/schema.sql": [
        {
            "name": "conversations table",
            "code": dedent("""\
                CREATE TABLE conversations (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(128) NOT NULL,
                    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """).strip(),
            "usage": (
                "PostgreSQL production şemasının referans tanımıdır. SQLAlchemy ORM "
                "modelleri bu tablo yapısıyla uyumludur; Terraform RDS bu şemayı "
                "migrate eder."
            ),
        },
        {
            "name": "tool_calls idempotency",
            "code": dedent("""\
                CREATE TABLE tool_calls (
                    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
                    tool_name VARCHAR(128) NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    ...
                );
            """).strip(),
            "usage": (
                "Tool çağrıları için idempotency ve audit alanlarını tanımlar. "
                "Unique constraint tekrarlayan finansal işlemlerin çift kaydını önler."
            ),
        },
    ],
    # --- Stage 8: Data analyst ---
    "src/agents/data_analyst.py": [
        {
            "name": "run_data_analyst()",
            "code": dedent("""\
                async def run_data_analyst(*, question, tenant_id, client, approval_granted=False):
                    generated_sql, final_sql, correctness, sql_repaired = await generate_validated_sql(...)
                    guardrail = validate_sql(final_sql, tenant_id=tenant_id)
                    if guardrail.needs_human_approval and not approval_granted:
                        return DataAnalystResult(needs_human_approval=True, executed=False, ...)
                    rows = execute_safe_select(final_sql, tenant_id=tenant_id)
                    return DataAnalystResult(executed=True, rows=rows, analysis_summary=..., ...)
            """).strip(),
            "usage": (
                "Text-to-SQL analyst pipeline'ının ana giriş noktasıdır. "
                "SQL üret → guardrail → correctness → onay → execute → özet akışını "
                "yönetir. `/v1/analyst/query` bu fonksiyonu çağırır."
            ),
        },
        {
            "name": "generate_validated_sql()",
            "code": dedent("""\
                async def generate_validated_sql(question, tenant_id, client, *, max_regenerations=2):
                    final_sql = await generate_sql_query(question, tenant_id, client)
                    for attempt in range(max_regenerations + 1):
                        safety = validate_sql(final_sql, tenant_id=tenant_id)
                        correctness = validate_sql_correctness(final_sql, question=..., tenant_id=...)
                        if safety.allowed and correctness.is_correct:
                            return generated_sql, final_sql, correctness, repaired
                        # LLM regeneration with build_sql_regeneration_messages(...)
            """).strip(),
            "usage": (
                "Üretilen SQL'i güvenlik ve doğruluk kontrolünden geçirir; "
                "hatalıysa LLM ile yeniden üretir. Mock client SQL senaryolarını "
                "keyword'e göre simüle eder."
            ),
        },
    ],
    "src/security/guardrails.py": [
        {
            "name": "validate_sql()",
            "code": dedent("""\
                def validate_sql(sql: str, *, tenant_id=None, max_rows=1000) -> SqlGuardrailResult:
                    for keyword in FORBIDDEN_KEYWORDS:
                        if re.search(rf"\\b{keyword}\\b", upper):
                            return SqlGuardrailResult(allowed=False, reasons=[...])
                    if not upper.startswith("SELECT"):
                        return SqlGuardrailResult(allowed=False, reasons=["Only SELECT allowed"])
                    if "JOIN" in upper:
                        needs_human_approval = True
                    return SqlGuardrailResult(allowed=True, needs_human_approval=..., ...)
            """).strip(),
            "usage": (
                "SQL injection ve tehlikeli komutları engeller. DELETE/DROP gibi "
                "keyword'ler reddedilir; JOIN ve SUM(amount) onay gerektirir. "
                "Analyst pipeline her SQL'i bu fonksiyondan geçirir."
            ),
        },
    ],
    "src/security/sql_correctness.py": [
        {
            "name": "validate_sql_correctness()",
            "code": dedent("""\
                def validate_sql_correctness(sql, *, question, tenant_id) -> SqlCorrectnessResult:
                    intent = detect_sql_intent(question)
                    if intent == SqlIntent.AGGREGATE_TOTAL and "SUM(" not in upper:
                        issues.append("Aggregate question requires SUM(amount)")
                    if intent == SqlIntent.TOP_N and "ORDER BY" not in upper:
                        issues.append("Top-N question requires ORDER BY clause")
                    return SqlCorrectnessResult(is_correct=len(issues) == 0, intent=intent, ...)
            """).strip(),
            "usage": (
                "LLM SQL'inin soru niyetine uyup uymadığını kontrol eder. "
                "Schema, tenant filter ve intent-semantics eşleşmesi doğrulanır; "
                "hata durumunda canonical SQL ile repair yapılır."
            ),
        },
        {
            "name": "build_canonical_sql()",
            "code": dedent("""\
                def build_canonical_sql(question: str, tenant_id: str) -> str:
                    intent = detect_sql_intent(question)
                    if intent == SqlIntent.AGGREGATE_TOTAL:
                        return f"SELECT SUM(amount) AS total_amount FROM transactions WHERE tenant_id = '{tenant_id}' LIMIT 100"
                    return f"SELECT id, customer_id, amount, category FROM transactions WHERE tenant_id = '{tenant_id}' LIMIT 20"
            """).strip(),
            "usage": (
                "Deterministik referans SQL üretir. Eval ground truth ve otomatik "
                "repair için kullanılır; LLM hatalı SQL ürettiğinde fallback olarak devreye girer."
            ),
        },
    ],
    "src/api/routers/analyst.py": [
        {
            "name": "analyst_query()",
            "code": dedent("""\
                @router.post("/analyst/query", response_model=AnalystResponse)
                async def analyst_query(body: AnalystRequest, client=Depends(get_llm_client)):
                    result = await run_data_analyst(
                        question=body.question, tenant_id=body.tenant_id,
                        client=client, approval_granted=body.approval_granted,
                    )
                    return AnalystResponse(
                        generated_sql=result.generated_sql, final_sql=result.final_sql,
                        sql_correct=result.correctness.is_correct, executed=result.executed, ...
                    )
            """).strip(),
            "usage": (
                "Text-to-SQL analyst HTTP endpoint'idir. Guardrail, correctness ve "
                "execution sonuçlarını tek response'ta birleştirir."
            ),
        },
    ],
    # --- Stage 9: Observability ---
    "src/observability/traces.py": [
        {
            "name": "TraceSession",
            "code": dedent("""\
                class TraceSession:
                    @contextmanager
                    def span(self, name: str, kind: str, **attributes):
                        started = time.perf_counter()
                        try:
                            yield
                        finally:
                            self.spans.append(TraceSpan(name=name, kind=kind, latency_ms=..., ...))

                    def finish(self, status: str) -> TraceSummary:
                        _trace_store[self.trace_id] = TraceRecord(spans=self.spans, summary=summary)
                        return summary
            """).strip(),
            "usage": (
                "OpenTelemetry/LangSmith benzeri in-memory trace oturumudur. "
                "Workflow her node'u span olarak kaydeder; LLM çağrıları ayrıca "
                "`record_llm_span` ile işaretlenir."
            ),
        },
        {
            "name": "start_trace()",
            "code": dedent("""\
                def start_trace(*, run_id=None, prompt_version="v1") -> TraceSession:
                    return TraceSession(run_id=run_id, prompt_version=prompt_version)
            """).strip(),
            "usage": (
                "Workflow başında trace oturumu açar. ContextVar ile aktif trace "
                "taşınır; `generate_chat_response` bu trace'e LLM span ekler."
            ),
        },
    ],
    "src/observability/metrics.py": [
        {
            "name": "MetricsCollector",
            "code": dedent("""\
                class MetricsCollector:
                    def record_llm_call(self, *, model, latency_ms, prompt_tokens, completion_tokens, retry_count, status):
                        self.increment("llm_calls_total")
                        if status != "ok":
                            self.increment("llm_errors_total")
                        self.record_latency(f"llm_latency_ms:{model}", latency_ms)
                        self.set_gauge("llm_estimated_cost_usd_last", estimate_llm_cost_usd(...))

                    def snapshot(self) -> dict:
                        return {"counters": dict(self.counters), "latencies": {...}, "gauges": dict(self.gauges)}
            """).strip(),
            "usage": (
                "In-memory metrik toplayıcıdır. HTTP, LLM ve workflow metriklerini "
                "sayaç, latency histogram ve gauge olarak tutar. Prometheus export "
                "öncesi demo katmanı görevi görür."
            ),
        },
    ],
    "src/api/routers/observability.py": [
        {
            "name": "get_metrics_snapshot()",
            "code": dedent("""\
                @router.get("/metrics", response_model=MetricsSnapshotResponse)
                async def get_metrics_snapshot():
                    snapshot = get_metrics().snapshot()
                    return MetricsSnapshotResponse(**snapshot)
            """).strip(),
            "usage": (
                "`GET /v1/observability/metrics` endpoint'idir. LLM çağrı sayısı, "
                "latency ve tahmini maliyet metriklerini JSON olarak döner."
            ),
        },
        {
            "name": "get_trace_summary()",
            "code": dedent("""\
                @router.get("/traces/{trace_id}", response_model=TraceSummaryResponse)
                async def get_trace_summary(trace_id: str):
                    record = get_trace_store().get(trace_id)
                    if record is None:
                        raise HTTPException(status_code=404, detail="Trace not found")
                    return TraceSummaryResponse(**record.summary.model_dump())
            """).strip(),
            "usage": (
                "Belirli bir trace'in timeline ve maliyet özetini döner. "
                "Frontend `AgenticApiClient.getTrace()` ile workflow sonrası "
                "trace detayını gösterir."
            ),
        },
    ],
    # --- Stage 10: Evals & guardrails ---
    "src/evals/run_evals.py": [
        {
            "name": "run_all_evals()",
            "code": dedent("""\
                async def run_all_evals(client=None) -> dict:
                    classification = await run_classification_eval(client)
                    analyst = await run_analyst_eval(client)
                    return {
                        "total": classification["total"] + analyst["total"],
                        "passed": classification["passed"] + analyst["passed"],
                        "suites": {"classification": classification, "analyst": analyst},
                    }
            """).strip(),
            "usage": (
                "Classification ve analyst eval suite'lerini birleştirir. "
                "`GET /v1/evals/run` ve CI pipeline `python -m src.evals.run_evals` "
                "ile regression kontrolü yapar."
            ),
        },
        {
            "name": "run_classification_eval()",
            "code": dedent("""\
                async def run_classification_eval(client=None) -> dict:
                    for case in _load_jsonl(CLASSIFICATION_DATASET_PATH):
                        if case.get("should_block"):
                            ok = validate_user_input(case["message"]).blocked
                        else:
                            result = await classify_customer_message(case["message"], client)
                            ok = result.intent.value == case["expected_intent"]
                    return _build_eval_report(total=len(cases), passed=passed, cases=cases)
            """).strip(),
            "usage": (
                "Golden dataset üzerinde classifier doğruluğunu ölçer. "
                "Prompt injection block ve intent/risk eşleşmesi case bazında "
                "pass/fail raporlanır."
            ),
        },
    ],
    "src/security/input_guardrails.py": [
        {
            "name": "validate_user_input()",
            "code": dedent("""\
                def validate_user_input(text: str) -> InputGuardrailResult:
                    injection_hits = detect_prompt_injection(text)
                    exfiltration_hits = detect_data_exfiltration(text)
                    if injection_hits or exfiltration_hits:
                        return InputGuardrailResult(
                            allowed=False, blocked=True, risk_level="high",
                            categories=[...], reasons=[...],
                        )
                    return InputGuardrailResult(allowed=True, blocked=False)
            """).strip(),
            "usage": (
                "Kullanıcı mesajlarında prompt injection ve veri sızdırma kalıplarını "
                "regex ile tarar. Classifier, classify endpoint ve workflow girişinde "
                "ilk savunma hattıdır."
            ),
        },
        {
            "name": "validate_tool_arguments()",
            "code": dedent("""\
                def validate_tool_arguments(tool_name: str, arguments: dict) -> InputGuardrailResult:
                    schema = TOOL_ARGUMENT_SCHEMAS.get(tool_name)
                    for field in schema.get("required", []):
                        if field not in arguments:
                            reasons.append(f"Missing required tool argument: {field}")
                    if tool_name == "transfer_money" and amount > schema["max_amount"]:
                        reasons.append("Transfer amount exceeds policy limit")
            """).strip(),
            "usage": (
                "Tool çalıştırma öncesi argüman şema ve limit kontrolü yapar. "
                "Transfer tutarı, IBAN formatı ve zorunlu alanlar doğrulanır."
            ),
        },
    ],
    "src/security/pii.py": [
        {
            "name": "mask_pii()",
            "code": dedent("""\
                def mask_pii(text: str) -> str:
                    masked = _EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
                    masked = _PHONE_PATTERN.sub("[PHONE_REDACTED]", masked)
                    masked = _IBAN_PATTERN.sub("[IBAN_REDACTED]", masked)
                    return masked
            """).strip(),
            "usage": (
                "Email, telefon ve IBAN gibi PII kalıplarını log ve DB kayıtlarından "
                "önce maskeler. Message repository, audit log ve feedback store "
                "bu fonksiyonu kullanır."
            ),
        },
    ],
    # --- Stage 11: Audit & security API ---
    "src/security/audit.py": [
        {
            "name": "build_tool_audit_event()",
            "code": dedent("""\
                def build_tool_audit_event(
                    *, actor, tenant_id, action, tool_name, arguments, approval_id=None, ...
                ) -> ComplianceAuditEvent:
                    return ComplianceAuditEvent(
                        actor=actor, action=action, tool_name=tool_name,
                        args_summary=minimize_tool_arguments(tool_name, arguments),
                        trace_id=trace.trace_id if trace else None,
                        correlation_id=get_correlation_id(), ...
                    )
            """).strip(),
            "usage": (
                "Tool çağrıları için standart compliance audit event'i oluşturur. "
                "Argümanlar allowlist + PII mask ile minimize edilir; trace ve "
                "correlation ID otomatik eklenir."
            ),
        },
        {
            "name": "to_persistence_payload()",
            "code": dedent("""\
                def to_persistence_payload(event: ComplianceAuditEvent) -> dict:
                    return {
                        "event_id": event.event_id,
                        "actor": event.actor,
                        "action": event.action,
                        "args_summary": event.args_summary,
                        "trace_id": event.trace_id,
                        "correlation_id": event.correlation_id,
                        ...
                    }
            """).strip(),
            "usage": (
                "Audit event'i DB ve structured log formatına normalize eder. "
                "ToolExecutionService tamamlanan ve replay edilen çağrıları "
                "bu payload ile persist eder."
            ),
        },
    ],
    "src/api/routers/security.py": [
        {
            "name": "list_recent_audit_logs()",
            "code": dedent("""\
                @router.get("/audit/recent", response_model=AuditLogListResponse)
                async def list_recent_audit_logs(limit: int = Query(default=20, ge=1, le=100)):
                    stores = get_data_stores()
                    rows = stores.audit_repo.list_recent(limit=limit)
                    entries = [AuditLogEntryResponse(id=row.id, actor=row.actor, ...) for row in rows]
                    return AuditLogListResponse(entries=entries)
            """).strip(),
            "usage": (
                "`GET /v1/security/audit/recent` endpoint'idir. Son compliance "
                "audit kayıtlarını JSON olarak döner; learning hub güvenlik "
                "lab'ında incelenir."
            ),
        },
    ],
    # --- Stage 12: Deploy & CI ---
    "Dockerfile": [
        {
            "name": "HEALTHCHECK",
            "code": dedent("""\
                FROM python:3.11-slim AS runtime
                ENV PYTHONPATH=/app APP_ENV=production
                COPY requirements.txt ./
                RUN pip install --no-cache-dir -r requirements.txt
                COPY src ./src
                EXPOSE 8000
                HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
                    CMD curl -fsS http://127.0.0.1:8000/health || exit 1
                CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
            """).strip(),
            "usage": (
                "Production FastAPI container imajını tanımlar. Slim Python base, "
                "dependency install ve uvicorn CMD içerir. HEALTHCHECK `/health` "
                "endpoint'ini periyodik kontrol eder; ECS task health için kritiktir."
            ),
        },
    ],
    "infra/terraform/": [
        {
            "name": "aws_ecr_repository",
            "code": dedent("""\
                resource "aws_ecr_repository" "api" {
                  name                 = "${var.project_name}-api"
                  image_tag_mutability = "MUTABLE"
                  image_scanning_configuration { scan_on_push = true }
                }

                resource "aws_secretsmanager_secret" "openai_api_key" {
                  name = "${var.project_name}/${var.environment}/openai-api-key"
                }
            """).strip(),
            "usage": (
                "Terraform IaC'nin çekirdek kaynaklarıdır. ECR container registry, "
                "Secrets Manager API key ve CloudWatch log group tanımlar. "
                "ECS task definition bu secret'ları environment'a enjekte eder."
            ),
        },
        {
            "name": "aws_lb_target_group",
            "code": dedent("""\
                resource "aws_lb_target_group" "api" {
                  port        = 8000
                  protocol    = "HTTP"
                  health_check {
                    path     = "/health"
                    interval = 30
                    matcher  = "200"
                  }
                }
            """).strip(),
            "usage": (
                "ALB target group FastAPI container'ına trafik yönlendirir. "
                "Health check `/health` path'ini kullanır; unhealthy task'lar "
                "otomatik devre dışı bırakılır."
            ),
        },
    ],
    ".github/workflows/ci.yml": [
        {
            "name": "test job",
            "code": dedent("""\
                jobs:
                  test:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/setup-python@v5
                        with:
                          python-version: "3.11"
                      - run: pip install -r requirements.txt
                      - run: pytest -q
                      - run: python -m src.evals.run_evals
            """).strip(),
            "usage": (
                "Her push ve PR'da pytest ve mock eval regression çalıştırır. "
                "Classification ve analyst golden dataset skorları düşerse CI kırılır."
            ),
        },
        {
            "name": "docker-build job",
            "code": dedent("""\
                  docker-build:
                    needs: test
                    steps:
                      - run: docker build -t agentic-ai-prep:ci .
                      - run: |
                          docker run -d --name agenticai-ci -p 18000:8000 \\
                            -e LLM_PROVIDER=mock agentic-ai-prep:ci
                          curl -fsS http://127.0.0.1:18000/health
            """).strip(),
            "usage": (
                "Test geçtikten sonra Docker imajı build eder ve container içinde "
                "health smoke testi yapar. Production deploy öncesi imajın "
                "çalıştığını doğrular."
            ),
        },
    ],
    # --- Stage 13: Frontend & feedback ---
    "frontend/app.js": [
        {
            "name": "legacy entry",
            "code": dedent("""\
                /* Legacy entry — hub.js is the main app. Kept for static asset tests. */
                export {};
            """).strip(),
            "usage": (
                "Eski frontend giriş dosyasıdır; asıl uygulama `hub.js` üzerinden "
                "çalışır. Static asset testleri ve geriye dönük uyumluluk için "
                "tutulmuştur."
            ),
        },
    ],
    "frontend/src/client.ts": [
        {
            "name": "AgenticApiClient",
            "code": dedent("""\
                export class AgenticApiClient {
                  constructor(private readonly baseUrl: string = "") {}

                  runWorkflow(body: WorkflowRequest): Promise<WorkflowResponse> {
                    return this.request<WorkflowResponse>("/v1/workflow/run", {
                      method: "POST", body: JSON.stringify(body),
                    });
                  }

                  async *streamChat(body: ChatRequest): AsyncGenerator<StreamChunk> {
                    const response = await fetch(`${this.baseUrl}/v1/chat`, {...});
                    // SSE data: lines parse → yield StreamChunk
                  }
                }
            """).strip(),
            "usage": (
                "TypeScript API client'ıdır. Workflow, chat, trace ve feedback "
                "endpoint'lerini tip güvenli şekilde sarmalar. Frontend demo "
                "ve hub UI bu sınıfı kullanır."
            ),
        },
        {
            "name": "mapStepLabel()",
            "code": dedent("""\
                export function mapStepLabel(step: string): string {
                  const labels: Record<string, string> = {
                    classify_intent: "Niyet analizi",
                    retrieve_context: "Bilgi aranıyor",
                    execute_tool: "İşlem yürütülüyor",
                    final_answer: "Yanıt oluşturuluyor",
                  };
                  return labels[step] ?? step;
                }
            """).strip(),
            "usage": (
                "Workflow step id'lerini Türkçe UI etiketlerine çevirir. "
                "Frontend timeline görünümünde teknik node adları yerine "
                "kullanıcı dostu metin gösterilir."
            ),
        },
    ],
    "src/api/routers/feedback.py": [
        {
            "name": "submit_feedback()",
            "code": dedent("""\
                @router.post("/feedback", response_model=FeedbackResponse)
                async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
                    record = append_feedback(
                        user_id=body.user_id, conversation_id=body.conversation_id,
                        rating=body.rating, comment=body.comment,
                        trace_id=body.trace_id, run_id=body.run_id,
                    )
                    return FeedbackResponse(**record)
            """).strip(),
            "usage": (
                "Kullanıcı geri bildirimini toplar. Positive/negative rating, "
                "yorum ve ilişkili trace/run id'leri JSONL dosyasına yazılır."
            ),
        },
    ],
    "src/evals/feedback_store.py": [
        {
            "name": "append_feedback()",
            "code": dedent("""\
                def append_feedback(*, user_id, conversation_id, rating, comment="", trace_id=None, ...):
                    record = {
                        "feedback_id": str(uuid4()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "rating": rating,
                        "comment": mask_pii(comment),
                        "message_preview": mask_pii(message_preview[:240]),
                    }
                    with FEEDBACK_PATH.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(record, ensure_ascii=False) + "\\n")
                    return record
            """).strip(),
            "usage": (
                "Geri bildirimleri `data/feedback.jsonl` dosyasına ekler. "
                "PII maskelenir; offline analiz ve prompt iyileştirme döngüsü "
                "için ham veri kaynağıdır."
            ),
        },
        {
            "name": "list_feedback()",
            "code": dedent("""\
                def list_feedback(*, limit: int = 20) -> list[dict]:
                    if not FEEDBACK_PATH.exists():
                        return []
                    lines = FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()
                    items = [json.loads(line) for line in lines[-limit:]]
                    return list(reversed(items))
            """).strip(),
            "usage": (
                "Son N geri bildirim kaydını okur. `GET /v1/feedback/recent` "
                "endpoint'i bu fonksiyonu kullanarak dashboard'a veri sağlar."
            ),
        },
    ],
}
