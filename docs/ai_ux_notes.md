# AI UX Notları — Aşama 13

Bu doküman, `frontend/` demo arayüzündeki UX kararlarını ve mülakat cevap çerçevesini özetler.

## Hedef

Backend agent sistemini kullanıcıya **anlamlı işlem durumu** ile sunmak; chain-of-thought veya ham tool JSON göstermemek.

## Modlar

| Mod | Endpoint | Kullanım |
|-----|----------|----------|
| Workflow | `POST /v1/workflow/run` | Policy, transfer, onay gerektiren senaryolar |
| Chat Stream | `POST /v1/chat` (`stream: true`) | Serbest sohbet, token-by-token yanıt |

Varsayılan mod **Workflow** — mülakat demosunda agent adımları ve onay akışı ön planda.

## Streaming

- Chat modunda SSE (`data: {"token": "..."}`) okunur; her chunk `assistant` balonuna eklenir.
- Kullanıcı gönder butonuna bastığında input disable edilir; hata olursa **Tekrar dene** görünür.
- Workflow modunda streaming yok; bunun yerine `steps_completed` listesi Türkçe etiketlerle gösterilir.

## Tool / adım görünürlüğü

Ham tool adları yerine domain-dostu etiketler:

- `classify_intent` → Niyet analizi
- `retrieve_context` → Bilgi aranıyor
- `decide_action` → Aksiyon seçiliyor
- `request_human_approval` → Onay kontrolü
- `execute_tool` → İşlem yürütülüyor
- `final_answer` → Yanıt oluşturuluyor

**Prensip:** Banking domain'de kullanıcı "RAG retrieve" değil, "bilgi aranıyor" görür.

## Human-in-the-loop onayı

Yüksek riskli işlemlerde (`needs_human_approval: true`):

1. Yan panelde onay kartı açılır (özet + `approval_id`).
2. Modal ile ikinci onay katmanı (confirm/cancel).
3. Onay → aynı `run_id` + `approval_granted: true` ile workflow resume.
4. İptal → işlem durur; audit backend'de kalır.

Gösterilen bilgiler: seçilen tool, kısa özet, approval id. Tam prompt veya internal reasoning gösterilmez.

## Hata ve retry

- API hataları status banner'da (kırmızı) gösterilir.
- Son mesaj `state.lastMessage` ile saklanır; retry aynı isteği tekrarlar.
- Stream kopması veya 4xx/5xx için kullanıcıya net Türkçe mesaj.

## Trace / debug paneli

- Workflow sonrası `trace_summary` JSON olarak sağ panelde gösterilir.
- Üretimde bu panel sadece internal/admin kullanıcıya açılır; demo'da herkese açık (geliştirme kolaylığı).

Tam trace: `GET /v1/observability/traces/{trace_id}`

## Feedback → evaluation pipeline

1. Kullanıcı 👍/👎 ile `POST /v1/feedback` çağırır.
2. Kayıt `data/feedback.jsonl` dosyasına append edilir.
3. Her kayıt `trace_id` ve `run_id` ile workflow trace'e bağlanır.
4. `message_preview` ve `comment` PII maskelenir (`mask_pii`).
5. Negatif feedback örnekleri golden dataset veya regression eval'e eklenebilir.

```text
UI feedback → /v1/feedback → feedback.jsonl → (manuel/otomatik) eval dataset
```

## Frontend güvenlik (prompt injection)

- Frontend input **trusted değildir**; tüm validation backend'de (`input_guardrails`, policy, SQL guardrails).
- UI sadece JSON body gönderir; system prompt veya tool policy frontend'de tutulmaz.
- Yüksek riskli aksiyonlar UI'dan bypass edilemez — backend `needs_human_approval` zorunlu kılar.

## Dosya yapısı

```text
frontend/
  index.html    # layout, mod switch, onay modal
  styles.css    # minimal banking-demo tema
  app.js        # vanilla JS, fetch + SSE
  src/
    types.ts    # API contract (typecheck)
    client.ts   # TypeScript client referansı
```

Build adımı yok; FastAPI `/ui` altında static serve eder.

## Mülakat kısa cevapları

1. **Streaming:** SSE chunk'ları tek assistant balonuna append; scroll ve disable state ile UX.
2. **Tool görünürlüğü:** Domain etiketleri; ham CoT veya JSON kullanıcıya gösterilmez.
3. **Onay ekranı:** Özet + risk + approval id + confirm/cancel; resume ile devam.
4. **Injection:** Backend guardrails; frontend sadece untrusted transport.
5. **Feedback → eval:** `trace_id` ile bağla; JSONL store; negatif örnekleri dataset'e taşı.
