"""Aşama 15 — Genişletilmiş behavioral/leadership mülakat soruları."""

STAGE15_INTERVIEW_QA: list[dict] = [
    {
        "question": "Business beklentisi gerçekçi değilse nasıl yönetirsin?",
        "answer": (
            "Önce empati ile dinler, paydaşın gerçek acısını anlamaya çalışırım; "
            "story-1'de operasyon ekibi 'ChatGPT gibi bir şey, tüm dokümanları yükleyelim' dediğinde "
            "scope, güvenlik ve ölçüm kriterlerinin belirsiz olduğunu gördüm. "
            "Beklentiyi somut KPI'lara çevirir, ortalama cevap süresi ve eval pass rate gibi "
            "ölçülebilir hedefler öneririm. "
            "Riskleri teknik jargon yerine business diliyle anlatırım: compliance, veri sızıntısı, "
            "maliyet ve itibar riski. "
            "MVP scope'u net sınırlar, riskli aksiyonları fazlı plana alırım — "
            "story-1'de transfer aksiyonunu Faz 2'ye bırakıp 'policy lookup + kaynaklı cevap + audit' "
            "ile başladık. "
            "Alternatif fazlı yol haritası sunarım: önce knowledge, sonra guarded action. "
            "Son adımda yazılı scope agreement ve eval kriterleri ile tüm tarafları hizalarım; "
            "plan onaylandığında pilot departmanda cevap süresi %45 azaldı."
        ),
        "deep_dive": (
            "Bankacılık bağlamında 'autonomous agent' beklentisi sık karşılaşılan bir durumdur. "
            "Bu beklentiyi doğrudan reddetmek yerine approval gate, audit log ve citation zorunluluğu "
            "gibi kontrollü mekanizmalarla yönetirim. "
            "Story-1'de full agent autonomy yerine guarded routing seçmemizin nedeni hallucination "
            "ve transfer gibi yüksek riskli senaryolardı. "
            "Paydaşa 'hayır' demek yerine 'önce güvenli omurgayı kuruyoruz, sonra aksiyon genişletiyoruz' "
            "narrative'i sunmak güven oluşturur. "
            "Eval regression ve trace_id zorunluluğu gibi teknik guardrail'leri business KPI'larıyla "
            "eşleştirerek teknik derinliği anlaşılır kılarsın."
        ),
        "red_flags": ["Hayır diyemem", "Teknik jargon ile boğ"],
        "strong_signals": ["Phased MVP", "Written KPIs", "Risk framing"],
        "tags": ["leadership", "stakeholder"],
    },
    {
        "question": "Junior engineer riskli agent tasarımı önerirse nasıl yönlendirirsin?",
        "answer": (
            "Önce öneriyi anlamaya çalışır, junior'ın motivasyonunu ve demo etkisini küçümsemem; "
            "story-3'te ekip 'LLM'e tüm DB tool'larını verelim' fikrine heyecanlıydı çünkü demo "
            "etkileyici görünüyordu. "
            "Sonra riski somut gösteririm: test ortamında DELETE TABLE senaryosunu çalıştırdım "
            "ve blast radius'u herkes gördü. "
            "Risk matrisi çizerek tool genişliği ile güvenlik riskini karşılaştırır, "
            "read-only analyst agent, SQL guardrails, tenant filter ve approval gibi güvenli alternatifi "
            "birlikte tasarlarız. "
            "Pair programming ile data_analyst.py ve guardrails.py'yi birlikte yazdık; "
            "blame yok, öğrenme fırsatı var. "
            "Junior'a ownership devrederim — golden SQL eval dataset'ini o sahiplensin diye "
            "story-3'te 2 haftada eval pipeline sahibi oldu. "
            "Sonuç olarak ekip güvenli yolu seçti ve junior mülakat sunumunda güvenlik katmanlarını "
            "kendisi anlattı."
        ),
        "deep_dive": (
            "Story-3'teki read-only analyst alternatifi, esneklikten ödün vererek production riskini "
            "kabul edilebilir seviyeye indirdi. "
            "Policy as code yaklaşımı prompt'ta 'lütfen silme' demekten çok daha güvenilirdir; "
            "AST validation ve DB read-only role son savunma hattıdır. "
            "Toplantıda eleştirmek yerine demo ile göstermek ikna gücü yüksektir. "
            "Junior'a sorumluluk vermek motivasyonu artırır ve güvenli pattern'i içselleştirmesini "
            "sağlar. "
            "Mentorluk = ownership devretmek; teknik yönlendirme ile birlikte görünür sorumluluk "
            "vermek en kalıcı öğrenme yoludur."
        ),
        "red_flags": ["Toplantıda eleştiri", "Sen yap"],
        "strong_signals": ["Safe alternative", "Mentorship", "Shared ownership"],
        "tags": ["mentorship", "leadership"],
    },
    {
        "question": "PoC'yi production sistemine çevirmek için hangi adımları uygularsın?",
        "answer": (
            "Story-2'de notebook'ta çalışan RAG+LLM demosu vardı; hardcoded API key, sync blocking, "
            "test yok ve log'da müşteri IBAN'ı vardı — stakeholder 'haftaya pilot' dediğinde "
            "sistematik hardening şarttı. "
            "İlk adım interface + mock test: LLMClient interface ve MockLLMClient ile CI pytest "
            "kurarak deterministik test omurgası oluşturdum. "
            "Timeout/retry, structured errors, PII mask_pii audit pipeline ve input guardrails "
            "(injection/exfiltration) ekledim. "
            "Observability için trace timeline ve healthcheck'li Dockerfile hazırladım. "
            "Golden eval 10 case'i deploy gate yaptım; eval geçmeden production'a çıkmıyoruz. "
            "Secrets yönetimi, rollback planı (önceki Docker tag + eval gate) ve feature flag ile "
            "pilot için sadece knowledge açık, transfer kapalı başlattık. "
            "Pilot 3 hafta gecikmeyle açıldı ama sıfır P1 incident, 100+ pytest ve ilk ay "
            "0 unauthorized tool execution ile güven kazandık."
        ),
        "deep_dive": (
            "Story-2'deki defense-in-depth yaklaşımı guardrails → policy → approval → audit "
            "katmanlarından oluşur. "
            "PoC'de 'hızlı' alınan shortcut'ların production maliyeti 3-5 kat olabilir; "
            "ilk günden test zorunlu kılmak en iyi yatırımdır. "
            "Idempotency için tool execution'da DB unique constraint, rollback için eval gate "
            "kritik teknik detaylardır. "
            "Checklist driven yaklaşım (production readiness maddeleri) hiçbir adımın atlanmamasını "
            "sağlar. "
            "Feature flag ile kademeli rollout, tam kapasiteye geçmeden önce gerçek kullanıcı "
            "davranışını güvenli ortamda gözlemlemeni sağlar."
        ),
        "red_flags": ["Direkt deploy", "Test sonra"],
        "strong_signals": ["Checklist driven", "Feature flag"],
        "tags": ["production", "poc"],
    },
    {
        "question": "AI çözümünün business impact'ini nasıl ölçersin?",
        "answer": (
            "Story-5'te yönetim 'AI projesi ROI göster' dediğinde teknik metrikler vardı ama "
            "business diline çevrilmemişti; önce baseline ölçüm şarttır. "
            "Manuel policy arama süresini ölçtük: ortalama 15 dakika; agent sonrası resolution time "
            "2 dakikaya indi. "
            "Deflection rate'i escalasyon oranı %40'tan %68'e çıkış olarak takip ettik. "
            "Accuracy için eval pass rate, adoption için haftalık kullanım, maliyet için "
            "token cost/interaction ($0.03) metriklerini bir arada izledik. "
            "Baseline vs after karşılaştırması yaparak Finance ile cost avoidance hesabı "
            "(FTE saat tasarrufu) oluşturduk. "
            "Executive dashboard'da resolution time, deflection ve cost/interaction üç KPI "
            "haftalık güncellendi. "
            "Pilot ROI pozitif çıktı ve Faz 2 budget onayı alındı."
        ),
        "deep_dive": (
            "Story-5'teki ROI hesabı, observability/traces ve feedback verisini business narrative'e "
            "dönüştürmeyi gösterir. "
            "Sadece accuracy veya latency raporlamak yönetim için yeterli değildir; "
            "FTE tasarrufu ve escalasyon azalması gibi somut business çıktıları gerekir. "
            "Daha ucuz model kullanımı gibi trade-off'ları quality eval ile koruyarak maliyet "
            "optimizasyonu yapılabilir. "
            "Business metrikleri discovery aşamasında tanımlanmalı; sonradan veri toplamak "
            "çok daha zordur. "
            "Traceable metrics sayesinde her iddia kanıtlanabilir ve executive güveni artar."
        ),
        "red_flags": ["Sadece accuracy"],
        "strong_signals": ["ROI narrative", "Traceable metrics"],
        "tags": ["impact", "metrics"],
    },
    {
        "question": "Bir model/agent incident'ında ownership'i nasıl alırsın?",
        "answer": (
            "Story-4'te pilot'ta agent yanlış transfer limiti policy'si söyledi; stale doc nedeniyle "
            "operasyon 2 yanlış işlem başlattı ve stakeholder güveni sarsıldı. "
            "İlk hareket communicate: durumu şeffaf paylaşır, timeline veririm. "
            "trace_id ile replay yaparak root cause'u buldum: stale chunk retrieval ve eski doc version. "
            "Blameless postmortem'de ingestion TTL eksikliği ve eval set coverage gap'i tespit ettik. "
            "48 saat içinde hotfix: doc version metadata, retrieval filter 'active_only', "
            "golden dataset'e 5 yeni policy case, kaynak göster UI zorunlu, düşük confidence'ta "
            "abstention mesajı. "
            "Eval %96'ya çıktı, 2 hafta sonra otomatik regression eklendi. "
            "Stakeholder'a şeffaf RCA raporu sundum; incident'ı gizlemek yerine ownership "
            "uzun vadede güveni artırdı."
        ),
        "deep_dive": (
            "Story-4'teki stale doc incident'ında asıl sorun LLM değil retrieval failure'dı; "
            "fix data pipeline + eval ile yapıldı, sadece prompt tweak yetmezdi. "
            "Model vendor'u suçlamak veya hatayı gizlemek red flag'dir; 48 saat içinde RCA + "
            "kalıcı fix beklenir. "
            "Eval coverage gap analizi rutin olmalı; her incident yeni golden case eklenmesi "
            "için fırsattır. "
            "Retrieval version mismatch alert gibi monitoring, aynı hata sınıfının tekrarını "
            "önler. "
            "Blameless kültür kalıcı aksiyonları mümkün kılar; ekip öğrenir, sistem güçlenir."
        ),
        "red_flags": ["Model vendor suçu", "Gizle"],
        "strong_signals": ["48h RCA", "Permanent fix", "Eval regression"],
        "tags": ["incident", "ownership"],
    },
]
