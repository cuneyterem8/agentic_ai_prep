"""Stage 15 — Behavioral & Technical Leadership content."""

STAGE15_CONTENT = {
    "title": "Behavioral & Technical Leadership",
    "subtitle": "STAR hikayeleri, takım etkisi, teknik karar alma",
    "summary": (
        "Expert seviyede sadece kod değil: cross-functional çalışma, trade-off anlatma, "
        "incident ownership ve ölçülebilir business impact. Her hikaye STAR + Technical Depth formatında."
    ),
    "topics": [
        "Cross-functional çalışma",
        "PoC → production hardening",
        "Teknik yönlendirme ve mentorluk",
        "Incident ownership",
        "Business impact ölçümü",
        "Ambiguity management",
    ],
    "stories": [
        {
            "id": "story-1",
            "title": "Belirsiz business ihtiyacını teknik plana çevirme",
            "situation": (
                "Operasyon ekibi 'çalışanlar policy sorularına çok uzun sürede cevap buluyor' dedi. "
                "İlk talep: 'ChatGPT gibi bir şey koyalım, tüm dokümanları yükleyelim.' "
                "Scope, güvenlik ve ölçüm kriterleri belirsizdi."
            ),
            "task": (
                "2 hafta içinde net MVP scope, güvenlik gereksinimleri ve başarı metrikleri ile "
                "onaylanabilir teknik plan sunmam istendi."
            ),
            "action": (
                "5 operasyon görüşmesi yaptım; soru tiplerini knowledge vs action olarak ayırdım. "
                "Riskli senaryoları (transfer, veri sızıntısı) ayrı listeledim. "
                "MVP'yi 'policy lookup + kaynaklı cevap + audit' olarak sınırladım; transfer aksiyonunu Faz 2'ye aldım. "
                "Teknik planda mock LLM ile test edilebilir omurga, golden eval ve trace_id zorunluluğu koydum. "
                "Business ile ortak KPI: ortalama cevap süresi ve doğruluk (eval pass rate)."
            ),
            "result": (
                "Plan onaylandı. 6 haftada MVP canlı; pilot departmanda ortalama cevap süresi %45 azaldı. "
                "Eval pass rate %92. Compliance audit'te eksik bulgu yok."
            ),
            "technical_depth": (
                "Mimari: FastAPI + deterministic workflow + RAG citations + input guardrails. "
                "Trade-off: full agent autonomy yerine guarded routing. "
                "Failure mode: hallucination → citation zorunlu + eval regression. "
                "Monitoring: trace timeline + feedback.jsonl."
            ),
            "reflection": (
                "Bugün olsa discovery'ye 1 hafta daha ayırır, kullanıcı sorularından golden dataset'i "
                "daha erken oluştururdum. Business dilinde KPI'yi ilk günden yazdırırım."
            ),
        },
        {
            "id": "story-2",
            "title": "PoC'yi production'a taşırken hardening",
            "situation": (
                "Notebook'ta çalışan RAG+LLM demosu vardı; stakeholder 'haftaya pilot' dedi. "
                "Demo hardcoded API key, sync blocking calls, test yok, log'da müşteri IBAN'ı vardı."
            ),
            "task": "Demo'yu güvenli, test edilebilir, deploy edilebilir servise dönüştürmek.",
            "action": (
                "1) LLMClient interface + MockLLMClient → CI pytest. "
                "2) Timeout/retry + structured errors. "
                "3) PII mask_pii audit pipeline. "
                "4) Input guardrails (injection/exfiltration). "
                "5) Dockerfile + healthcheck. "
                "6) Golden eval 10 case → deploy gate. "
                "7) Pilot için feature flag: sadece knowledge, transfer kapalı."
            ),
            "result": (
                "Pilot 3 hafta gecikmeyle ama sıfır P1 incident ile açıldı. "
                "pytest 100+ test, eval regression CI'da. İlk ay 0 unauthorized tool execution."
            ),
            "technical_depth": (
                "Defense in depth: guardrails → policy → approval → audit. "
                "Idempotency tool execution için DB unique constraint. "
                "Rollback: önceki Docker tag + eval gate."
            ),
            "reflection": "PoC'de 'hızlı' alınan shortcut'ların production maliyeti 3-5x. İlk günden test zorunlu kılmalıydım.",
        },
        {
            "id": "story-3",
            "title": "Junior engineer riskli agent tasarımını yönlendirme",
            "situation": (
                "Junior engineer 'LLM'e tüm DB tool'larını verelim, kendisi SQL yazsın' önerdi. "
                "Ekip heyecanlıydı çünkü demo etkileyici görünüyordu."
            ),
            "task": "Teknik olarak doğru ama güvenli alternatifi savunmak ve ekibi ikna etmek.",
            "action": (
                "Demo'da DELETE TABLE senaryosunu çalıştırdım (test ortamında). "
                "Risk matrisi çizdim: tool genişliği vs blast radius. "
                "Alternatif: read-only analyst agent, SQL guardrails, tenant filter, row limit, approval. "
                "Pair programming ile data_analyst.py ve guardrails.py birlikte yazdık. "
                "Junior'a ownership verdim: golden SQL eval dataset'i o sahiplensin."
            ),
            "result": (
                "Ekip read-only analyst yolunu seçti. Junior 2 haftada eval pipeline sahibi oldu. "
                "Mülakat/jüri sunumunda güvenlik katmanlarını o anlattı."
            ),
            "technical_depth": (
                "Policy as code > prompt'ta 'lütfen silme'. "
                "AST validation + DB read-only role son savunma. "
                "Trade-off: esneklik azaldı ama production riski kabul edilebilir seviyeye indi."
            ),
            "reflection": "Blame etmeden demo ile göstermek ikna gücü yüksek. Junior'a sorumluluk vermek motivasyonu artırdı.",
        },
        {
            "id": "story-4",
            "title": "Agent incident sonrası ownership",
            "situation": (
                "Pilot'ta agent yanlış transfer limiti policy'si söyledi (stale doc). "
                "Operasyon 2 yanlış işlem başlattı; biri approval'da durdu, biri düzeltildi. "
                "Stakeholder güveni sarsıldı."
            ),
            "task": "Root cause, kalıcı fix ve güven restorasyonu — 48 saat içinde.",
            "action": (
                "trace_id ile replay: stale chunk retrieval + eski doc version. "
                "Blameless postmortem: ingestion TTL yoktu, eval set bu policy'yi kapsamıyordu. "
                "Aksiyonlar: doc version metadata, retrieval filter 'active_only', "
                "golden dataset'e 5 yeni policy case, 'kaynak göster' UI zorunlu, "
                "düşük confidence'ta abstention mesajı."
            ),
            "result": (
                "48 saat içinde hotfix + eval %96. 2 hafta sonra aynı hata sınıfı için otomatik regression. "
                "Stakeholder'a şeffaf RCA raporu sunuldu."
            ),
            "technical_depth": (
                "RCA: retrieval failure not LLM failure. "
                "Fix: data pipeline + eval not prompt tweak only. "
                "Monitoring: retrieval version mismatch alert."
            ),
            "reflection": "Incident'ı gizlemek yerine şeffaf RCA güveni uzun vadede artırdı. Eval coverage gap analizi rutin olmalı.",
        },
        {
            "id": "story-5",
            "title": "Ölçülebilir business impact",
            "situation": (
                "Yönetim 'AI projesi ROI göster' dedi. Teknik metrikler (latency, accuracy) vardı "
                "ama business diline çevrilmemişti."
            ),
            "task": "3 ay pilot sonunda ROI story oluşturmak.",
            "action": (
                "Baseline ölçüm: manuel policy arama süresi (15 dk ortalama). "
                "Agent sonrası: trace latency + resolution time (2 dk). "
                "Deflection: escalasyon oranı %40 → %68. "
                "Cost: token cost/interaction $0.03. "
                "Dashboard: haftalık adoption, accuracy (eval), cost. "
                "Finance ile cost avoidance hesabı: FTE saat tasarrufu."
            ),
            "result": (
                "Pilot ROI pozitif; Faz 2 budget onayı. "
                "3 KPI executive dashboard'da: resolution time, deflection, cost/interaction."
            ),
            "technical_depth": (
                "Metrics: observability/traces + feedback. "
                "Trade-off: daha ucuz model classify için, quality eval ile korundu."
            ),
            "reflection": "Business metrikleri discovery aşamasında tanımlanmalı; sonradan veri toplamak zor.",
        },
    ],
    "interview_qa": [
        {
            "question": "Business beklentisi gerçekçi değilse nasıl yönetirsin?",
            "answer": (
                "Empati ile dinle, beklentiyi somut KPI'lara çevir, MVP scope öner. "
                "Riskleri business diliyle anlat (güvenlik, compliance, maliyet). "
                "Alternatif fazlı plan sun: 'hafta 4'te knowledge, hafta 8'de guarded action.' "
                "Yazılı scope agreement ve eval kriterleri ile hizala."
            ),
            "deep_dive": "Bankacılık bağlamında autonomous agent beklentisini approval gate ile yönet.",
            "red_flags": ["Hayır diyemem", "Teknik jargon ile boğ"],
            "strong_signals": ["Phased MVP", "Written KPIs", "Risk framing"],
            "tags": ["leadership", "stakeholder"],
        },
        {
            "question": "Junior engineer riskli agent tasarımı önerirse nasıl yönlendirirsin?",
            "answer": (
                "Önce anla, sonra risk demo'su ile göster. Pair programming ile güvenli pattern yazdır. "
                "Ownership ver (eval, guardrails test). Blame yok; öğrenme fırsatı."
            ),
            "deep_dive": "story-3 örneği: read-only analyst alternatifi.",
            "red_flags": ["Toplantıda eleştiri", "Sen yap"],
            "strong_signals": ["Safe alternative", "Mentorship", "Shared ownership"],
            "tags": ["mentorship", "leadership"],
        },
        {
            "question": "PoC'yi production sistemine çevirmek için hangi adımları uygularsın?",
            "answer": (
                "1) Interface + mock test 2) Timeout/retry 3) Guardrails 4) Observability 5) Eval regression "
                "6) Secrets 7) Deploy artifact 8) Rollback plan 9) Feature flag pilot 10) Post-launch monitoring."
            ),
            "deep_dive": "production_readiness_checklist.md 44 madde.",
            "red_flags": ["Direkt deploy", "Test sonra"],
            "strong_signals": ["Checklist driven", "Feature flag"],
            "tags": ["production", "poc"],
        },
        {
            "question": "AI çözümünün business impact'ini nasıl ölçersin?",
            "answer": (
                "Resolution time, deflection rate, accuracy (eval), adoption, cost/interaction. "
                "Baseline vs after comparison. Executive dashboard haftalık."
            ),
            "deep_dive": "story-5 ROI hesabı.",
            "red_flags": ["Sadece accuracy"],
            "strong_signals": ["ROI narrative", "Traceable metrics"],
            "tags": ["impact", "metrics"],
        },
        {
            "question": "Bir model/agent incident'ında ownership'i nasıl alırsın?",
            "answer": (
                "İlk sorumlu ol: communicate, trace RCA, hotfix, postmortem, kalıcı aksiyon. "
                "Blameless kültür. Stakeholder'a şeffaf timeline. Eval gap kapat."
            ),
            "deep_dive": "story-4 stale doc incident.",
            "red_flags": ["Model vendor suçu", "Gizle"],
            "strong_signals": ["48h RCA", "Permanent fix", "Eval regression"],
            "tags": ["incident", "ownership"],
        },
    ],
    "principles": [
        "Empati + teknik netlik birlikte",
        "Trade-off'ları business diliyle anlat",
        "Küçük MVP, net ölçüm, güvenli rollout",
        "Blameless postmortem, kalıcı aksiyon",
        "Mentorluk = ownership devretmek",
    ],
}
