# Agentic AI Prep — Expert AI/LLM Data Scientist Mülakat Hazırlık Planı

Bu plan, `Expert AI/LLM Data Scientist in Agentic AI` rolü için hazırlanmıştır. Hedef sadece kavram ezberlemek değil; Python ağırlıklı, çalıştırılabilir, production mantığı olan küçük ama gerçekçi AI/agent servisleri geliştirerek mülakatta senior/expert seviyede cevap verebilmektir.

Rolün ana beklentileri:

- LLM destekli agent'lar tasarlamak, geliştirmek ve production'a taşımak.
- Agent'ların veri, araçlar, API'ler ve iş uygulamalarıyla güvenli şekilde etkileşmesini sağlamak.
- LangGraph, LangChain, Semantic Kernel, AutoGen, CrewAI benzeri agentic framework mantığını bilmek.
- RAG, embedding, vector database, memory ve retrieval sistemleri kurmak.
- Python ile production-ready servisler yazmak.
- Evaluation, safety, guardrail, observability ve banking compliance risklerini yönetmek.
- Business problemi teknik mimariye, teknik mimariyi ölçülebilir iş etkisine çevirmek.

## Çalışma Formatı

Her aşamada aynı mülakat simülasyonu formatını kullanacağız:

| Bölüm | İçerik |
| --- | --- |
| Soru | Gerçek mülakatta gelebilecek şekilde sorulur. |
| Beklenen cevap | Senior/expert seviyede teknik cevap özeti. |
| Derinleştirme | Follow-up sorularla trade-off, failure mode, güvenlik ve production düşüncesi ölçülür. |
| Kırmızı bayraklar | Zayıf cevapta görülen riskli sinyaller. |
| Güçlü sinyaller | Seni öne çıkaracak yaklaşım, terminoloji ve örnekler. |
| Canlı kod görevi | Python ağırlıklı, çalışan küçük uygulama veya test yazılır. |
| DoD | Definition of Done: test, run command, logging, hata senaryosu, kısa mimari notu. |

Her modül sonunda şunlar hazır olmalı:

- Çalışan kod.
- En az 3 gerçekçi mülakat sorusuna güçlü cevap.
- En az 1 canlı kod egzersizi.
- En az 1 failure mode analizi.
- En az 1 test veya evaluation kontrolü.
- Kısa mimari karar notu.

## Önerilen Repository Yapısı

Kodları aşama aşama ekleyeceğiz. Başlangıçta tüm dosyaları üretmek yerine her aşamada sadece gereken parçayı yazacağız.

```text
agentic_ai_prep/
  agentic_ai_mulakat_hazirlik_plani.md
  README.md
  requirements.txt
  .env
  src/
    common/
      config.py
      logging.py
      errors.py
      retry.py
      schemas.py
    llm/
      base.py
      mock_client.py
      openai_client.py
      tool_calling.py
      structured_output.py
    api/
      main.py
      routers/
        chat.py
        ingest.py
        agent.py
    agents/
      state.py
      tools.py
      workflow.py
      policies.py
    rag/
      documents.py
      chunking.py
      embeddings.py
      retriever.py
      evaluation.py
    data/
      models.py
      repositories.py
      migrations/
    evals/
      golden_dataset.jsonl
      run_evals.py
    observability/
      traces.py
      metrics.py
    security/
      pii.py
      guardrails.py
      audit.py
  tests/
    test_retry.py
    test_structured_output.py
    test_rag.py
    test_agent_policy.py
```

İlk prensip: API anahtarı olmayan ortamda da demo çalışmalı. Bu yüzden önce `MockLLMClient` ile offline çalışan sistemi kuracağız, sonra gerçek OpenAI/Azure OpenAI adapter'ını ekleyeceğiz.

## Çalıştırma Standardı

