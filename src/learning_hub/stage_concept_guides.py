"""Her aşama için Özet sekmesinde gösterilecek kavram rehberleri."""

from src.learning_hub.models import ConceptGuide

STAGE_CONCEPT_GUIDES: dict[int, ConceptGuide] = {
    0: {
        "title": "Production Omurga (Config, Logging, Healthcheck)",
        "definition": (
            "Production omurga, bir AI servisinin LLM katmanından bağımsız çalışan temel altyapı "
            "bileşenleridir: konfigürasyon yönetimi, yapılandırılmış loglama ve sağlık kontrolü. "
            "Bu katman, uygulamanın hangi ortamda çalıştığını, hangi ayarlarla başladığını ve "
            "dış bağımlılıkların erişilebilir olup olmadığını deterministik biçimde bildirir. "
            "PoC kodundan production servise geçişte ilk kurulması gereken iskelet burasıdır; "
            "model yanıt vermese bile operasyon ekibi sistemin durumunu ölçebilir."
        ),
        "purpose": (
            "Dağınık ortam değişkenleri, okunamaz loglar ve 'servis ayakta mı?' sorusuna net cevap "
            "verememe durumunu çözer. Konfigürasyon tek kaynaktan yönetildiğinde staging ile production "
            "arasında sürpriz farklar azalır. Yapılandırılmış loglama, hata ayıklama ve incident "
            "response sürecini hızlandırır; correlation id ile tek bir kullanıcı isteği uçtan uca "
            "izlenebilir. Healthcheck endpoint'i load balancer, Docker HEALTHCHECK ve deploy smoke "
            "testlerinin ortak dilidir."
        ),
        "how_it_works": (
            "Uygulama başlarken Pydantic Settings `.env` dosyasını okur ve tip güvenli bir `Settings` "
            "nesnesi üretir; eksik veya hatalı değerler erken aşamada yakalanır. Her HTTP isteğinde "
            "middleware bir correlation id atar veya istemciden geleni devralır; tüm log satırları "
            "JSON formatında bu id ile yazılır. LLM çağrıları, tool execution ve audit kayıtları aynı "
            "trace bağlamına bağlanabilir. `GET /health` endpoint'i uygulama durumunu, seçili LLM "
            "provider'ını ve veritabanı bağlantısını özetler; deploy sonrası ilk kontrol buradan yapılır."
        ),
        "core_logic": (
            "Konfigürasyon → loglama → sağlık kontrolü üçlüsü LLM'den bağımsız bir omurgadır ve "
            "mülakatta 'önce omurga, sonra model' cümlesi buradan gelir. LLM yanıt vermese bile servis "
            "ayakta mı, hangi ortamda çalışıyor, hangi provider seçili — bunlar deterministik olarak "
            "bilinmelidir. Healthcheck sadece '200 döndü' demek değildir; DB ve provider durumunu "
            "ayrıştırmak operasyonel teşhisi kolaylaştırır."
        ),
        "in_this_project": (
            "`src/common/config.py` mock/openai seçimini ve tüm ortam değişkenlerini yönetir. "
            "`src/common/logging.py` JSON structured logging ve correlation id taşımayı sağlar. "
            "`src/common/health.py` uygulama, provider ve DB durumunu birleştirir; `GET /health` "
            "deploy smoke test ve Docker HEALTHCHECK için kullanılır. API key olmadan mock modda "
            "tüm testler bu omurga üzerinde koşar; `.env` dosyası tek konfigürasyon kaynağıdır."
        ),
    },
    1: {
        "title": "LLM Client Abstraction",
        "definition": (
            "LLM Client abstraction, farklı dil modeli sağlayıcılarına (OpenAI, mock, fallback) "
            "tek bir arayüz üzerinden erişmeyi sağlayan tasarım desenidir. `Protocol` veya abstract "
            "base class ile `complete()` ve `stream()` gibi standart metotlar tanımlanır; somut "
            "implementasyonlar bu sözleşmeye uyar. Factory pattern ayarlara göre doğru client'ı "
            "seçer. Bu sayede domain kodu belirli bir API'ye değil, soyut arayüze bağımlı kalır."
        ),
        "purpose": (
            "Doğrudan OpenAI SDK'sına bağımlı kod test edilemez, provider değişimi pahalı ve "
            "retry/timeout mantığı her yerde tekrarlanır. Abstraction katmanı CI'da mock client "
            "kullanarak gerçek API maliyeti olmadan deterministik test sağlar. Timeout, exponential "
            "backoff ve transient hata yönetimi merkezi bir serviste toplanır. Production'da "
            "primary provider fail olunca fallback'e geçiş bu katmandan yönetilir."
        ),
        "how_it_works": (
            "`LLMClient` Protocol `complete()` ve `stream()` metotlarını tanımlar; dönüş tipleri "
            "projede standartlaştırılmıştır. `create_llm_client()` factory fonksiyonu `.env`'deki "
            "`LLM_PROVIDER` değerine göre `MockLLMClient` veya `OpenAIClient` döner. "
            "`generate_chat_response()` servis katmanı timeout ve exponential retry uygular; "
            "geçici hatalarda (timeout, 5xx) tekrar dener, validation veya authorization "
            "hatalarında retry yapmaz. Tüm agent, RAG ve classify modülleri bu servis üzerinden "
            "LLM'e erişir; doğrudan SDK çağrısı yapılmaz."
        ),
        "core_logic": (
            "Dependency inversion: domain kodu somut API'ye değil interface'e bağlanır — mülakatta "
            "en sık sorulan trade-off budur. Retry yalnızca geçici hatalarda anlamlıdır; aynı "
            "prompt'u validation hatasında tekrar göndermek maliyet ve gürültü üretir. Mock client "
            "deterministik yanıt vererek CI'da gerçek API'ye ihtiyaç bırakmaz; offline geliştirme "
            "mümkün olur."
        ),
        "in_this_project": (
            "`src/llm/base.py` `LLMClient` Protocol tanımını içerir. `src/llm/mock_client.py` "
            "classification, SQL üretimi ve chat senaryolarını simüle eder. `src/llm/factory.py` "
            "içindeki `create_llm_client()` `.env`'deki `LLM_PROVIDER` ile seçim yapar. "
            "`src/llm/service.py` timeout + retry mantığını uygular; `src/common/retry.py` "
            "exponential backoff sağlar. Tüm üst katmanlar `generate_chat_response()` üzerinden LLM'e gider."
        ),
    },
    2: {
        "title": "FastAPI",
        "definition": (
            "FastAPI, Python'da modern, yüksek performanslı REST API geliştirmek için kullanılan "
            "bir web framework'üdür. Pydantic ile otomatik request/response validation, OpenAPI "
            "şema üretimi ve async desteği sunar. Router, dependency injection ve middleware "
            "mekanizmaları ile production servis davranışını (hata formatı, streaming, metrik) "
            "standartlaştırır. Agent sistemlerinde LLM mantığı ile HTTP katmanı ayrı tutulmalıdır."
        ),
        "purpose": (
            "Agent ve LLM iş mantığını dış dünyaya güvenli, tutarlı bir REST arayüzü ile açar. "
            "Request validation sayesinde bozuk body'ler LLM'e ulaşmadan 422 ile reddedilir. "
            "Streaming (SSE), sync chat ve workflow endpoint'leri aynı servis altında birleşir. "
            "Exception handler'lar ve middleware correlation id, HTTP metrikleri ve güvenlik "
            "header'larını merkezi yönetir."
        ),
        "how_it_works": (
            "FastAPI router'lar endpoint tanımlar; Pydantic modeller body ve query parametrelerini "
            "validate eder. `Depends()` ile dependency injection sağlanır; testte `get_llm_client` "
            "override edilebilir. Chat endpoint sync veya SSE streaming modunda çalışabilir; "
            "workflow endpoint checkpoint durumunda `run_id` ile resume kabul eder. "
            "Exception handler'lar 422, 403, 504 gibi standart HTTP kodları döner. Middleware "
            "correlation id atar ve HTTP istek metriklerini toplar."
        ),
        "core_logic": (
            "API katmanı ince tutulur: iş mantığı router'da değil, service/agent katmanında kalır. "
            "Depends(get_llm_client) ile dependency injection testte override edilebilir — bu "
            "integration test stratejisinin temelidir. Streaming için SSE çoğu chat UI için "
            "yeterlidir; çift yönlü etkileşim gerekiyorsa WebSocket düşünülür."
        ),
        "in_this_project": (
            "`src/api/main.py` uygulama giriş noktasıdır; router'lar burada mount edilir. "
            "`POST /v1/chat` mock veya OpenAI ile konuşur; `POST /v1/workflow/run` tam agent "
            "akışını tetikler. `POST /v1/classify`, `POST /v1/rag/query`, `POST /v1/analyst/query` "
            "her modülü ayrı test edilebilir kılar. Demo UI (`/ui/`) bu endpoint'leri tarayıcıdan "
            "çağırır; `src/api/exception_handlers.py` hata formatını standartlaştırır."
        ),
    },
    3: {
        "title": "Structured Output / LangChain Kavramları",
        "definition": (
            "Structured output, LLM'in serbest metin yerine belirli bir JSON şemasına uyan "
            "yapılandırılmış veri üretmesini ifade eder. LangChain kavramları (chain, parser, "
            "callback) bu projede framework bağımsız uygulanır: chain deterministik işlem hattı, "
            "parser Pydantic validation, callback ise gözlemlenebilirlik sağlar. "
            "Contract-first yaklaşımda önce schema tanımlanır, sonra prompt yazılır."
        ),
        "purpose": (
            "Serbest metin LLM çıktısı downstream kodda parse edilemez ve hata oranı yüksektir. "
            "Intent classification, risk skoru ve approval flag gibi alanlar typed JSON olarak "
            "gerekir. Parse hatasında repair loop bozuk çıktıyı düzeltme şansı verir. "
            "Callback handler chain/LLM/parse olaylarını loglayarak LangSmith benzeri "
            "gözlemlenebilirlik sağlar."
        ),
        "how_it_works": (
            "Prompt'ta JSON schema açıkça istenir; LLM metin üretir. `parse_structured_output()` "
            "Pydantic model ile çıktıyı validate eder; schema dışı alanlar reddedilir. "
            "Parse hatasında repair loop devreye girer: bozuk JSON tekrar LLM'e düzeltilmesi "
            "için gönderilir. Callback handler classify, LLM çağrısı ve parse adımlarını "
            "loglar. Input guardrail injection tespit ederse classify chain'e girmeden bloklar."
        ),
        "core_logic": (
            "Chain = deterministik işlem hattı; LLM sadece bir adım, tüm akış ona bağımlı değildir. "
            "Tool authorization ve audit framework dışında domain katmanında kalır. "
            "Contract-first: önce schema, sonra prompt; çıktı schema'ya uymak zorundadır — "
            "mülakatta 'JSON mode yeterli mi?' sorusunun cevabı: validation katmanı şarttır."
        ),
        "in_this_project": (
            "`src/llm/structured_output.py` parse ve repair mantığını içerir. "
            "`src/agents/classifier.py` içindeki `classify_customer_message()` intent/risk/approval "
            "JSON üretir — workflow'un ilk node'udur. `src/security/input_guardrails.py` injection'ı "
            "classify'a girmeden bloklar. `src/agents/callbacks.py` chain olaylarını loglar; "
            "`POST /v1/classify` endpoint'i bu chain'i tek başına test eder."
        ),
    },
    4: {
        "title": "LangGraph-Style Agent Workflow",
        "definition": (
            "LangGraph-style agent workflow, çok adımlı agent akışını explicit state machine "
            "olarak yöneten bir orchestration desenidir. Her adım (node) belirli bir işlev yerine "
            "getirir; edge'ler koşullu geçişleri tanımlar. `AgentState` typed alanlarla durumu "
            "tutar; serbest metin state anti-pattern'dir. Checkpoint mekanizması onay beklerken "
            "akışı durdurur ve `run_id` ile kaldığı yerden devam ettirir."
        ),
        "purpose": (
            "Tek prompt ile karmaşık banking senaryolarını çözmek güvenilir değildir; adımlar "
            "ayrıştırılmalıdır. Policy engine tool çalıştırmadan önce ALLOW/DENY/REQUIRE_APPROVAL "
            "kararı verir; model ne seçerse seçsin son söz policy'dedir. High-risk tool (transfer) "
            "human approval olmadan çalışmaz. Idempotent tool execution retry'da aynı finansal "
            "işlemin tekrarlanmasını engeller."
        ),
        "how_it_works": (
            "Akış classify → retrieve → decide → approve → tool → answer → audit adımlarından oluşur. "
            "Her adım ayrı node olarak implement edilir; state typed dict ile taşınır. "
            "Policy engine role × tool × risk matrix uygular. Transfer gibi high-risk aksiyonda "
            "workflow `awaiting_approval` durumunda checkpoint kaydeder. Onay gelince aynı "
            "`run_id` ile resume edilir; tool execution idempotency key ile güvenli retry sağlar."
        ),
        "core_logic": (
            "Agentic kararlar deterministic guardrail'lerle sınırlandırılır — model tool seçse bile "
            "policy son sözü söyler. Checkpoint olmadan human-in-the-loop production'da "
            "uygulanamaz. State machine explicit olduğunda debug, test ve observability çok daha "
            "kolaydır; 'black box agent' anti-pattern'den kaçınılır."
        ),
        "in_this_project": (
            "`src/agents/workflow.py` içindeki `CustomerSupportWorkflow` tüm stack'in birleştiği "
            "orchestrator'dır. `src/agents/state.py` typed `AgentState` tanımlar; "
            "`src/agents/checkpoint.py` onay beklerken duraklatmayı sağlar. "
            "`POST /v1/workflow/run` E2E akışı tetikler; demo UI onay modalı ile resume yapar. "
            "Transfer senaryosu `awaiting_approval` durumunda checkpoint kaydeder. "
            "`src/agents/react_loop.py` ReAct (Reasoning+Acting) döngüsünü demo eder; "
            "Observe→Think→Act pattern'i tool_call/final_answer/escalate karar tipleriyle "
            "modellenir. Agent vs chatbot: agent çok adımlı görev tamamlar, tool kullanır; "
            "chatbot tek adımlı Q&A yapar. Memory türleri: short-term (konuşma), long-term "
            "(tercihler), episodic (geçmiş görevler), semantic (RAG corpus), tool memory "
            "(API sonuçları). Temel riskler: hallucination, tool misuse, prompt injection, "
            "infinite loop, over-autonomy. Kritik prensip: LLM karar verebilir ama yetki "
            "vermez — authorization policy engine'de kalır."
        ),
    },
    5: {
        "title": "OpenAI Adapter",
        "definition": (
            "OpenAI adapter, mock LLM client'tan gerçek OpenAI/GPT production API'sine geçişi "
            "sağlayan somut implementasyondur. Async API çağrısı, timeout, hata mapping ve "
            "model seçimi bu katmanda yapılır. FallbackLLMClient primary model fail olunca "
            "(timeout, 5xx) secondary modele geçer. Structured output için JSON mode, Pydantic "
            "validation ve repair katmanları birlikte çalışır."
        ),
        "purpose": (
            "Mock mod geliştirme ve test için yeterlidir; production kalitesi gerçek model "
            "gerektirir. Adapter katmanı OpenAI SDK detaylarını domain kodundan izole eder. "
            "Model fallback latency spike veya primary outage durumunda degrade path sunar. "
            "Her LLM çağrısı model adı, token, latency ve retry count loglanarak maliyet "
            "ve performans takibi mümkün olur."
        ),
        "how_it_works": (
            "OpenAIClient async API çağrısı yapar; timeout ve hata mapping uygular. "
            "`.env`'de `LLM_PROVIDER=openai` ve geçerli `OPENAI_API_KEY` olduğunda factory "
            "bu client'ı döner; key yoksa otomatik MockLLMClient seçilir. FallbackLLMClient "
            "primary fail olunca gpt-4o → gpt-4o-mini degrade path'ini izler. Tool calling "
            "parse katmanı function call yanıtlarını typed modele dönüştürür. "
            "Structured output JSON mode + validation + repair üçlüsüyle güvenilir çıktı üretir."
        ),
        "core_logic": (
            "Model seçimi latency, cost, reasoning ihtiyacı ve compliance'a göre yapılır — "
            "en pahalı model her zaman doğru seçim değildir. Fallback sadece model adı değiştirmek "
            "değildir; tool compatibility ve kalite kontrolü gerektirir. Her LLM çağrısı "
            "observability trace'ine yazılmalıdır; aksi halde maliyet sürprizleri kaçınılmazdır."
        ),
        "in_this_project": (
            "`src/llm/openai_client.py` gerçek OpenAI API entegrasyonunu içerir. "
            "`.env`: `LLM_PROVIDER=openai` + `OPENAI_API_KEY` ile gerçek model devreye girer; "
            "key yoksa factory otomatik MockLLMClient döner. `src/llm/fallback_client.py` "
            "gpt-4o → gpt-4o-mini degrade path'ini gösterir. `src/llm/tool_calling.py` "
            "function call parse mantığını sağlar; testler ve demo offline çalışabilir."
        ),
    },
    6: {
        "title": "RAG (Retrieval-Augmented Generation)",
        "definition": (
            "RAG (Retrieval-Augmented Generation), dil modelinin yanıt üretmeden önce harici "
            "bilgi kaynağından ilgili doküman parçalarını getirip prompt'a eklediği bir "
            "mimari yaklaşımdır. 'Retrieval' aşaması kullanıcı sorusuna en uygun chunk'ları "
            "bulur; 'Augmented' aşaması bu chunk'ları LLM context'ine enjekte eder; "
            "'Generation' aşaması model yalnızca bu bağlama dayanarak cevap üretir. "
            "Model tüm kurumsal bilgiyi ezberlemez; ihtiyaç anında güncel ve kaynaklı bilgi çeker."
        ),
        "purpose": (
            "LLM'in eğitim verisi dışında kalan kurumsal policy, prosedür ve ürün bilgisine "
            "erişmesini sağlar. Hallucination riskini azaltır; model 'bilmiyorum' demek yerine "
            "ilgili doküman parçalarını getirip kaynak gösterebilir. Bilgi tabanı güncellendiğinde "
            "modeli yeniden eğitmeye gerek kalmaz; sadece index yenilenir. "
            "Bankacılık gibi regulated ortamlarda cevabın hangi policy'ye dayandığını göstermek kritiktir."
        ),
        "how_it_works": (
            "Dokümanlar parçalara (chunk) bölünür; her chunk embedding vektörüne dönüştürülür. "
            "Kullanıcı sorusu embed edilir ve vector search en benzer chunk'ları bulur. "
            "Hybrid search keyword skorunu da ekleyerek semantik + lexical eşleşmeyi birleştirir. "
            "Bulunan chunk'lar prompt'a context olarak verilir; LLM yalnızca bu context'e "
            "dayanarak cevap üretir ve kaynak id'lerini döner. Kötü retrieval kötü cevap demektir; "
            "bu yüzden precision@k gibi metriklerle eval şarttır."
        ),
        "core_logic": (
            "Retrieval ve generation ayrı aşamalardır — model tüm bilgiyi ezberlemez, ihtiyaç "
            "anında getirir. Conversation memory (diyalog geçmişi) ile knowledge retrieval "
            "(kurumsal KB) farklı store'larda tutulmalıdır; karıştırmak mülakat red flag'idir. "
            "Grounded answer: LLM context dışına çıkmamalı; kaynak id'leri kullanıcıya gösterilmelidir."
        ),
        "in_this_project": (
            "`src/rag/documents.py` içindeki `default_banking_documents()` örnek bankacılık policy "
            "corpus'u sağlar (FAST/EFT dahil). `src/rag/preparation.py` clean→normalize→chunk "
            "pipeline; `KnowledgeBase.ingest()` entegrasyonu. `src/rag/retriever.py` hybrid "
            "(vector + keyword) arama. `src/rag/reranker.py` ikinci aşama sıralama. "
            "`src/rag/query_rewrite.py` acronym expansion. `src/rag/pipeline.py` end-to-end "
            "RAG + opsiyonel judge eval — `POST /v1/rag/pipeline`. `src/rag/evaluation.py` "
            "precision@k, recall@k, MRR, NDCG, Hit Rate@k — `GET /v1/rag/eval`. "
            "Retrieval ve generation eval ayrı katmanlarda ölçülür."
        ),
    },
    7: {
        "title": "PostgreSQL / Veri Katmanı",
        "definition": (
            "Veri katmanı, AI uygulamasının kalıcı state'ini yöneten persistence katmanıdır. "
            "Conversation history, tool call logları, audit kayıtları ve idempotency cache "
            "burada saklanır. SQLAlchemy ORM tabloları tanımlar; repository pattern CRUD "
            "işlemlerini soyutlar. Local geliştirmede SQLite, production'da PostgreSQL (+ "
            "opsiyonel pgvector) kullanılır."
        ),
        "purpose": (
            "LLM stateless'tır; diyalog geçmişi, tool sonuçları ve audit trail kalıcı depolama "
            "gerektirir. Idempotency ile retry-safe finansal işlem garantisi verilir — aynı "
            "idempotency_key ile gelen çağrı tekrar çalıştırılmaz. Audit log compliance için "
            "PII maskelenmiş özet içerir. Multi-tenant güvenlik için tenant_id her sorguda "
            "filtre olarak zorunlu tutulur."
        ),
        "how_it_works": (
            "SQLAlchemy ORM conversations, messages, tool_calls, audit_logs tablolarını modeller. "
            "Repository pattern CRUD işlemlerini soyutlar; workflow API her mesajı DB'ye yazar. "
            "ToolExecutionService aynı `idempotency_key` ile gelen çağrıyı tekrar çalıştırmaz — "
            "cache'lenmiş sonucu döner. Audit log'a PII maskelenmiş özet yazılır. "
            "`schema.sql` production DDL taslağıdır; bootstrap script örnek veri yükler."
        ),
        "core_logic": (
            "AI uygulamasında veri katmanı LLM'den bağımsızdır — tek JSON blob anti-pattern'dir. "
            "Tool call, message ve audit ayrı modellenmelidir. Read-only DB role text-to-SQL "
            "için son savunma hattıdır. SQLite local, PostgreSQL production; migration stratejisi "
            "mülakatta sık sorulur."
        ),
        "in_this_project": (
            "Local'de SQLite (`DATABASE_URL=sqlite:///./data/app.db`); prod'da PostgreSQL + "
            "opsiyonel pgvector. `src/data/schema.sql` production DDL taslağıdır. "
            "`src/data/database.py` bağlantı yönetimi; `src/data/repositories.py` CRUD soyutlaması. "
            "`src/data/tool_execution.py` idempotency ile güvenli retry sağlar. Workflow API her "
            "mesajı DB'ye yazar; transfer tool idempotency ile korunur."
        ),
    },
    8: {
        "title": "Agentic Data Analyst / Text-to-SQL",
        "definition": (
            "Agentic data analyst, doğal dil sorularını güvenli read-only SQL'e çevirip sonucu "
            "analiz eden bir AI pipeline'ıdır. Text-to-SQL agent'ının production riskleri "
            "(SQL injection, cross-tenant leak, destructive query) katmanlı guardrail ile "
            "kontrol altına alınır. LLM SQL üretir ama asla kör güvenilmez; validation, "
            "correctness check ve DB read-only role son savunma hattıdır."
        ),
        "purpose": (
            "İş kullanıcılarının SQL bilmeden veri analizi yapmasını sağlar. "
            "Guardrail forbidden keyword, SELECT-only ve tenant filter kontrolü uygular. "
            "Correctness katmanı intent ile SQL semantiğini karşılaştırır; hatalı SQL "
            "regenerate/repair loop'a girer. Query transparency: kullanıcıya üretilen SQL "
            "ve confidence gösterilir — yanlış aggregation yanlış business kararı demektir."
        ),
        "how_it_works": (
            "LLM sorudan SQL üretir; `validate_sql()` DROP/DELETE/cross-tenant engeller. "
            "Guardrail forbidden keyword, SELECT-only, tenant filter kontrol eder. "
            "Correctness katmanı intent ile SQL semantiğini karşılaştırır. "
            "Hatalı SQL regenerate/repair loop'a girer; onay gerekiyorsa akış durur. "
            "Güvenli SELECT çalıştırılır; confidence ve query kullanıcıya gösterilir. "
            "Golden dataset eval gerçek business sorularını regression'da tutar."
        ),
        "core_logic": (
            "LLM'in ürettiği SQL'e asla kör güvenilmez — DB read-only role son savunma hattıdır. "
            "Allowlist + AST benzeri kontrol + row limit + timeout katmanlı savunma sağlar. "
            "Cross-tenant leak en kritik güvenlik açığıdır; tenant_id her sorguda zorunlu olmalıdır."
        ),
        "in_this_project": (
            "`src/agents/data_analyst.py` içindeki `run_data_analyst()` NL→SQL pipeline'ının "
            "giriş noktasıdır. `src/security/guardrails.py` içindeki `validate_sql()` "
            "DROP/DELETE/cross-tenant engeller. `src/security/sql_correctness.py` intent-SQL "
            "uyumunu kontrol eder. `POST /v1/analyst/query` tenant_id ile scoped analiz yapar; "
            "`GET /v1/analyst/eval` golden dataset regression koşar."
        ),
    },
    9: {
        "title": "Observability (Gözlemlenebilirlik)",
        "definition": (
            "Observability, deterministik olmayan LLM/agent davranışını production'da izlenebilir "
            "kılan trace, metric ve log altyapısıdır. TraceSession her agent run için span "
            "timeline oluşturur: classify, retrieval, LLM, tool, audit. MetricsCollector HTTP, "
            "LLM ve workflow counter/latency istatistikleri tutar. Root cause analysis ve maliyet "
            "takibi bu veriye dayanır."
        ),
        "purpose": (
            "LLM latency spike veya tool failure durumunda hangi span yavaş olduğunu bulmak "
            "gerekir; latency breakdown olmadan optimizasyon yapılamaz. Prompt version trace'e "
            "yazılır; eval regression ile birlikte prompt değişikliği etkisi ölçülür. "
            "Tool failure ile model failure span kind ile ayrılır. "
            "Trace replay geçmiş run'ları incident sonrası inceler."
        ),
        "how_it_works": (
            "Workflow her adımda `trace.span()` açar; span'ler nested timeline oluşturur. "
            "Her LLM çağrısı model, token, latency, retry count loglanır. "
            "MetricsCollector HTTP istek sayısı, LLM latency histogram ve workflow counter tutar. "
            "Response'ta `trace_id` ve `trace_summary` döner; demo UI trace paneli bunu gösterir. "
            "Trace store in-memory veya persistent olarak replay destekler."
        ),
        "core_logic": (
            "Latency breakdown olmadan optimizasyon yapılmaz — hangi span yavaş, önce o bulunur. "
            "Cost estimate trace summary'de olmalıdır; token sayısı × model fiyatı. "
            "Observability afterthought değil; workflow tasarımının parçasıdır."
        ),
        "in_this_project": (
            "`src/observability/traces.py` TraceSession ve span yönetimini sağlar. "
            "`src/observability/metrics.py` HTTP ve LLM metriklerini toplar. Workflow response'ta "
            "`trace_id` ve `trace_summary` döner. `GET /v1/observability/traces/{id}` timeline "
            "replay; `GET /v1/observability/metrics` dashboard snapshot. Demo UI trace paneli "
            "bu veriyi gösterir."
        ),
    },
    10: {
        "title": "Evaluation & Guardrails",
        "definition": (
            "Evaluation & guardrails, LLM sistemini ölçmeden production'a almamayı garanti eden "
            "kalite ve güvenlik katmanıdır. Golden dataset regression deterministik eval sağlar; "
            "input guardrail prompt injection ve data exfiltration pattern'lerini bloklar. "
            "PII maskesi email, phone, IBAN'ı log ve feedback'ten temizler. "
            "Eval runner pass/fail score üretir; CI gate olarak kullanılabilir."
        ),
        "purpose": (
            "Prompt değişikliği sessiz regression yaratabilir; golden dataset bunu yakalar. "
            "Guardrail tek katman değildir; input, retrieval, output ve tool execution'da "
            "uygulanır. Test piramidi LLM'de de geçerlidir: unit → integration → scenario → human eval. "
            "Regression olmadan prompt değişikliği production'a çıkmamalıdır."
        ),
        "how_it_works": (
            "Golden JSONL: input → expected intent/risk/approval; mock LLM ile deterministik eval koşar. "
            "Input guardrail classify ve workflow'un ilk satırında injection'ı bloklar. "
            "PII maskesi write-time'da uygulanır; ham PII log'a düşmez. "
            "`python -m src.evals.run_evals` classification + analyst eval çalıştırır. "
            "Eval runner pass/fail score üretir; CI pipeline gate olarak kullanılabilir."
        ),
        "core_logic": (
            "Mock LLM ile eval deterministik olmalıdır; gerçek API eval CI'da pahalı ve flaky'dir. "
            "Golden dataset gerçek business senaryolarını kapsamalıdır — sadece happy path yetmez. "
            "Guardrail false positive/negative trade-off'u mülakatta tartışılır."
        ),
        "in_this_project": (
            "`python -m src.evals.run_evals` classification + analyst + judge eval çalıştırır. "
            "`GET /v1/evals/run` API üzerinden tüm eval suite'leri tetiklenir. "
            "`GET /v1/evals/judge` RAG cevap kalitesi rubric eval. "
            "`src/evals/judge.py` groundedness/correctness/completeness/safety skorları; "
            "pointwise ve pairwise modları. Groundedness ≠ correctness: context desteği vs "
            "gerçek dünya doğruluğu. Structured assertion primary; LLM-as-a-Judge supplementary "
            "hybrid yaklaşım — judge-only red flag. "
            "`src/security/input_guardrails.py` injection tespiti yapar. "
            "`src/security/pii.py` mask_pii write-time'da uygular."
        ),
    },
    11: {
        "title": "Security & Compliance",
        "definition": (
            "Security & compliance, bankacılık ortamında autonomous AI risklerini yöneten "
            "policy, audit ve access control katmanıdır. Policy engine role × tool × risk "
            "matrix uygular; LLM authorization yapmaz, sadece öneri üretir. "
            "ComplianceAuditEvent data minimization ile audit kaydı üretir. "
            "Defense in depth: least privilege, allowlisted tools, approval gates ve audit trail "
            "birlikte çalışır."
        ),
        "purpose": (
            "Agent'ın hassas veri sızdırmasını ve yetkisiz tool çalıştırmasını engeller. "
            "Customer sadece read-only tool kullanabilir; transfer için support/admin + approval "
            "gerekir. PII log'a ham düşmez; mask_pii write-time'da uygulanır. "
            "Audit trail compliance denetimlerinde kanıt sağlar."
        ),
        "how_it_works": (
            "Policy engine her tool execution öncesi `can_execute_tool()` çağrılır. "
            "Role × tool × risk matrix ALLOW/DENY/REQUIRE_APPROVAL döner. "
            "High-risk transfer senaryosu onay olmadan `AWAITING_APPROVAL`'da kalır. "
            "`build_policy_audit_event()` compliance formatında audit yazar. "
            "`GET /v1/security/audit/recent` son kayıtları listeler."
        ),
        "core_logic": (
            "Defense in depth: model güvenli cevap verir demek yetmez. "
            "Agent tool seçebilir ama çalıştırma izni policy engine verir — LLM authorization yapmaz. "
            "Human-in-the-loop high-risk aksiyonlar için zorunludur; checkpoint olmadan production'a çıkılmaz."
        ),
        "in_this_project": (
            "`src/agents/policies.py` içindeki `can_execute_tool()` workflow'da her tool öncesi "
            "çağrılır. `src/security/audit.py` içindeki `build_policy_audit_event()` compliance "
            "formatında audit yazar. `GET /v1/security/audit/recent` son kayıtları listeler. "
            "Transfer senaryosu onay olmadan `AWAITING_APPROVAL`'da kalır. Workflow body'deki "
            "`user_role` (customer, support_agent, admin) policy kararını etkiler."
        ),
    },
    12: {
        "title": "AWS Deploy & CI/CD",
        "definition": (
            "AWS deploy & CI/CD, local çalışan FastAPI servisini container + cloud mimarisine "
            "taşıyan otomasyon katmanıdır. Dockerfile Python slim image + uvicorn CMD + HEALTHCHECK "
            "tanımlar. Terraform ECS Fargate, RDS PostgreSQL, ALB, Secrets Manager kaynaklarını "
            "provisioning eder. GitHub Actions PR'da pytest + docker build smoke test koşar."
        ),
        "purpose": (
            "Local'de çalışan kod production ortamında da güvenilir şekilde deploy edilmelidir. "
            "CI pipeline test geçmeden image build edilmez; deploy workflow staging/production "
            "ortamlarına image push + terraform apply yapar. Secrets asla git veya image içinde "
            "olmaz — Secrets Manager veya .env (local only). Rollback planı incident response'ın "
            "parçasıdır."
        ),
        "how_it_works": (
            "Dockerfile multi-stage veya slim base ile image üretir; HEALTHCHECK `GET /health` "
            "kullanır. `docker-compose.deploy.yml` staging stack (Postgres + API) tanımlar. "
            "Terraform modülleri VPC, ECS, RDS, ALB ve Secrets Manager oluşturur. "
            "GitHub Actions workflow PR'da pytest, eval regression ve docker build smoke test "
            "koşar. Deploy script image tag + terraform apply ile staging/production'a çıkar."
        ),
        "core_logic": (
            "Public endpoint ALB/API Gateway arkasında; RDS private subnet'te olmalıdır. "
            "Blue-green/canary deployment ile rollback riski azaltılır. "
            "Infrastructure as code (Terraform) manual drift'i önler; mülakatta trade-off tartışılır."
        ),
        "in_this_project": (
            "`docker-compose.deploy.yml` staging stack (Postgres + API) tanımlar. "
            "`scripts/deploy-compose.ps1` ve `scripts/deploy-aws.ps1` deploy otomasyonu sağlar. "
            "`infra/terraform/` ECS Fargate, RDS ve ALB kaynaklarını tanımlar. "
            "`docs/aws_architecture.md` trade-off'ları anlatır. "
            "`tests/test_deploy_artifacts.py` Dockerfile ve CI yaml varlığını doğrular."
        ),
    },
    13: {
        "title": "Frontend & AI UX",
        "definition": (
            "Frontend & AI UX, backend agent sisteminin kullanıcıya doğru sunulduğu presentation "
            "katmanıdır. SSE ile token-by-token chat streaming, workflow modunda domain-friendly "
            "adım etiketleri ('Bilgi aranıyor') ve high-risk aksiyonda onay modalı sağlar. "
            "Chain-of-thought sızdırmadan anlamlı işlem durumu gösterilir. "
            "Frontend untrusted'dır; tüm validation backend'de kalır."
        ),
        "purpose": (
            "Ham tool JSON veya internal CoT kullanıcıya gösterilmez; güven ve compliance için "
            "domain label kullanılır. Onay modalı summary, risk, approval_id ve confirm/cancel "
            "sunarak human-in-the-loop UX'i tamamlar. Feedback trace_id ile eval pipeline'a "
            "bağlanır; negative case golden dataset'e eklenir. "
            "Learning Hub ve Agent Demo birleşik arayüz mülakat hazırlığını destekler."
        ),
        "how_it_works": (
            "SSE ile chat streaming: token-by-token yanıt tarayıcıda render edilir. "
            "Workflow modunda agent adımları domain-friendly etiketlerle gösterilir. "
            "High-risk aksiyonda onay modalı açılır; onay `POST /v1/workflow/run` resume "
            "tetikler. Trace paneli `trace_summary` timeline'ını görselleştirir. "
            "👍/👎 feedback `POST /v1/feedback` ile PII masked olarak kaydedilir."
        ),
        "core_logic": (
            "Frontend untrusted — tüm validation backend'de kalır. "
            "Kullanıcıya raw tool JSON veya CoT gösterilmez. "
            "Feedback loop: negative case → golden dataset → regression; UX kalitesi eval'e bağlanır."
        ),
        "in_this_project": (
            "`/ui/` Learning Hub + Agent Demo birleşik arayüzdür. "
            "`frontend/hub.js` aşama navigasyonu ve concept guide gösterimi sağlar. "
            "`frontend/demo.js` workflow, SSE chat, onay modalı, trace paneli ve feedback içerir. "
            "`POST /v1/feedback` → feedback store (PII masked). "
            "`frontend/src/client.ts` type-safe API client referansıdır; detay `docs/ai_ux_notes.md`'de."
        ),
    },
    14: {
        "title": "System Design Case Study",
        "definition": (
            "System design case study, tüm modülleri tek bir uçtan uca banking assistant "
            "senaryosunda birleştiren entegrasyon ve mülakat hazırlık aşamasıdır. "
            "Internal Banking Knowledge Assistant + Actionable Support Agent ana case'dir. "
            "Mimari, failure mode, MVP scope ve business impact anlatımı bu aşamada "
            "sentezlenir; sistem 'prompt + vector DB' değildir."
        ),
        "purpose": (
            "System design mülakatında parça parça modülleri tek hikâyede anlatmayı sağlar. "
            "E2E senaryolar policy lookup, transfer+approval ve injection block gerçek "
            "production risklerini gösterir. Production readiness checklist go/no-go "
            "kriterleri tanımlar. CLI demo ve integration test mülakat provası için "
            "canlı kanıt sunar."
        ),
        "how_it_works": (
            "Kullanıcı sorusu classify → RAG retrieve → policy check → tool (gerekirse onay) → "
            "grounded answer → audit → trace summary akışını izler. "
            "`python -m src.case_study.run_demo` üç senaryoyu CLI'da koşar. "
            "Integration test E2E regression sağlar. "
            "`docs/system_design_case_study.md` 11 bölümlük expert cevap iskeleti sunar. "
            "Production readiness checklist deploy öncesi go/no-go değerlendirmesi yapar."
        ),
        "core_logic": (
            "Sistem access control, audit, eval, observability bir pakettir — sadece RAG yetmez. "
            "MVP: workflow + guardrails + approval + eval + demo UI. "
            "Sonra: hybrid search, real ingestion pipeline, multi-agent, dashboard. "
            "Failure mode analizi mülakatın en değerli bölümüdür."
        ),
        "in_this_project": (
            "`POST /v1/workflow/run` ana E2E endpoint'tir; classify → RAG → policy → tool → "
            "audit → trace akışını tetikler. `src/case_study/bank_chatbot.py` intent routing + "
            "policy + RAG/tools deterministik referans akışı. Intent taxonomy: general_faq, "
            "balance_query, money_transfer, fraud_report. MFA transfer akışı explicit onay "
            "gerektirir. Observability: session_id, intent, retrieved_doc_ids, tool_calls, "
            "groundedness_score, escalation_flag log alanları. "
            "`python -m src.case_study.run_demo` dört senaryoyu CLI'da koşar. "
            "`docs/system_design_case_study.md` mimari ve failure mode iskeleti. "
            "`tests/test_case_study_integration.py` E2E regression."
        ),
    },
}
