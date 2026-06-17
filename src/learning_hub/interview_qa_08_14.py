"""Continuation — expanded mülakat Q&A for stages 8-14.

Extracted from stages_08_14.py with richer answer and deep_dive text.
"""

STAGE_INTERVIEW_QA_08_14: dict[int, list[dict]] = {
    8: [
        {
            "question": "Text-to-SQL agent'ı production'a alırken en büyük riskler nelerdir?",
            "answer": (
                "En büyük riskler SQL injection ve cross-tenant veri sızıntısıdır; "
                "LLM yanlışlıkla DELETE/DROP üretebilir veya tenant_id filtresini atlayabilir. "
                "Yanlış aggregation (SUM/AVG hatası) iş kararını doğrudan etkiler ve güven kaybına yol açar. "
                "Maliyet tarafında full table scan veya LIMIT'siz sorgular hem DB'yi hem LLM token bütçesini zorlar. "
                "Son olarak kullanıcı LLM'in ürettiği SQL'e körü körüne güvenirse hata tespiti geç kalır. "
                "Bu projede bu riskler guardrails + read-only DB rolü + regeneration loop ile katmanlı azaltılır."
            ),
            "deep_dive": (
                "Pipeline `src/agents/data_analyst.py` içindeki `run_data_analyst()` ile başlar; "
                "üretilen SQL önce `src/security/guardrails.py` `validate_sql()` ile SELECT-only ve tenant filtresi "
                "açısından denetlenir. Doğruluk katmanı `src/security/sql_correctness.py` `validate_sql_correctness()` "
                "ve `repair_sql()` ile intent uyumunu kontrol eder. Dışarıya `POST /v1/analyst/query` endpoint'i "
                "(`src/api/routers/analyst.py`) üzerinden erişilir; eval için `GET /v1/analyst/eval` kullanılır."
            ),
            "red_flags": ["LLM SQL direkt çalıştır"],
            "strong_signals": ["Multi-layer validation", "Read-only role"],
            "tags": ["sql", "risk"],
        },
        {
            "question": "LLM'in ürettiği SQL'i nasıl validate edersin?",
            "answer": (
                "İlk katman keyword blocklist ve SELECT-only kuralıdır; DELETE, DROP, UPDATE gibi ifadeler reddedilir. "
                "AST parse ile string manipülasyonu bypass'ları yakalanır; sadece `contains` kontrolü yeterli değildir. "
                "Her sorguda tenant_id filtresi zorunlu tutulur; cross-tenant okuma engellenir. "
                "Row LIMIT ve query timeout ile kaynak tüketimi sınırlandırılır. "
                "Staging ortamında EXPLAIN ANALYZE ile plan maliyeti ölçülür. "
                "Son savunma hattı olarak DB kullanıcısı read-only yetkide tutulur."
            ),
            "deep_dive": (
                "`validate_sql()` fonksiyonu `src/security/guardrails.py` içinde `SqlGuardrailResult` döner; "
                "tenant filtresi ve max_rows parametreleri burada uygulanır. "
                "Intent ve canonical SQL fallback `src/security/sql_correctness.py` `validate_sql_correctness()` "
                "ile kontrol edilir; başarısızlıkta `repair_sql()` regeneration loop'una girilir. "
                "`pytest tests/test_sql_guardrails.py` bu kuralların regresyonunu doğrular."
            ),
            "red_flags": ["String contains check only"],
            "strong_signals": ["AST parser", "DB permission last line"],
            "tags": ["sql", "validation"],
        },
        {
            "question": "Read-only data analyst agent için permission model nasıl olur?",
            "answer": (
                "Veritabanı tarafında dedicated read-only kullanıcı ve tenant-scoped view'lar tanımlanır. "
                "Uygulama katmanında analyst rolü RBAC ile sınırlandırılır; her sorgu tenant_id ile scope'lanır. "
                "Query timeout ve max row limit her execution'da zorunlu uygulanır. "
                "Yüksek riskli veya büyük hacimli sorgular human approval gate'inden geçer. "
                "Admin DB kullanıcısı asla agent pipeline'ına bağlanmaz; least privilege prensibi korunur. "
                "Audit log'da hangi tenant için hangi sorunun çalıştırıldığı trace_id ile ilişkilendirilir."
            ),
            "deep_dive": (
                "`run_data_analyst()` fonksiyonu `tenant_id` parametresini hem LLM prompt'una hem "
                "`validate_sql()` çağrısına geçirir. Guardrail katmanı tenant filtresi yoksa sorguyu reddeder. "
                "Lab ortamında `POST /v1/analyst/query` body'sinde `tenant_id: tenant-a` ile test edilir. "
                "Approval gerektiren senaryolar workflow approval mekanizmasıyla entegre edilebilir."
            ),
            "red_flags": ["Admin DB user"],
            "strong_signals": ["Least privilege DB role"],
            "tags": ["permissions", "sql"],
        },
        {
            "question": "Yanlış analiz sonucu business kararını etkilerse nasıl önlem alırsın?",
            "answer": (
                "Kullanıcıya sadece sayı değil, kaynak SQL ve kısa açıklama birlikte gösterilir; "
                "şeffaflık doğrulamayı mümkün kılar. "
                "Varsayımlar (hangi tablo, hangi filtre, hangi aggregation) açıkça belgelenir. "
                "Confidence skoru düşük sonuçlarda human review eşiği devreye girer. "
                "Gerçek iş sorularından oluşan golden eval seti CI'da regresyon olarak koşulur. "
                "Production'da negatif feedback trace_id ile kaydedilip eval dataset'ine geri beslenir. "
                "Yanlış karar riski yüksek domainlerde abstention (cevap vermeme) tercih edilir."
            ),
            "deep_dive": (
                "DataAnalystResult yapısı `src/agents/data_analyst.py` içinde sql, explanation ve rows alanlarını "
                "döner; frontend ve API tüketicisi sorguyu doğrudan görebilir. "
                "`GET /v1/analyst/eval` endpoint'i business sorularına karşı doğruluk skorunu ölçer. "
                "Observability katmanında trace timeline hangi regeneration adımlarının geçildiğini gösterir."
            ),
            "red_flags": ["Sadece sayı göster"],
            "strong_signals": ["Query transparency", "Eval dataset"],
            "tags": ["business", "analyst"],
        },
        {
            "question": "Agent'ın confidence değerini kullanıcıya göstermeli misin?",
            "answer": (
                "Evet, özellikle düşük confidence durumlarında kullanıcı sonucu doğrulamaya yönlendirilir. "
                "Ancak ham LLM logprob veya self-reported confidence genelde kalibre değildir ve yanıltıcı olabilir. "
                "Eval-based confidence — golden set üzerindeki geçmiş performans — daha güvenilir bir sinyaldir. "
                "UI'da confidence bar yerine 'doğrulama önerilir' gibi actionable mesaj tercih edilir. "
                "Yüksek riskli kararlar için confidence eşiğinin altında otomatik human review tetiklenir. "
                "Abstention politikası: emin olunmayan sorularda tahmin yerine açık 'bilmiyorum' yanıtı verilir."
            ),
            "deep_dive": (
                "Eval skoru `GET /v1/analyst/eval` endpoint'inden alınır ve production confidence proxy'si olarak "
                "kullanılabilir. `run_data_analyst()` içindeki regeneration loop başarısızlık sayısı dolaylı "
                "güven sinyali sağlar. Observability trace'lerinde `record_llm_call()` token ve latency metrikleri "
                "confidence kalibrasyonu için veri kaynağı oluşturur."
            ),
            "red_flags": ["%99 her zaman"],
            "strong_signals": ["Calibrated confidence", "Abstention"],
            "tags": ["confidence", "ux"],
        },
    ],
    9: [
        {
            "question": "Agent yanlış cevap verdiğinde root cause analysis nasıl yaparsın?",
            "answer": (
                "İlk adım trace_id ile oturumu replay etmektir; tek bir ID tüm pipeline'ı birleştirir. "
                "Timeline'da prompt versiyonu, retrieval edilen chunk'lar, model çıktısı ve tool argümanları sırayla incelenir. "
                "Validation ve final answer adımları karşılaştırılarak hata hangi span'de oluştu tespit edilir. "
                "Golden case ile side-by-side diff yapılır; regression mi yoksa edge case mi anlaşılır. "
                "Tahmine dayalı RCA yerine span-level kanıt toplanır. "
                "Bulgular prompt, retrieval veya policy katmanına yönelik düzeltme olarak dokümante edilir."
            ),
            "deep_dive": (
                "`GET /v1/observability/traces/{trace_id}` endpoint'i `src/api/routers/observability.py` "
                "`get_trace_summary()` ile TraceSummaryResponse döner. "
                "Trace store `src/observability/traces.py` `get_trace_store()` üzerinden persist edilir; "
                "her span'de kind, latency_ms ve metadata bulunur. "
                "Workflow çalıştırmak için `POST /v1/workflow/run` sonrası dönen trace_id ile sorgu yapılır."
            ),
            "red_flags": ["Tahmin"],
            "strong_signals": ["Replay", "Prompt versioning"],
            "tags": ["rca", "debugging"],
        },
        {
            "question": "LLM latency yüksekse nereden başlarsın?",
            "answer": (
                "Genel optimizasyon yerine span breakdown ile darboğaz bulunur: classify, retrieval, generation, tool. "
                "Her adımın p95 latency'si ayrı ayrı ölçülür; en yavaş span öncelik alır. "
                "Classification için daha küçük ve hızlı model routing uygulanabilir. "
                "Retrieval cache ve embedding batching tekrarlayan sorgularda kazanç sağlar. "
                "Generation tarafında token limiti ve streaming UX algılanan gecikmeyi düşürür. "
                "Optimizasyon öncesi baseline metrik kaydedilir; değişiklik sonrası A/B karşılaştırma yapılır."
            ),
            "deep_dive": (
                "Trace timeline `TraceSummary` içinde her span için `latency_ms` taşır; "
                "`src/observability/traces.py` `TraceSession.span()` context manager ile ölçüm yapılır. "
                "`src/llm/service.py` içinde `record_llm_call()` model bazlı latency kaydeder. "
                "`GET /v1/observability/metrics` snapshot'ında workflow ve LLM counter'ları görülebilir."
            ),
            "red_flags": ["Genel optimize et"],
            "strong_signals": ["Per-step p95", "Bottleneck first"],
            "tags": ["latency", "performance"],
        },
        {
            "question": "Tool call failure ile model reasoning failure nasıl ayrılır?",
            "answer": (
                "Trace'te span kind alanı birincil ayrım aracıdır: tool, llm, classification. "
                "Tool failure genelde external system (timeout, 4xx/5xx, auth) kaynaklıdır; model reasoning sağlam olabilir. "
                "LLM failure parse hatası, schema uyumsuzluğu veya generation timeout olarak görünür. "
                "Classification failure intent yanlış anlaşıldığında downstream tüm adımlar sapar. "
                "Error taxonomy ile her failure tipi farklı runbook'a yönlendirilir. "
                "Hepsini 'LLM hatası' diye etiketlemek kök neden analizini geciktirir."
            ),
            "deep_dive": (
                "Timeline span'leri `src/observability/traces.py` içinde kind alanıyla etiketlenir; "
                "workflow `src/agents/workflow.py` her adımda ayrı span açar. "
                "Tool span'lerinde exception metadata ve HTTP status kaydedilir. "
                "Replay için `GET /v1/observability/traces/{trace_id}` ile span sırası ve hata noktası okunur."
            ),
            "red_flags": ["Hepsi LLM hatası"],
            "strong_signals": ["Error taxonomy", "Span kinds"],
            "tags": ["debugging", "tools"],
        },
        {
            "question": "Hangi metrikleri dashboard'a koyarsın?",
            "answer": (
                "Success rate ve p95 latency her pipeline adımı için ayrı panelde gösterilir. "
                "Token cost ve interaction başına maliyet bütçe kontrolü için kritiktir. "
                "Tool failure rate, approval rate ve block rate güvenlik sağlığını yansıtır. "
                "Fallback rate model veya retrieval degradasyonunu erken haber verir. "
                "User feedback ratio (positive/negative) kalite trendini izler. "
                "Sadece uptime göstermek yeterli değildir; iş ve maliyet metrikleri birlikte takip edilir."
            ),
            "deep_dive": (
                "`src/observability/metrics.py` `MetricsCollector.snapshot()` HTTP, LLM ve workflow counter'larını "
                "toplar. `GET /v1/observability/metrics` endpoint'i bu snapshot'ı JSON olarak sunar. "
                "`record_workflow_run()` ve `record_llm_call()` `src/agents/workflow.py` ile "
                "`src/llm/service.py`'den otomatik beslenir. Production'da CloudWatch exporter ile entegre edilebilir."
            ),
            "red_flags": ["Sadece uptime"],
            "strong_signals": ["Cost per interaction", "Approval SLA"],
            "tags": ["metrics", "dashboard"],
        },
        {
            "question": "Prompt değişikliklerinin etkisini nasıl takip edersin?",
            "answer": (
                "Her trace'e prompt_version tag'i eklenir; hangi prompt ile üretildiği geriye dönük sorgulanabilir. "
                "CI pipeline'da eval regression gate'i prompt değişikliğini merge öncesi yakalar. "
                "Golden set üzerinde A/B comparison ile eski ve yeni prompt skorları karşılaştırılır. "
                "Production'da kademeli rollout (canary) ile gerçek trafikte drift izlenir. "
                "Prompt değişikliği kayıtsız bırakılırsa RCA ve rollback imkansızlaşır. "
                "Versiyon numarası environment variable veya config'den merkezi yönetilir."
            ),
            "deep_dive": (
                "`start_trace()` fonksiyonu `src/observability/traces.py` içinde `prompt_version` parametresi alır; "
                "settings'teki PROMPT_VERSION env ile senkron tutulur. "
                "Eval regression `src/evals/run_evals.py` `run_all_evals()` ile CI'da koşturulur. "
                "Trace replay `GET /v1/observability/traces/{trace_id}` ile prompt_version alanı doğrulanır."
            ),
            "red_flags": ["Prompt değişikliği kayıtsız"],
            "strong_signals": ["Versioned prompts", "Eval gate"],
            "tags": ["prompts", "eval"],
        },
    ],
    10: [
        {
            "question": "Bir agent'ın doğru çalıştığını nasıl test edersin?",
            "answer": (
                "Test piramidi LLM agent'ları için de geçerlidir: altta unit, ortada integration, üstte scenario. "
                "Unit testler parser, policy engine ve guardrail fonksiyonlarını deterministik mock ile doğrular. "
                "Integration testler workflow API endpoint'lerini uçtan uca çağırır. "
                "Scenario testler golden dataset üzerinde intent, risk ve approval beklenenlerini karşılaştırır. "
                "İnsan değerlendirmesi production sample'ın küçük bir yüzdesinde kalite güvencesi sağlar. "
                "Production monitoring (success rate, block rate, feedback) sürekli regresyon alarmı verir."
            ),
            "deep_dive": (
                "`src/evals/run_evals.py` `run_all_evals()` classification, analyst ve guardrail eval'lerini "
                "orchestrate eder. `GET /v1/evals/run` tüm eval'leri API üzerinden tetikler. "
                "`pytest tests/test_guardrails.py` input guardrail regresyonunu doğrular. "
                "Classification eval için `GET /v1/classify/eval` endpoint'i kullanılır."
            ),
            "red_flags": ["Manuel chat only"],
            "strong_signals": ["Golden regression CI", "Scenario tests"],
            "tags": ["testing", "eval"],
        },
        {
            "question": "LLM output regression test nasıl kurulur?",
            "answer": (
                "Golden JSONL dosyası input → expected intent/risk/approval eşlemesi içerir. "
                "CI'da LLM mock'lanır; deterministik cevaplarla flake'siz test sağlanır. "
                "`run_evals` pipeline skor hesaplar ve threshold altında build fail eder. "
                "Dataset versiyonlanır; her değişiklik git'te izlenebilir olmalıdır. "
                "LLM-as-judge tek başına yeterli değildir; structured assertion primary, "
                "judge supplementary hybrid yaklaşım tercih edilir. Golden dataset + mock "
                "eval CI gate; judge RAG groundedness regression için ikinci katman."
                "Production'dan anonim örnekler periyodik olarak dataset'e eklenir."
            ),
            "deep_dive": (
                "Golden dataset `classification_golden_dataset.jsonl` formatında tutulur; "
                "`run_classification_eval()` `src/evals/run_evals.py` içinde bu dosyayı okur. "
                "CI workflow `.github/workflows/ci.yml` pytest ve eval gate'i içerir. "
                "`GET /v1/classify/eval` endpoint'i canlı skoru döner."
            ),
            "red_flags": ["LLM-as-judge only", "Judge olmadan RAG production"],
            "strong_signals": ["Deterministic mock eval + judge hybrid", "Versioned dataset"],
            "tags": ["regression", "eval"],
        },
        {
            "question": "Tool çağrısı yapmadan önce hangi validation'ları uygularsın?",
            "answer": (
                "Schema validation ile argüman tipleri ve zorunlu alanlar kontrol edilir. "
                "Auth/RBAC katmanı kullanıcının bu tool'u çağırma yetkisini doğrular. "
                "Policy engine ALLOW/DENY/REQUIRE_APPROVAL kararını verir. "
                "Idempotency key tekrarlayan çağrılarda çift işlem engeller. "
                "Args guardrail injection veya anormal değerleri filtreler. "
                "Yüksek riskli aksiyonlarda human approval onayı alınmadan execution yapılmaz."
            ),
            "deep_dive": (
                "Tool argüman doğrulaması workflow içinde guardrail katmanında uygulanır; "
                "policy kararı `src/agents/policies.py` `evaluate_tool_permission()` ve "
                "`can_execute_tool()` fonksiyonlarından gelir. "
                "Onay gerektiren tool çağrıları `POST /v1/workflow/run` sonrası AWAITING_APPROVAL "
                "status'üne düşer. Audit event `src/security/audit.py` ile kaydedilir."
            ),
            "red_flags": ["Direct exec"],
            "strong_signals": ["Multi-gate", "Audit before exec"],
            "tags": ["tools", "validation"],
        },
        {
            "question": "Bankacılık ortamında guardrail tasarımın nasıl olur?",
            "answer": (
                "Defense in depth: input, retrieval filter, output ve tool execution katmanları birbirini tamamlar. "
                "Input guardrail prompt injection ve data exfiltration girişimlerini yakalar. "
                "Retrieval filter tenant ve role bazlı erişim kontrolü uygular. "
                "Output guardrail PII sızıntısını ve yetkisiz bilgi ifşasını engeller. "
                "Tool execution katmanında policy engine son kararı verir; LLM yetki vermez. "
                "Tek regex veya tek katman guardrail bankacılık ortamında yetersiz kalır."
            ),
            "deep_dive": (
                "`src/security/input_guardrails.py` `validate_user_input()` ve `detect_prompt_injection()` "
                "injection savunmasını sağlar. `src/security/pii.py` `mask_pii()` email, phone ve IBAN maskeler. "
                "`pytest tests/test_guardrails.py` dört katmanın regresyon testini içerir. "
                "Mülakatta katman diyagramını çizmek güçlü sinyal verir."
            ),
            "red_flags": ["Tek regex"],
            "strong_signals": ["Layered defense", "Policy engine"],
            "tags": ["guardrails", "banking"],
        },
        {
            "question": "Evaluation dataset'i nasıl oluşturursun?",
            "answer": (
                "Gerçek kullanıcı sorguları anonimleştirilerek temel dataset oluşturulur. "
                "Edge case'ler (belirsiz intent, çoklu intent, sınır değer tutarları) bilinçli eklenir. "
                "Injection attempt örnekleri guardrail regresyonu için ayrı kategoride tutulur. "
                "SME (subject matter expert) review ile etiket kalitesi doğrulanır. "
                "Dataset JSONL formatında versiyonlanır; her PR'da diff review edilir. "
                "Production feedback pipeline negatif vakaları otomatik aday olarak işaretler."
            ),
            "deep_dive": (
                "Feedback → golden dataset pipeline `src/evals/feedback_store.py` `append_feedback()` ile "
                "başlar; negatif rating'li kayıtlar eval adayı olur. "
                "`POST /v1/feedback` endpoint'i trace_id ile birlikte feedback toplar. "
                "`run_all_evals()` yeni dataset versiyonunu CI'da otomatik skorlar."
            ),
            "red_flags": ["10 synthetic only"],
            "strong_signals": ["Production sampling", "SME labeled"],
            "tags": ["dataset", "eval"],
        },
        {
            "question": "LLM-as-a-Judge nedir ve ne zaman kullanılır?",
            "answer": (
                "LLM-as-a-Judge, bir LLM çıktısını başka bir LLM (veya rubric motoru) ile "
                "değerlendirme yaklaşımıdır. Question, context, generated answer ve rubric "
                "verilir; groundedness, correctness, completeness, safety skorları üretilir. "
                "RAG regression, prompt versiyon karşılaştırma ve synthetic test set "
                "değerlendirmede ölçeklenebilir. Tek başına yeterli değildir; structured "
                "assertion ve golden dataset ile hybrid kullanılmalıdır."
            ),
            "deep_dive": (
                "`src/evals/judge.py` judge_answer() rubric skorları döner. "
                "`GET /v1/evals/judge` golden dataset eval. "
                "`rag_judge_golden.jsonl` FAST/EFT groundedness örnekleri."
            ),
            "red_flags": ["Sadece judge, golden dataset yok"],
            "strong_signals": ["Hybrid eval stack", "Versioned rubric"],
            "tags": ["llm-judge", "eval"],
        },
        {
            "question": "Groundedness ile correctness arasındaki fark nedir?",
            "answer": (
                "Groundedness cevaptaki iddiaların verilen context/kaynak dokümanlarla "
                "desteklenip desteklenmediğini ölçer. Correctness cevabın gerçek dünyada "
                "veya ground truth'a göre doğru olup olmadığını ölçer. Context dışı ama "
                "gerçekte doğru bir cevap: yüksek correctness, düşük groundedness. "
                "RAG sistemlerinde groundedness kritik metriklerden biridir."
            ),
            "deep_dive": (
                "`src/evals/judge.py` her iki metriği ayrı skorlar. "
                "Golden case: EFT hafta sonu — context desteklemez → düşük groundedness."
            ),
            "red_flags": ["İki metriği aynı sanmak"],
            "strong_signals": ["Context vs ground truth ayrımı"],
            "tags": ["llm-judge", "groundedness"],
        },
        {
            "question": "Pointwise ve pairwise evaluation farkı nedir?",
            "answer": (
                "Pointwise: tek cevaba rubric skorları verilir (groundedness 0-5). "
                "Pairwise: iki cevap karşılaştırılır, hangisi daha iyi seçilir. "
                "Pointwise basit ve otomatiktir; skor kalibrasyonu zordur. Pairwise "
                "insan tercihine daha yakın olabilir ama hangi metrikte iyi olduğunu "
                "ayrı ölçmek gerekir. Production'da ikisi birlikte kullanılabilir."
            ),
            "deep_dive": (
                "`src/evals/judge.py` pointwise_eval() ve pairwise_eval() fonksiyonları. "
                "pytest tests/test_judge.py pairwise A vs B groundedness karşılaştırmasını test eder."
            ),
            "red_flags": ["Sadece pairwise, rubric yok"],
            "strong_signals": ["Her iki modu bilerek seçmek"],
            "tags": ["llm-judge", "eval"],
        },
        {
            "question": "LLM-as-a-Judge güvenilirliği nasıl artırılır?",
            "answer": (
                "Net rubric, JSON output zorunluluğu, düşük temperature, golden dataset "
                "kalibrasyonu, insan değerlendirmesiyle korelasyon ölçümü. Birden fazla "
                "judge modeliyle ensemble yapılabilir. Safety-critical kararlar sadece "
                "LLM judge'a bırakılmamalı; rule-based validation ile desteklenmelidir."
            ),
            "deep_dive": (
                "`src/evals/judge.py` deterministic mock judge CI için; "
                "production'da temperature=0 + JSON schema. "
                "`aggregate_metrics()` trend izleme."
            ),
            "red_flags": ["Tek judge, kalibrasyon yok"],
            "strong_signals": ["Human correlation", "Rule-based safety backup"],
            "tags": ["llm-judge", "eval"],
        },
    ],
    11: [
        {
            "question": "Agent'ın hassas müşteri verisini sızdırmasını nasıl engellersin?",
            "answer": (
                "Least privilege prensibi hem retrieval hem tool erişiminde uygulanır. "
                "Retrieval access control tenant ve role bazlı chunk filtrelemesi yapar. "
                "Output filter PII ve yetkisiz bilgiyi response'tan temizler. "
                "PII mask fonksiyonu log ve feedback yazımında zorunlu çalışır. "
                "Tool allowlist dışındaki aksiyonlar policy engine tarafından reddedilir. "
                "Audit trail ve DLP scanning sızdırma girişimlerini geriye dönük tespit eder."
            ),
            "deep_dive": (
                "`src/security/input_guardrails.py` data_exfiltration kategorisinde şüpheli prompt'ları flagler. "
                "`src/security/pii.py` `mask_pii()` hassas alanları maskelemeden geçirmez. "
                "Audit kayıtları `src/security/audit.py` `ComplianceAuditEvent` ile data minimization uygular. "
                "`GET /v1/security/audit/recent` son audit olaylarını listeler."
            ),
            "red_flags": ["Model güvenli"],
            "strong_signals": ["Defense in depth", "Access-controlled RAG"],
            "tags": ["data-leak", "security"],
        },
        {
            "question": "Tool access authorization nasıl tasarlanır?",
            "answer": (
                "Policy engine role × tool × risk matrisi üzerinden karar verir. "
                "Agent hangi tool'u çağıracağını önerir; yetki kararını engine verir, LLM vermez. "
                "Üç sonuç tipi vardır: ALLOW, DENY, REQUIRE_APPROVAL. "
                "Transfer gibi irreversible aksiyonlar varsayılan olarak onay gerektirir. "
                "Policy as code yaklaşımı ile kurallar test edilebilir ve versiyonlanabilir. "
                "Frontend veya client tarafı yetki kontrolü yapmaz; tüm karar server-side'dır."
            ),
            "deep_dive": (
                "`src/agents/policies.py` `evaluate_tool_permission()` ve `can_execute_tool()` "
                "UserRole enum'u ile role matrix'i uygular. "
                "Lab'da `POST /v1/workflow/run` ile '80000 TL transfer' mesajı REQUIRE_APPROVAL senaryosunu tetikler. "
                "`pytest tests/test_security_policy.py` unauthorized denial testlerini içerir."
            ),
            "red_flags": ["LLM decides auth"],
            "strong_signals": ["Policy as code", "Role matrix"],
            "tags": ["authorization", "tools"],
        },
        {
            "question": "Her tool call için audit log'da ne tutarsın?",
            "answer": (
                "Actor (user_id), tenant_id ve action tipi her kayıtta zorunludur. "
                "Args summary data minimization ile tutulur; tam müşteri kaydı yazılmaz. "
                "Approval_id onay gerektiren aksiyonlarda karar izini sağlar. "
                "Result (success/failure/blocked) ve timestamp operasyonel analiz için gereklidir. "
                "Trace_id observability ile audit arasında köprü kurar. "
                "Risk_level alanı yüksek riskli olayların filtrelenmesini kolaylaştırır."
            ),
            "deep_dive": (
                "`ComplianceAuditEvent` yapısı `src/security/audit.py` içinde "
                "`build_policy_audit_event()` ve `build_tool_audit_event()` ile oluşturulur. "
                "Trace correlation için `get_trace()` observability modülünden trace_id çekilir. "
                "`GET /v1/security/audit/recent` endpoint'i `list_recent_audit_logs()` ile son kayıtları döner."
            ),
            "red_flags": ["Full customer record"],
            "strong_signals": ["Data minimization", "Trace correlation"],
            "tags": ["audit", "compliance"],
        },
        {
            "question": "PII içeren prompt'ları nasıl yönetirsin?",
            "answer": (
                "Mümkün olduğunca PII prompt'a hiç sokulmaz; tokenize veya ID referansı kullanılır. "
                "Gerekli durumlarda minimize edilir veya maskelenerek LLM'e gönderilir. "
                "Log yazımında `mask_pii()` zorunlu uygulanır; ham PII CloudWatch'a gitmez. "
                "Feedback store'daki message_preview alanı maskelenmiş halde persist edilir. "
                "Retention policy ile eski log'lar otomatik silinir veya arşivlenir. "
                "GDPR/KVKK uyumu için veri minimizasyonu tasarımın parçasıdır."
            ),
            "deep_dive": (
                "`src/security/pii.py` `mask_pii()` email, phone ve IBAN pattern'lerini `[REDACTED]` ile değiştirir. "
                "`src/evals/feedback_store.py` `append_feedback()` çağrısında message_preview maskelenir. "
                "`POST /v1/feedback` endpoint'i ham PII kabul etmemeli; backend son kontrolü yapar."
            ),
            "red_flags": ["Raw PII in CloudWatch"],
            "strong_signals": ["Mask at write", "Retention policy"],
            "tags": ["pii", "compliance"],
        },
        {
            "question": "Bankacılık ortamında autonomous agent'a hangi limitleri koyarsın?",
            "answer": (
                "Irreversible action (transfer, hesap kapatma) human approval olmadan yapılamaz. "
                "Varsayılan mod read-only'dir; yazma yetkisi explicit grant gerektirir. "
                "Rate limit kullanıcı ve tenant bazında abuse'u engeller. "
                "Token budget aşırı maliyet ve döngüsel çağrıları sınırlar. "
                "Arbitrary code execution kesinlikle yasaktır; tool allowlist dar tutulur. "
                "Her aksiyon audit log'a yazılır; sessiz execution kabul edilmez."
            ),
            "deep_dive": (
                "Workflow `AWAITING_APPROVAL` status'ü `src/agents/workflow.py` içinde onay bekleyen "
                "transfer senaryosunu modeller. Policy engine `src/agents/policies.py` transfer için "
                "REQUIRE_APPROVAL döner. Lab action `POST /v1/workflow/run` onaysız transfer denemesini test eder."
            ),
            "red_flags": ["Full autonomy"],
            "strong_signals": ["Approval gates", "Allowlisted tools"],
            "tags": ["banking", "limits"],
        },
    ],
    12: [
        {
            "question": "Bu AI agent sistemini AWS üzerinde nasıl deploy edersin?",
            "answer": (
                "ALB public subnet'te trafiği karşılar; FastAPI container ECS Fargate task'larında çalışır. "
                "RDS PostgreSQL private subnet'te tutulur; internetten doğrudan erişilemez. "
                "Secrets Manager API key ve DB credential'larını yönetir; rotation planı tanımlanır. "
                "CloudWatch logs ve custom metrics operasyonel görünürlük sağlar. "
                "CI/CD pipeline ECR'a image push eder, ardından terraform apply ile infra güncellenir. "
                "Manuel EC2 SSH deploy yerine IaC ve otomasyon tercih edilir."
            ),
            "deep_dive": (
                "Mimari diyagram `docs/aws_architecture.md` dosyasında tanımlıdır. "
                "Terraform modülleri `infra/terraform/` altında ECS, RDS, ALB ve VPC kaynaklarını yönetir. "
                "CI workflow `.github/workflows/ci.yml` pytest ve docker build smoke test içerir. "
                "Local healthcheck `GET /health` endpoint'i ile doğrulanır."
            ),
            "red_flags": ["EC2 manual SSH"],
            "strong_signals": ["IaC", "Private subnet RDS"],
            "tags": ["aws", "deploy"],
        },
        {
            "question": "FastAPI servisini ECS üzerinde nasıl çalıştırırsın?",
            "answer": (
                "Dockerfile ile production image build edilir; HEALTHCHECK tanımlı olmalıdır. "
                "Image ECR'a push edilir; task definition bu image tag'ini referans alır. "
                "ECS service desired count ve deployment configuration ile yönetilir. "
                "ALB target group /health endpoint'ine health check yapar; unhealthy task trafik almaz. "
                "Auto-scaling CPU veya p95 latency metriklerine göre task sayısını ayarlar. "
                "Tek EC2 without orchestration production için yeterli dayanıklılık sağlamaz."
            ),
            "deep_dive": (
                "Root `Dockerfile` uvicorn CMD ve HEALTHCHECK direktifi içerir. "
                "Terraform `infra/terraform/ecs.tf` task definition ve service kaynaklarını tanımlar. "
                "Deploy test `pytest tests/test_deploy_artifacts.py` artifact bütünlüğünü doğrular. "
                "`GET /health` lab action olarak local smoke test için kullanılır."
            ),
            "red_flags": ["Single EC2 no orchestration"],
            "strong_signals": ["Fargate", "Health-based routing"],
            "tags": ["ecs", "fastapi"],
        },
        {
            "question": "Secrets ve API key yönetimini nasıl yaparsın?",
            "answer": (
                "Secrets Manager veya Parameter Store merkezi secret deposu olarak kullanılır. "
                "ECS task definition environment variable'ları secret reference ile doldurulur. "
                "Rotation planı periyodik key yenileme ve zero-downtime geçiş sağlar. "
                ".env dosyası yalnızca local development içindir; git'e ve Docker image'a girmez. "
                "CI/CD pipeline secret'ları masked variable olarak alır. "
                "Hardcoded API key production kodunda kesinlikle bulunmaz."
            ),
            "deep_dive": (
                "Local `.env` dosyası gitignore'da tutulur; README'de setup adımları açıklanır. "
                "Terraform `infra/terraform/` Secrets Manager kaynağı tanımlayabilir. "
                "`Dockerfile` içinde secret COPY edilmez; runtime injection tercih edilir. "
                "Deploy workflow `docs/deploy_workflow.md` secret handling adımlarını belgeler."
            ),
            "red_flags": [".env in Docker image"],
            "strong_signals": ["Secrets Manager", "Rotation"],
            "tags": ["secrets", "security"],
        },
        {
            "question": "CloudWatch'ta hangi metrikleri takip edersin?",
            "answer": (
                "ECS CPU ve memory utilization kapasite planlaması için izlenir. "
                "ALB 5xx rate servis sağlığının birincil göstergesidir. "
                "p95 latency kullanıcı deneyimi SLA'sını yansıtır. "
                "Custom LLM cost metric token tüketimini dollar bazında gösterir. "
                "Error rate ve log insights trace_id araması incident RCA'yı hızlandırır. "
                "Sadece log toplamak metrik alarmı olmadan yetersiz kalır."
            ),
            "deep_dive": (
                "Uygulama metrikleri `src/observability/metrics.py` `get_metrics().snapshot()` ile üretilir; "
                "CloudWatch exporter bu counter'ları push edebilir. "
                "`GET /v1/observability/metrics` local debug için aynı snapshot'ı sunar. "
                "`docs/aws_architecture.md` monitoring bölümü alarm eşiklerini tanımlar."
            ),
            "red_flags": ["Logs only no metrics"],
            "strong_signals": ["Alarms", "Dashboard per service"],
            "tags": ["cloudwatch", "monitoring"],
        },
        {
            "question": "Production incident olduğunda nasıl rollback yaparsın?",
            "answer": (
                "İlk adım trace ve log ile RCA yapılır; kök neden belgelenmeden rollback yapılmaz. "
                "Önceki stabil Docker image tag'i ECS task definition'a geri alınır. "
                "Terraform veya ECS service update ile deployment geri sarılır. "
                "Kritik durumda desired_count=0 ile trafik tamamen kesilebilir. "
                "Versioned image tag'leri rollback'i tek komutla mümkün kılar. "
                "Fix-forward only yaklaşımı veri kaybı veya güvenlik açığı durumunda risklidir."
            ),
            "deep_dive": (
                "Incident runbook `docs/aws_architecture.md` Incident bölümünde adım adım yazılıdır. "
                "Deploy workflow `docs/deploy_workflow.md` rollback prosedürünü referans alır. "
                "ECR'da her CI build immutable tag ile saklanır. "
                "`pytest tests/test_deploy_artifacts.py` deploy artifact'lerinin varlığını doğrular."
            ),
            "red_flags": ["Fix forward only"],
            "strong_signals": ["Versioned images", "Rollback runbook"],
            "tags": ["incident", "rollback"],
        },
    ],
    13: [
        {
            "question": "Agent response streaming frontend'de nasıl gösterilir?",
            "answer": (
                "SSE (Server-Sent Events) fetch ile backend'e bağlanılır; ReadableStream reader chunk'ları okur. "
                "Her `data:` satırı assistant balonuna append edilir; kullanıcı metni anında görür. "
                "Stream sırasında input disable edilir; çift gönderim engellenir. "
                "Auto-scroll en son token'ı görünür tutar. "
                "Bağlantı kopması durumunda retry veya hata mesajı gösterilir. "
                "Tam response beklemek algılanan latency'yi artırır ve UX'i kötüleştirir."
            ),
            "deep_dive": (
                "`frontend/app.js` içindeki `streamChat()` fonksiyonu SSE reader loop'unu implement eder. "
                "TypeScript referans client `frontend/src/client.ts` `AgenticApiClient` ile "
                "type-safe API çağrıları sağlar. Demo UI `/ui/` path'inden `frontend/hub.js` ile birlikte servis edilir."
            ),
            "red_flags": ["Full response wait"],
            "strong_signals": ["Progressive render", "Retry on fail"],
            "tags": ["streaming", "frontend"],
        },
        {
            "question": "Tool call adımlarını kullanıcıya göstermeli misin?",
            "answer": (
                "Evet, ancak domain-friendly etiketlerle: 'Bilgi aranıyor', 'Policy kontrol ediliyor' gibi. "
                "Raw tool JSON veya internal function adları kullanıcıya gösterilmemelidir. "
                "Bankacılık UX'inde adım görünürlüğü güven oluşturur; sistem çalışıyor hissi verir. "
                "Chain-of-thought (CoT) reasoning sızdırılmaz; yalnızca güvenli özet adımlar gösterilir. "
                "Progress step indicator uzun workflow'larda bekleme toleransını artırır. "
                "Tool failure durumunda kullanıcı dostu hata mesajı gösterilir."
            ),
            "deep_dive": (
                "`frontend/app.js` içinde `STEP_LABELS` objesi tool adımlarını Türkçe domain etiketlerine "
                "map eder. `runWorkflow()` fonksiyonu her adımda UI progress state'ini günceller. "
                "Detaylar `docs/ai_ux_notes.md` dosyasında UX prensipleri olarak belgelenmiştir."
            ),
            "red_flags": ["Raw tool JSON"],
            "strong_signals": ["Domain labels", "Progress steps"],
            "tags": ["ux", "tools"],
        },
        {
            "question": "Human-in-the-loop approval ekranı nasıl tasarlanır?",
            "answer": (
                "Modal veya side card'da özet, risk seviyesi, tool adı ve approval_id birlikte gösterilir. "
                "Confirm ve cancel butonları net ayrılır; tek tık auto-approve kabul edilmez. "
                "Double confirm yüksek tutarlı transferlerde ek güvenlik sağlar. "
                "Onay sonrası workflow resume endpoint'i ile execution devam eder. "
                "Audit id kullanıcıya görünür tutulur; compliance izlenebilirliği sağlanır. "
                "Approval beklerken kullanıcıya timeout ve iptal seçeneği sunulur."
            ),
            "deep_dive": (
                "Approval modal markup `frontend/index.html` içinde `approval-modal` id'li element olarak tanımlıdır. "
                "`frontend/app.js` onay submit'inde approval_id'yi backend'e iletir. "
                "Backend workflow `AWAITING_APPROVAL` status'ünden `POST /v1/workflow/run` resume ile devam eder. "
                "Audit kaydı `src/security/audit.py` approval_id alanını persist eder."
            ),
            "red_flags": ["Tek tık auto-approve"],
            "strong_signals": ["Double confirm", "Audit id visible"],
            "tags": ["approval", "ux"],
        },
        {
            "question": "Frontend'den gelen prompt injection riskleri nasıl azaltılır?",
            "answer": (
                "Frontend untrusted kabul edilir; tüm güvenlik kararları backend'de alınır. "
                "System prompt ve policy kuralları client-side JS'te bulunmaz. "
                "Her API endpoint'inde `validate_user_input()` injection kontrolü çalışır. "
                "Client-side regex filter tek başına yeterli savunma değildir. "
                "API key ve secret'lar frontend bundle'a dahil edilmez. "
                "CORS ve auth token yönetimi backend policy ile sınırlandırılır."
            ),
            "deep_dive": (
                "`src/security/input_guardrails.py` `validate_user_input()` her endpoint'te "
                "(`POST /v1/workflow/run`, chat stream vb.) çağrılır. "
                "`frontend/app.js` yalnızca kullanıcı mesajını iletir; policy logic içermez. "
                "`pytest tests/test_guardrails.py` injection senaryolarını backend seviyesinde test eder."
            ),
            "red_flags": ["Client-side filter only"],
            "strong_signals": ["Backend validation", "No secrets in JS"],
            "tags": ["injection", "frontend"],
        },
        {
            "question": "Kullanıcı feedback'i evaluation pipeline'a nasıl bağlanır?",
            "answer": (
                "Kullanıcı `POST /v1/feedback` ile rating ve opsiyonel trace_id gönderir. "
                "Feedback JSONL store'a PII maskelenmiş olarak yazılır. "
                "Negatif rating'li kayıtlar golden dataset adayı olarak işaretlenir. "
                "Periyodik eval regression yeni adayları skorlar. "
                "trace_id bağlantısı sayesinde tam pipeline replay mümkün olur. "
                "Feedback kaybolmaması için async queue ve persist garantisi gerekir."
            ),
            "deep_dive": (
                "`src/api/routers/feedback.py` `submit_feedback()` endpoint'i feedback request'i alır. "
                "`src/evals/feedback_store.py` `append_feedback()` JSONL dosyasına maskelenmiş kayıt yazar. "
                "Lab action `POST /v1/feedback` body'sinde rating ve message_preview ile test edilir. "
                "Pipeline detayı `docs/ai_ux_notes.md` feedback bölümünde açıklanır."
            ),
            "red_flags": ["Feedback kaybolur"],
            "strong_signals": ["trace_id link", "PII masked store"],
            "tags": ["feedback", "eval"],
        },
    ],
    14: [
        {
            "question": "Kurum çalışanları için internal banking knowledge assistant uçtan uca nasıl kurarsın?",
            "answer": (
                "Problem tanımı ile başlanır: hangi use case'ler (policy lookup, transfer, analiz) kapsamda. "
                "Ingestion pipeline dokümanları tenant ve role bazlı erişim kontrolü ile indexler. "
                "FastAPI workflow orchestrator intent classification, RAG ve tool adımlarını birleştirir. "
                "Hybrid RAG retrieval kalitesini artırır; policy-guarded tools yazma aksiyonlarını sınırlar. "
                "Human approval, audit, eval ve observability production omurgasını oluşturur. "
                "AWS deploy ile MVP: policy lookup + guarded transfer senaryosu canlıya alınır."
            ),
            "deep_dive": (
                "11 bölümlük iskelet `docs/system_design_case_study.md` dosyasında tanımlıdır. "
                "E2E demo `python -m src.case_study.run_demo` komutu ile çalıştırılır. "
                "`POST /v1/workflow/run` endpoint'i case-study senaryolarını (ör. şifre sıfırlama policy) tetikler. "
                "`pytest tests/test_case_study_integration.py` üç E2E senaryoyu doğrular."
            ),
            "red_flags": ["Sadece ChatGPT wrapper"],
            "strong_signals": ["MVP scope", "Security layers"],
            "tags": ["system-design", "e2e"],
        },
        {
            "question": "Bu sistemde en kritik failure mode'lar nelerdir?",
            "answer": (
                "Hallucinated policy yanlış compliance kararına yol açar; RAG + eval ile azaltılır. "
                "Prompt injection yetkisiz aksiyon veya veri sızıntısı riski taşır. "
                "Unauthorized transfer en yüksek iş riski; policy engine + approval gate korur. "
                "LLM timeout kullanıcı deneyimini bozar; fallback ve retry gerekir. "
                "Stale docs güncel olmayan policy cevabı üretir; ingestion refresh pipeline şarttır. "
                "Eval drift ve PII leak uzun vadeli güven kaybına neden olur."
            ),
            "deep_dive": (
                "Failure mode tablosu `docs/system_design_case_study.md` içinde her risk için "
                "mitigation sütunu ile birlikte listelenmiştir. "
                "Her modül kendi guardrail'ini sağlar: `input_guardrails.py`, `policies.py`, `mask_pii()`. "
                "Integration test `tests/test_case_study_integration.py` kritik senaryoları otomatik doğrular."
            ),
            "red_flags": ["Failure mode yok"],
            "strong_signals": ["Mitigation per failure"],
            "tags": ["failure-modes"],
        },
        {
            "question": "İlk MVP'de neyi dahil eder, neyi sonraya bırakırsın?",
            "answer": (
                "MVP kapsamı: workflow orchestrator, guardrails, approval gate, audit trail, eval regression ve demo UI. "
                "Policy lookup ve guarded transfer iki birincil use case olarak yeterli değer sunar. "
                "Hybrid search, gerçek ingestion pipeline ve multi-agent orchestration Phase 2'ye bırakılır. "
                "Operasyonel dashboard ve gelişmiş analytics MVP sonrası eklenir. "
                "Phased rollout ile her fazda Go/No-Go kriteri uygulanır. "
                "Her şeyi day 1'e sığdırmak teslim süresini uzatır ve kaliteyi düşürür."
            ),
            "deep_dive": (
                "Go/No-Go kriterleri `docs/production_readiness_checklist.md` dosyasında tanımlıdır. "
                "MVP modülleri repo'da mevcuttur: workflow, guardrails, audit, eval, frontend demo. "
                "Case study demo `src/case_study/run_demo` MVP kapsamını somutlaştırır. "
                "Stage 14 lab action'ları MVP senaryolarını canlı test etmeyi sağlar."
            ),
            "red_flags": ["Her şey day 1"],
            "strong_signals": ["Phased rollout"],
            "tags": ["mvp", "scope"],
        },
        {
            "question": "Production readiness checklist'in ne olur?",
            "answer": (
                "Security: guardrails aktif, RBAC tanımlı, PII mask zorunlu, pen test tamamlanmış. "
                "Eval regression CI gate geçiyor; golden dataset güncel. "
                "Healthcheck endpoint container orchestrator tarafından doğrulanıyor. "
                "Secrets git ve image dışında yönetiliyor; rotation planı mevcut. "
                "Observability trace + metrics + alarm kurulu; rollback runbook yazılı. "
                "Backup ve disaster recovery prosedürü test edilmiş olmalıdır."
            ),
            "deep_dive": (
                "`docs/production_readiness_checklist.md` 44 maddelik Go/No-Go listesi içerir; "
                "her madde repo'daki modül veya endpoint'e map edilmiştir. "
                "Örnek: guardrails → `test_guardrails.py`, healthcheck → `GET /health`, "
                "audit → `GET /v1/security/audit/recent`. Checklist code review'da birlikte doğrulanır."
            ),
            "red_flags": ["Checklist yok"],
            "strong_signals": ["Mapped to code", "Go/No-Go"],
            "tags": ["production", "checklist"],
        },
        {
            "question": "Business impact'i nasıl ölçersin?",
            "answer": (
                "Resolution time: ortalama soru çözüm süresi agent öncesi/sonrası karşılaştırılır. "
                "Deflection rate: kaç sorgunun insan desteğine gitmeden çözüldüğü ölçülür. "
                "Accuracy eval golden set skoru ile kalite trendi izlenir. "
                "Adoption aktif kullanıcı ve session sayısı ile ölçülür. "
                "Cost per interaction token ve infra maliyetinin interaction'a bölünmesiyle hesaplanır. "
                "Trace ve feedback kaynakları bu metriklerin ham verisini sağlar."
            ),
            "deep_dive": (
                "Impact metrics tablosu stage 14 dokümantasyonunda (`docs/system_design_case_study.md`) "
                "KPI → veri kaynağı eşlemesi ile tanımlıdır. "
                "`GET /v1/observability/metrics` cost ve latency verisi sunar. "
                "`POST /v1/feedback` kullanıcı memnuniyeti sinyalini toplar; "
                "eval skoru accuracy trendini ölçer."
            ),
            "red_flags": ["Impact ölçülmez"],
            "strong_signals": ["Measurable KPIs"],
            "tags": ["business", "impact"],
        },
        {
            "question": "Intent routing ile policy engine arasındaki fark nedir?",
            "answer": (
                "Intent classifier kullanıcının niyetini belirler (general_faq, balance_query, "
                "money_transfer, fraud_report). Policy engine LLM'den bağımsız olarak "
                "authentication, authorization, MFA, transaction limit ve tool izinlerini "
                "kontrol eder. LLM 'transfer yapmak istiyor' diyebilir; transferi başlatma "
                "yetkisi policy katmanındadır. Routing hangi pipeline'a gideceğini seçer; "
                "policy o pipeline'da aksiyonun yapılıp yapılamayacağını belirler."
            ),
            "deep_dive": (
                "`src/case_study/bank_chatbot.py` classify → _map_intent → authorize_action akışı. "
                "`src/agents/policies.py` can_execute_tool production policy engine kararını verir."
            ),
            "red_flags": ["LLM hem intent hem yetki verir"],
            "strong_signals": ["Intent vs policy ayrımı"],
            "tags": ["system-design", "banking"],
        },
        {
            "question": "Bankacılık chatbotunda prompt injection savunması nasıl tasarlanır?",
            "answer": (
                "System prompt ve user input ayrılır; retrieved dokümanlar instruction değil "
                "data olarak ele alınır. Tool permissions LLM dışında policy engine'de kontrol "
                "edilir. Input guardrail injection pattern'lerini classify öncesi bloklar. "
                "Output guardrail PII sızıntısını engeller. Sensitive action için hard-coded "
                "policy ve human escalation zorunludur."
            ),
            "deep_dive": (
                "`src/security/input_guardrails.py` validate_user_input injection bloklar. "
                "Case study scenario prompt_injection_blocked E2E test eder. "
                "`src/case_study/bank_chatbot.py` guardrail ilk pipeline adımıdır."
            ),
            "red_flags": ["Tek katman savunma"],
            "strong_signals": ["Defense in depth", "Retrieval as data not instruction"],
            "tags": ["system-design", "security"],
        },
        {
            "question": "Bank chatbot başarı metrikleri nelerdir?",
            "answer": (
                "Retrieval: Recall@k, MRR, NDCG. Generation: groundedness, correctness, "
                "completeness, safety. Business: containment rate, escalation rate. "
                "UX: CSAT, thumbs up/down. Performance: latency, timeout rate. "
                "Compliance: audit completeness, policy violation rate. "
                "İki katmanlı eval: retrieval ve generation ayrı ölçülmelidir."
            ),
            "deep_dive": (
                "`GET /v1/rag/eval` retrieval metrikleri (MRR, NDCG). "
                "`GET /v1/evals/judge` generation rubric skorları. "
                "`GET /v1/observability/metrics` latency ve cost trendleri."
            ),
            "red_flags": ["Sadece accuracy", "Retrieval ve generation karışık"],
            "strong_signals": ["Two-layer eval", "Business + compliance KPIs"],
            "tags": ["system-design", "metrics"],
        },
    ],
}