Her canlı kod aşaması şu komutlarla doğrulanabilir olmalı:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
uvicorn src.api.main:app --reload
```

Gerçek LLM çağrısı gereken yerlerde:

```powershell
copy infra\terraform\terraform.tfvars.example infra\terraform\terraform.tfvars
# OPENAI_API_KEY veya AZURE_OPENAI_* değerleri .env içine eklenir
```

Mülakat açısından önemli cümle:

> "Ben agent sistemlerinde önce deterministic, test edilebilir ve gözlemlenebilir bir omurga kurarım; LLM'i bu omurganın içinde kontrollü bir karar/veri üretim bileşeni olarak konumlandırırım."

## Değerlendirme Rubriği

| Seviye | Cevap karakteri |
| --- | --- |
| Junior | Kavramları bilir ama failure mode, güvenlik, maliyet ve operasyon düşünmez. |
| Mid | Uygulamayı yazabilir ama production trade-off'ları sınırlıdır. |
| Senior | Test, monitoring, retry, timeout, güvenlik, data isolation ve deployment risklerini anlatır. |
| Expert | Architecture, governance, cost, reliability, compliance, business impact ve takım etkisini birlikte ele alır. |

## Aşama 0 - Mülakat Hikayesi ve Ortam Hazırlığı

Amaç: Kendini role net konumlandırmak ve canlı kod ortamını stabil hale getirmek.

Yazılacak kod:

- `README.md`: Projenin amacı, çalıştırma komutları, modül sırası.
- `requirements.txt`: FastAPI, Pydantic, pytest, httpx, tenacity, python-dotenv gibi temel bağımlılıklar.
- `.env`: API key, model adı, log level, database URL (git'e eklenmez).
- `src/common/config.py`: Pydantic settings.
- `src/common/logging.py`: JSON'a yakın structured logging.

Mülakat soruları:

1. Bu rol için kendini nasıl konumlandırırsın?
2. AI agent projesini notebook demosundan production servisine taşırken ilk baktığın şeyler nelerdir?
3. LLM projesinde "çalışıyor" demek için hangi teknik kriterler gerekir?

Beklenen cevap:

- Python ve ML/LLM bilgisini backend engineering, evaluation, observability ve güvenlikle birleştirdiğini söyle.
- PoC ile production arasındaki farkı vurgula: reliability, latency, cost, security, traceability, rollback, tests.
- Bankacılık bağlamında audit log, PII, data minimization ve human approval risklerini özellikle an.

Canlı kod görevi:

- Minimal config ve logging altyapısını yaz.
- Bir `healthcheck` fonksiyonu veya endpoint'i ile ortamın doğru yüklendiğini göster.

DoD:

- `pytest -q` çalışır.
- API key olmadan testler geçer.
- Log formatı request id veya correlation id taşıyabilecek şekilde tasarlanır.

## Aşama 1 - Production-Ready Python Temelleri

Amaç: Sadece script değil, sürdürülebilir Python servis kodu yazabildiğini göstermek.

Konular:

- Async Python.
- Type hints.
- Pydantic modelleme.
- Dataclass kullanımı.
- Custom exception.
- Retry, timeout, circuit breaker.
- Dependency injection.
- Unit test.
- Clean architecture.

Yazılacak kod:

- `src/llm/base.py`: LLM client protocol/interface.
- `src/llm/mock_client.py`: Deterministic mock LLM.
- `src/common/retry.py`: Retry policy helper.
- `tests/test_retry.py`: Timeout ve retry davranışı.
- `tests/test_mock_llm.py`: Mock response testi.

Canlı kod görevi:

```python
class LLMClient(Protocol):
    async def complete(self, messages: list[Message]) -> LLMResponse:
        ...
```

Sonra bu interface'i kullanan ve provider bağımsız çalışan bir servis fonksiyonu yazacağız.

Mülakat soruları:

1. OpenAI API çağrılarında timeout ve retry politikasını nasıl tasarlarsın?
2. Async Python kullanırken blocking bir SDK çağrısını nasıl yönetirsin?
3. LLM client kodunda neden provider interface'i kullanırsın?
4. Production'da agent workflow bazen takılı kalıyorsa debug'a nereden başlarsın?
5. Python servisinde type hint gerçekten ne kazandırır?

Beklenen cevap:

- Timeout her dış çağrıda zorunludur.
- Retry sadece transient hatalarda yapılır; validation ve authorization hataları retry edilmez.
- Idempotency gerektiren tool call'larda retry dikkatli yapılır.
- Provider adapter ile model değişimi, mock test ve fallback kolaylaşır.
- Async çağrılar event loop'u bloklamamalıdır; gerekirse thread pool veya async-native SDK kullanılır.

Kırmızı bayraklar:

- Sonsuz retry.
- Timeout belirtmemek.
- API key'i kod içine yazmak.
- Testlerde gerçek LLM API'sine bağımlı olmak.

Güçlü sinyaller:

- Idempotency key.
- Correlation id.
- Structured exception taxonomy.
- Dependency inversion.
- Deterministic test.

## Aşama 2 - FastAPI ile LLM/Agent Servis Tasarımı

Amaç: Agent sistemini backend servisi olarak expose edebilmek.

Konular:

- REST endpoint tasarımı.
- Request validation.
- Streaming response.
- SSE/WebSocket farkı.
- AuthN/AuthZ.
- Rate limiting.
- Background tasks.
- File upload.
- Multi-tenant isolation.
- API versioning.

Yazılacak kod:

- `src/api/main.py`: FastAPI app.
- `src/api/routers/chat.py`: `/v1/chat` endpoint'i.
- `src/api/routers/agent.py`: `/v1/agent/run` endpoint'i.
- Streaming için async generator.
- Request/response Pydantic şemaları.
- Basic request id middleware.

Canlı kod görevi:

- Mock LLM kullanan `/v1/chat` endpoint'i yaz.
- Aynı endpoint için streaming mode ekle.
- Invalid request için 422, provider timeout için 504 döndür.

Mülakat soruları:

1. GPT-4o kullanan bir `/chat` endpoint'i nasıl tasarlarsın?
2. Agent cevabını frontend'e token token stream etmek için ne kullanırsın?
3. Kullanıcı bazlı conversation history nasıl yönetilir?
4. LLM maliyetlerini API seviyesinde nasıl kontrol edersin?
5. Multi-tenant bir sistemde request izolasyonunu nasıl sağlarsın?

Beklenen cevap:

- Request schema net olur: `user_id`, `conversation_id`, `message`, `metadata`.
- Streaming için SSE çoğu chat UI için yeterlidir; çift yönlü etkileşim gerekiyorsa WebSocket düşünülebilir.
- Conversation history veritabanında tutulur, prompt'a sınırsız basılmaz; özetleme ve retrieval kullanılır.
- Rate limit, token budget, model routing ve cache maliyeti kontrol eder.
- Tenant id auth context'ten gelir; client'ın gönderdiği tenant id'ye kör güvenilmez.

Canlı demo komutu:

```powershell
uvicorn src.api.main:app --reload
```

DoD:

- `/health` döner.
- `/v1/chat` mock cevap üretir.
- Streaming endpoint terminal veya browser ile izlenebilir.
- Hatalar standart response formatıyla döner.

## Aşama 3 - LangChain Temelleri

Amaç: LangChain'i demo aracı değil, composable AI application framework olarak anlatabilmek.

Konular:

- Prompt template.
- Output parser.
- Tool abstraction.
- Retriever.
- Runnable/LCEL.
- Callback handler.
- Structured output.
- LangSmith veya benzer tracing mantığı.

Yazılacak kod:

- `src/llm/structured_output.py`: JSON schema/Pydantic parse katmanı.
- `src/agents/tools.py`: Basit tool interface.
- `src/rag/retriever.py`: Mock retriever.
- LangChain varsa küçük LCEL chain örneği; yoksa framework bağımsız eşdeğer tasarım.

Canlı kod görevi:

- "Müşteri mesajını sınıflandır" chain'i yaz.
- Output kesinlikle şu schema'ya uysun:

```json
{
  "intent": "knowledge_question | account_action | complaint | unknown",
  "risk_level": "low | medium | high",
  "needs_human_approval": true
}
```

Mülakat soruları:

1. Chain, tool ve retriever arasındaki fark nedir?
2. Structured output üretmek için nasıl bir yaklaşım kullanırsın?
3. Output parser hata verirse ne yaparsın?
4. Callback sistemiyle tracing nasıl yapılır?
5. LangChain kullanırken hangi kısımları framework'e bırakmazsın?

Beklenen cevap:

- Chain deterministik bir işlem hattıdır; tool dış sistem aksiyonudur; retriever bilgi getirir.
- Structured output için JSON schema, Pydantic validation ve retry/repair stratejisi gerekir.
- Tool authorization ve audit'i framework dışında domain katmanında tutmak daha güvenlidir.
- Callback/tracing ile prompt, model, latency, token, tool call ve hata sınıfı izlenir.

Kırmızı bayraklar:

- "LangChain her şeyi çözer" demek.
- Parser hatasını kullanıcıya ham döndürmek.
- Tool'ları authorization olmadan modele açmak.

Güçlü sinyaller:

- Framework bağımsız core logic.
- Contract-first output schema.
- Tracing ve replay edilebilir test.

## Aşama 4 - LangGraph ve Agentic Workflow Tasarımı

Amaç: Multi-step, stateful ve güvenilir agent workflow tasarlayabilmek.

Konular:

- Graph-based workflow.
- Node ve edge.
- State schema.
- Conditional routing.
- Tool-using agent.
- Human-in-the-loop.
- Checkpointing.
- Retry/fallback.
- Deterministic vs agentic akış.
- Guarded execution.

Yazılacak kod:

- `src/agents/state.py`: Agent state modeli.
- `src/agents/workflow.py`: Basit graph/workflow.
- `src/agents/policies.py`: Tool permission ve approval kuralları.
- `tests/test_agent_policy.py`: Riskli tool çağrısı engelleniyor mu?

Canlı kod görevi:

Bir customer support workflow'u yazacağız:

1. `classify_intent`
2. `retrieve_context`
3. `decide_action`
4. `request_human_approval` gerekirse
5. `execute_tool` izinliyse
6. `final_answer`
7. `audit_log`

Mülakat soruları:

1. LangGraph neden klasik agent executor'dan daha uygun olabilir?
2. Müşteri destek agent'ı için state schema nasıl tasarlanır?
3. Agent yanlış tool seçerse bunu nasıl engellersin?
4. Multi-step workflow'da checkpointing neden önemlidir?
5. Bir node başarısız olursa recovery stratejin ne olur?

Beklenen cevap:

- Graph yaklaşımı state, routing, retry ve checkpoint kontrolünü explicit hale getirir.
- Her node idempotent tasarlanırsa retry güvenli olur.
- Riskli aksiyonlarda human approval ve policy engine gerekir.
- Checkpoint sayesinde uzun workflow kaldığı yerden devam eder, debug ve audit kolaylaşır.
- Agentic kararlar deterministic guardrail'lerle sınırlandırılır.

Kırmızı bayraklar:

- Modelin seçtiği her tool'u doğrudan çalıştırmak.
- State'i serbest text olarak tutmak.
- Retry sırasında aynı finansal işlemi tekrar çalıştırmak.

Güçlü sinyaller:

- Explicit state machine.
- Permission boundary.
- Approval gates.
- Checkpoint and replay.
- Tool result validation.

## Aşama 5 - GPT-4o / OpenAI API / Azure OpenAI Kullanımı

Amaç: Model çağırmanın ötesinde, güvenilir AI product component tasarlamak.

Konular:

- Chat/Responses pattern.
- Tool calling.
- Structured outputs.
- JSON schema validation.
- Multimodal input.
- Token budget.
- Context management.
- Cost optimization.
- Prompt versioning.
- Safety filters.
- Model fallback.

Yazılacak kod:

- `src/llm/openai_client.py`: Gerçek provider adapter.
- `src/llm/tool_calling.py`: Tool call parse/validate.
- `src/common/config.py`: Model adı, provider mode.
- `tests/test_structured_output.py`: Mock response ile schema testi.

Canlı kod görevi:

- `MockLLMClient` ile başlayan sistemi provider config'e göre `OpenAIClient` kullanabilir hale getir.
- Structured output bozuk gelirse validation hatası yakala ve kontrollü retry yap.
- Model fallback mantığını interface seviyesinde göster.

Mülakat soruları:

1. GPT-4o modelini hangi use-case'lerde tercih edersin?
2. Structured JSON output'u nasıl garantiye yaklaştırırsın?
3. Model hallucination üretiyorsa sistemsel olarak ne yaparsın?
4. Aynı agent için model fallback nasıl tasarlanır?
5. Prompt injection'a karşı nasıl savunma kurarsın?

Beklenen cevap:

- Model seçimi latency, cost, reasoning ihtiyacı, multimodal ihtiyaç ve compliance'a göre yapılır.
- Structured output için schema, validation, retry, fallback ve eval gerekir.
- Hallucination sadece prompt ile çözülmez; retrieval grounding, citations, confidence, abstention ve evaluation gerekir.
- Fallback sadece model adı değiştirmek değildir; kalite, token, latency ve tool compatibility kontrol edilir.
- Prompt injection için instruction hierarchy, content sanitization, tool allowlist ve retrieval isolation gerekir.

DoD:

- API key yokken mock mod çalışır.
- API key varken gerçek adapter devreye alınabilir.
- Her LLM çağrısı latency, token/cost tahmini ve model adı loglar.

## Aşama 6 - RAG, Retrieval ve Memory Systems

Amaç: Grounded ve context-aware agent geliştirebilmek.

Konular:

- Document ingestion.
- Chunking.
- Embedding.
- Vector search.
- Hybrid search.
- Reranking.
- Metadata filtering.
- Query rewriting.
- Context compression.
- Conversation memory.
- Long-term memory.
- Retrieval evaluation.

Yazılacak kod:

- `src/rag/documents.py`: Document modeli.
- `src/rag/chunking.py`: Chunking stratejileri.
- `src/rag/embeddings.py`: Mock embedding ve opsiyonel provider adapter.
- `src/rag/retriever.py`: Basit in-memory vector retrieval.
- `src/rag/evaluation.py`: Precision@k benzeri basit ölçüm.
- `tests/test_rag.py`: Retrieval kalitesi için mini dataset.

Canlı kod görevi:

- Örnek bankacılık iç doküman parçalarından küçük bilgi tabanı oluştur.
- Kullanıcı sorusuna en ilgili chunk'ları getir.
- Cevap üretmeden önce kaynak chunk id'lerini göster.

Mülakat soruları:

1. Banka içi bilgi asistanı için RAG mimarisi nasıl kurarsın?
2. Chunk size ve overlap nasıl seçilir?
3. Vector search kötü sonuç getiriyorsa nasıl iyileştirirsin?
4. RAG sisteminde hallucination nasıl azaltılır?
5. Conversation memory ile knowledge retrieval farkı nedir?

Beklenen cevap:

- Ingestion, parsing, chunking, embedding, indexing, retrieval, reranking, generation ve eval ayrı aşamalardır.
- Chunk seçimi doküman yapısına, model context limitine ve retrieval evaluation sonucuna göre yapılır.
- Kötü retrieval için query rewriting, hybrid search, metadata filters, reranker ve daha iyi chunking denenir.
- Hallucination için grounded prompt, citation, answerability check ve "bilmiyorum" politikası gerekir.
- Conversation memory kullanıcının diyalog bağlamıdır; knowledge retrieval kurumsal bilgi tabanıdır.

Kırmızı bayraklar:

- Tüm dokümanı prompt'a koymak.
- Retrieval kalitesini ölçmemek.
- Kaynak göstermeden kesin cevap üretmek.

Güçlü sinyaller:

- Golden query set.
- Retrieval eval.
- Metadata-aware search.
- Access-controlled retrieval.

## Aşama 7 - PostgreSQL, pgvector ve Data Layer

Amaç: AI uygulamasının veri katmanını sağlam tasarlayabilmek.

Konular:

- PostgreSQL schema design.
- pgvector.
- Transaction management.
- Conversation history.
- Tool execution logs.
- Audit logging.
- Idempotency.
- Indexing.
- Row-level security.
- Data retention.

Yazılacak kod:

- `src/data/models.py`: Conversation, Message, ToolCall, AuditLog modelleri.
- `src/data/repositories.py`: Repository pattern.
- SQL schema taslağı.
- Opsiyonel Docker Compose ile Postgres + pgvector.
- API key veya Docker yoksa SQLite/in-memory fallback.

Canlı kod görevi:

- Conversation history schema tasarla.
- Tool call sonucunu audit log'a yaz.
- Aynı `idempotency_key` ile gelen riskli tool call'ın tekrar çalışmasını engelle.

Mülakat soruları:

1. Agent conversation history için PostgreSQL schema nasıl tasarlarsın?
2. Tool call sonuçlarını nasıl loglarsın?
3. pgvector ile retrieval yapmanın avantajları ve limitleri nelerdir?
4. Production'da migration stratejin ne olur?
5. Sensitive banking verisi için veri izolasyonu nasıl yapılır?

Beklenen cevap:

- Conversation, message, tool_call ve audit_log ayrı modellenir.
- Tool call log'u input, output summary, status, latency, actor, approval id ve correlation id taşır.
- Hassas payload maskelenir veya encrypted storage'a alınır; log'a ham PII basılmaz.
- pgvector operasyonel kolaylık sağlar ama büyük ölçek, hybrid ranking ve advanced retrieval için ayrıca search engine gerekebilir.
- Tenant isolation auth, DB query filter, RLS ve testlerle doğrulanır.

DoD:

- Schema diyagramı veya kısa tablo açıklaması var.
- Idempotency testi geçer.
- Audit log PII maskesi uygular.

## Aşama 8 - Agentic Data Analyst Case

Amaç: Doğal dil sorusunu güvenli veri analizine dönüştüren agent tasarlamak.

Case:

Kullanıcı doğal dille soru sorar. Agent SQL üretir, güvenlik kontrolünden geçirir, PostgreSQL'den veri çeker, sonucu analiz eder ve gerekirse grafik/özet üretir. Riskli sorgularda human approval ister.

Yazılacak kod:

- `src/agents/data_analyst.py`: NL to SQL workflow.
- `src/security/guardrails.py`: SQL policy checks.
- `src/evals/golden_dataset.jsonl`: Örnek soru-SQL beklenen çıktı seti.
- `tests/test_sql_guardrails.py`: `DROP`, `DELETE`, cross-tenant query engelleme.

Canlı kod görevi:

- Basit bir transactions tablosu için read-only SQL üretim akışı simüle et.
- SQL'i çalıştırmadan önce parse/policy check yap.
- Yüksek riskli sorguda `needs_human_approval=True` döndür.

Mülakat soruları:

1. Text-to-SQL agent'ı production'a alırken en büyük riskler nelerdir?
2. LLM'in ürettiği SQL'i nasıl validate edersin?
3. Read-only data analyst agent için permission model nasıl olur?
4. Yanlış analiz sonucu business kararını etkilerse nasıl önlem alırsın?
5. Agent'ın confidence değerini kullanıcıya göstermeli misin?

Beklenen cevap:

- SQL validation için allowlist, AST parser, read-only role, row limit, timeout ve tenant filter gerekir.
- LLM'in ürettiği SQL'e güvenilmez; DB permission son savunma hattıdır.
- Kritik analizlerde source data, query, assumptions ve confidence görünür olmalıdır.
- Evaluation set gerçek business sorularını kapsamalıdır.

## Aşama 9 - Observability, Monitoring ve Debugging

Amaç: Deterministik olmayan agent davranışını production'da izlenebilir hale getirmek.

Konular:

- Structured logging.
- Distributed tracing.
- Prompt/version tracing.
- Token usage.
- Latency breakdown.
- Tool call trace.
- Error categorization.
- User feedback.
- Cost monitoring.
- LangSmith/OpenTelemetry mantığı.

Yazılacak kod:

- `src/observability/traces.py`: Trace context.
- `src/observability/metrics.py`: Basit metrics collector.
- LLM call decorator: model, latency, token, retry count loglar.
- Agent run sonunda trace summary.

Canlı kod görevi:

- Bir agent run için şu timeline'ı üret:
  - classification latency
  - retrieval latency
  - LLM generation latency
  - tool call latency
  - total cost estimate
  - final status

Mülakat soruları:

1. Agent yanlış cevap verdiğinde root cause analysis nasıl yaparsın?
2. LLM latency yüksekse nereden başlarsın?
3. Tool call failure ile model reasoning failure nasıl ayrılır?
4. Hangi metrikleri dashboard'a koyarsın?
5. Prompt değişikliklerinin etkisini nasıl takip edersin?

Beklenen cevap:

- Root cause için trace replay edilir: prompt, retrieved context, model output, tool args, validation result ve final answer incelenir.
- Latency breakdown olmadan optimizasyon yapılmaz.
- Prompt version ve eval score birlikte takip edilir.
- Dashboard metrikleri: success rate, groundedness, tool failure rate, p95 latency, token cost, fallback rate, approval rate, user feedback.

Kırmızı bayraklar:

- Sadece application error log'a bakmak.
- Prompt değişikliklerini versiyonlamamak.
- Cost metriğini dashboard'a koymamak.

Güçlü sinyaller:

- Trace id.
- Replay.
- Golden dataset regression.
- Prompt/model versioning.

## Aşama 10 - Evaluation, Testing ve Guardrails

Amaç: LLM sistemini ölçmeden production'a almamak.

Konular:

- Unit test.
- Integration test.
- Golden dataset.
- Regression test.
- LLM-as-judge.
- Human evaluation.
- Tool call validation.
- JSON schema validation.
- Safety guardrails.
- Prompt injection defense.
- Data leakage prevention.
- Scenario testing.

Yazılacak kod:

- `src/evals/run_evals.py`: Golden dataset çalıştırıcı.
- `src/security/pii.py`: Basit PII masking.
- `src/security/guardrails.py`: Prompt injection ve data exfiltration kontrolleri.
- `tests/test_guardrails.py`: Injection ve PII testleri.

Canlı kod görevi:

- 10 satırlık golden dataset oluştur.
- Her satır için expected intent, expected risk level ve expected approval decision kontrol et.
- Eval sonucunu pass/fail ve score olarak bas.

Mülakat soruları:

1. Bir agent'ın doğru çalıştığını nasıl test edersin?
2. LLM output regression test nasıl kurulur?
3. Tool çağrısı yapmadan önce hangi validation'ları uygularsın?
4. Bankacılık ortamında guardrail tasarımın nasıl olur?
5. Evaluation dataset'i nasıl oluşturursun?

Beklenen cevap:

- Test piramidi LLM sistemlerinde de vardır: unit, integration, scenario, human eval.
- Golden dataset gerçek kullanıcı soruları, edge case, injection, ambiguous intent ve failure case içerir.
- Tool validation schema, auth, policy, idempotency ve risk approval kontrol eder.
- Guardrail tek katman değildir; input, retrieval, model output ve tool execution katmanlarında uygulanır.

DoD:

- Eval script deterministik modda çalışır.
- Guardrail testleri geçer.
- PII log'a ham düşmez.

## Aşama 11 - Security, Compliance ve Banking Context

Amaç: Bankacılık ortamında autonomous AI risklerini doğru yönetmek.

Konular:

- PII masking.
- Data minimization.
- Access control.
- Audit trail.
- Encryption at rest/in transit.
- Prompt injection.
- Data exfiltration.
- Tool permission boundaries.
- Human approval.
- Least privilege.
- Compliance-aware logging.

Yazılacak kod:

- `src/security/pii.py`: IBAN, email, phone benzeri örnek PII maskesi.
- `src/security/audit.py`: Audit event builder.
- `src/agents/policies.py`: Role/action matrix.
- `tests/test_security_policy.py`: Yetkisiz tool çağrısı engelleme.

Canlı kod görevi:

- Kullanıcı mesajı PII içeriyorsa log'a maskeli yaz.
- `transfer_money` gibi high-risk tool için human approval zorunlu yap.
- `knowledge_search` gibi low-risk tool için read-only çalıştır.

Mülakat soruları:

1. Agent'ın hassas müşteri verisini sızdırmasını nasıl engellersin?
2. Tool access authorization nasıl tasarlanır?
3. Her tool call için audit log'da ne tutarsın?
4. PII içeren prompt'ları nasıl yönetirsin?
5. Bankacılık ortamında autonomous agent'a hangi limitleri koyarsın?

Beklenen cevap:

- Least privilege, allowlisted tools, approval gates, masking, encryption ve audit trail gerekir.
- Agent tool seçebilir ama tool çalıştırma izni policy engine tarafından verilir.
- Audit log actor, tenant, action, args summary, approval id, result, timestamp, trace id ve risk level tutar.
- PII mümkünse prompt'a hiç girmez; gerekiyorsa minimize/mask edilir.

Kırmızı bayraklar:

- "Model zaten güvenli cevap verir" demek.
- Tüm tool'ları modele açık bırakmak.
- Audit log'a ham müşteri verisi yazmak.

Güçlü sinyaller:

- Policy as code.
- Human approval for irreversible actions.
- Data minimization.
- Defense in depth.

## Aşama 12 - AWS Production Architecture

Amaç: Local çalışan AI sistemini production mimariye taşıyabilmek.

Konular:

- ECS/EKS/Lambda.
- API Gateway veya ALB.
- RDS PostgreSQL.
- Secrets Manager.
- S3.
- CloudWatch.
- IAM.
- VPC.
- Autoscaling.
- CI/CD.
- Blue-green deployment.
- Cost monitoring.
- Model API egress control.

Yazılacak çıktı:

- `docs/aws_architecture.md`: Mimari tasarım.
- `Dockerfile`: FastAPI servisi container.
- `docker-compose.yml`: Local Postgres + API.
- Opsiyonel GitHub Actions workflow taslağı.

Canlı kod görevi:

- FastAPI uygulamasını Dockerfile ile paketle.
- Healthcheck ekle.
- Environment variable ile provider, model ve database config yönet.

Mülakat soruları:

1. Bu AI agent sistemini AWS üzerinde nasıl deploy edersin?
2. FastAPI servisini ECS üzerinde nasıl çalıştırırsın?
3. Secrets ve API key yönetimini nasıl yaparsın?
4. CloudWatch'ta hangi metrikleri takip edersin?
5. Production incident olduğunda nasıl rollback yaparsın?

Beklenen cevap:

- Public endpoint API Gateway/ALB arkasında çalışır.
- FastAPI container ECS Fargate veya EKS üzerinde koşabilir.
- RDS private subnet'te, Secrets Manager ile secret yönetimi yapılır.
- CloudWatch logs/metrics, tracing ve alarms gerekir.
- Blue-green veya canary deployment ile risk azaltılır.
- Model API egress, network policy ve cost alert ile kontrol edilir.

DoD:

- Local Docker build başarılı.
- Healthcheck container içinde çalışır.
- Architecture dokümanı trade-off içerir.

## Aşama 13 - TypeScript Frontend ve AI UX

Amaç: Backend AI sisteminin kullanıcıya doğru şekilde sunulmasını anlayabilmek. Kodların çoğu Python olacak; bu aşamada frontend sadece mülakat kapsamını tamamlamak için hafif tutulacak.

Konular:

- Streaming chat UI.
- Type-safe API client.
- Tool execution visibility.
- Intermediate agent steps.
- Error states.
- Retry UX.
- Feedback collection.
- Human approval UI.
- File upload UX.
- Trace/debug panel.

Yazılacak çıktı:

- `docs/ai_ux_notes.md`: UX kararları.
- Opsiyonel minimal TypeScript client veya API contract.
- Feedback endpoint taslağı.

Mülakat soruları:

1. Agent response streaming frontend'de nasıl gösterilir?
2. Tool call adımlarını kullanıcıya göstermeli misin?
3. Human-in-the-loop approval ekranı nasıl tasarlanır?
4. Frontend'den gelen prompt injection riskleri nasıl azaltılır?
5. Kullanıcı feedback'i evaluation pipeline'a nasıl bağlanır?

Beklenen cevap:

- Kullanıcıya gereksiz chain-of-thought değil, anlamlı işlem durumu gösterilir.
- Tool call görünürlüğü domain'e göre ayarlanır: "bilgi aranıyor", "onay bekleniyor", "işlem tamamlandı".
- High-risk aksiyonlarda açık summary, risk, confirm/cancel ve audit id gerekir.
- Frontend input'u trusted değildir; backend validation ve policy zorunludur.
- Feedback trace id ile eval dataset'e bağlanabilir.

## Aşama 14 - Full System Design Case Study

Amaç: Tüm stack'i tek bir expert seviye sistem tasarım cevabında birleştirmek.

Çalışılacak case seçenekleri:

1. Internal Banking Knowledge Assistant.
2. Agentic Data Analyst.
3. Customer Support Agent.
4. Multi-Agent Workflow.

Önerilen ana case: `Internal Banking Knowledge Assistant + Actionable Support Agent`

Mimari bileşenler:

- FastAPI backend.
- PostgreSQL + pgvector.
- RAG ingestion pipeline.
- LLM provider adapter.
- LangGraph-style workflow.
- Tool permission policy.
- Human approval.
- Audit log.
- Evaluation pipeline.
- Observability dashboard.
- AWS deployment.

Canlı kod görevi:

- Daha önce yazılan modülleri birleştir.
- Kullanıcı sorusu al.
- Intent classify et.
- Retrieval yap.
- Tool gerekiyorsa policy check yap.
- Cevabı structured output ile döndür.
- Trace summary üret.

Mülakat soruları:

1. Kurum çalışanları için internal banking knowledge assistant tasarlasaydın uçtan uca nasıl kurardın?
2. Bu sistemde en kritik failure mode'lar nelerdir?
3. İlk MVP'de neyi dahil eder, neyi sonraya bırakırsın?
4. Production readiness checklist'in ne olur?
5. Business impact'i nasıl ölçersin?

Beklenen cevap iskeleti:

1. Problem ve kullanıcı: Çalışanların policy/procedure sorularına hızlı, kaynaklı cevap.
2. Data: Doküman ingestion, metadata, access control.
3. Retrieval: Hybrid search, reranking, citations.
4. Agent: Deterministic routing + guarded tool execution.
5. Backend: FastAPI, async, retries, rate limits.
6. Storage: PostgreSQL, pgvector, audit logs.
7. Security: PII masking, RBAC, tenant isolation, approval.
8. Evaluation: Golden set, human review, regression.
9. Observability: Trace, cost, latency, error taxonomy.
10. Deployment: AWS ECS/RDS/Secrets/CloudWatch/CI-CD.
11. Impact: Resolution time, deflection rate, accuracy, adoption, cost per interaction.

Kırmızı bayraklar:

- Sistemi sadece "prompt + vector DB" diye anlatmak.
- Access control ve audit'i unutmak.
- Evaluation'sız production'a çıkmak.
- Business metriği söylememek.

Güçlü sinyaller:

- MVP scope.
- Failure mode listesi.
- Security-first design.
- Traceability.
- Cost and latency trade-off.
- Rollback ve incident response.

## Aşama 15 - Behavioral ve Technical Leadership

Amaç: Expert seviyede sadece kod değil, takım etkisi ve teknik karar alma gücünü göstermek.

Konular:

- Cross-functional çalışma.
- Engineers ile production'a alma.
- Trade-off anlatma.
- Teknik karar savunma.
- Knowledge sharing.
- AI craftsmanship.
- Incident ownership.
- Ambiguity management.

Hazırlanacak hikayeler:

1. Belirsiz business ihtiyacını teknik plana çevirdiğin bir örnek.
2. PoC'yi production'a taşırken yaptığın hardening adımları.
3. Takımı ikna ettiğin veya teknik yönlendirme yaptığın bir durum.
4. Hata/incident sonrası aldığın aksiyonlar.
5. Ölçülebilir business impact ürettiğin proje.

STAR + Technical Depth formatı:

```text
Situation: Problem ve bağlam.
Task: Senden beklenen.
Action: Teknik ve iletişim aksiyonların.
Result: Ölçülebilir sonuç.
Technical depth: Architecture, trade-off, failure mode, monitoring.
Reflection: Bugün olsa neyi iyileştirirdin?
```

Mülakat soruları:

1. Business beklentisi gerçekçi değilse nasıl yönetirsin?
2. Junior engineer riskli agent tasarımı önerirse nasıl yönlendirirsin?
3. PoC'yi production sistemine çevirmek için hangi adımları uygularsın?
4. AI çözümünün business impact'ini nasıl ölçersin?
5. Bir model/agent incident'ında ownership'i nasıl alırsın?

Beklenen cevap:

- Empati + teknik netlik.
- Trade-off'ları business diliyle anlatma.
- Küçük MVP, net ölçüm, güvenli rollout.
- Blameless postmortem ve kalıcı aksiyon.

## Aşama 16 - Final Mülakat Simülasyonu

Amaç: Gerçek mülakat provası.

Simülasyon sırası:

| Sıra | Alan | Zorluk |
| --- | --- | --- |
| 1 | Python + FastAPI | Orta |
| 2 | LangChain temelleri | Orta |
| 3 | LangGraph agent workflow | Zor |
| 4 | GPT-4o tool calling + structured output | Zor |
| 5 | RAG + memory | Zor |
| 6 | PostgreSQL + pgvector + schema design | Orta-zor |
| 7 | AWS production architecture | Zor |
| 8 | Observability + debugging | Zor |
| 9 | Evaluation + guardrails | Zor |
| 10 | Full system design case | Expert |
| 11 | Behavioral + leadership | Expert |

Final prova formatı:

- 10 dakika: Kendini role göre tanıtma.
- 20 dakika: Python/FastAPI canlı kod.
- 20 dakika: Agent workflow canlı kod.
- 20 dakika: RAG/evaluation soruları.
- 30 dakika: Full system design.
- 15 dakika: Behavioral leadership.
- 10 dakika: Senin soruların.

Başarı kriterleri:

- Kod çalışıyor.
- Hatalar kontrollü.
- Test var.
- Tasarımda security, observability, cost ve business impact var.
- Cevaplar framework ezberi değil, production engineering düşüncesi gösteriyor.

## İlk Kod Oturumu İçin Net Başlangıç

Bir sonraki adımda `Aşama 0` ve `Aşama 1` ile başlamalıyız.

İlk oturumda yazılacaklar:

1. `requirements.txt`
2. `.env`
3. `README.md`
4. `src/common/config.py`
5. `src/common/logging.py`
6. `src/llm/base.py`
7. `src/llm/mock_client.py`
8. `tests/test_mock_llm.py`

İlk canlı mülakat sorusu:

> "FastAPI ile LLM tabanlı bir endpoint tasarlayacaksın. Ancak API anahtarı olmadan test edilebilir, production'da ise gerçek provider'a bağlanabilir olmasını istiyorum. Bunu Python'da nasıl tasarlarsın?"

İdeal yaklaşım:

- `LLMClient` interface.
- `MockLLMClient` test adapter.
- `OpenAIClient` production adapter.
- Pydantic request/response.
- Timeout/retry.
- Structured logging.
- Dependency injection.
- Unit tests.

Bu cevap ve kod, rolün "strong Python skills", "production-ready code", "LLM fundamentals", "agentic workflows" ve "robust reliable systems" beklentilerini aynı anda gösterir.
