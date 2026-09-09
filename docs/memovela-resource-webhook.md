# Mindful Diabetes → Memovela Resource webhook

When a CMS **post** is published or updated, Mindful Diabetes sends a signed `POST` request to the endpoint in `MEMOVELA_RESOURCE_WEBHOOK_URL`. The release process also sends established site articles that are marked for sharing. The receiving endpoint should upsert a memo into **Dr. J's Global Vela**, with the `resource` tag. Pages, drafts, and archived content are never sent.

The editor can supply a **Memovela Resource Blurb**. When it is blank, Mindful Diabetes automatically uses the article preview summary instead, so publishing never depends on manually writing a second description.

For a one-time resend, run `flask --app app.py sync-memovela-post <article-slug>`. The release process runs `sync-memovela-marked-articles` automatically on each deploy.

## Authentication

The request body is compact UTF-8 JSON. Verify the following before processing it:

1. Reject timestamps more than five minutes old. The Unix timestamp is in `X-Mindful-Timestamp`.
2. Calculate `HMAC-SHA256(MEMOVELA_RESOURCE_WEBHOOK_SECRET, "<timestamp>.<raw request body>")`.
3. Compare it in constant time with `X-Mindful-Signature`, whose value is `sha256=<digest>`.
4. Treat `Idempotency-Key` (also included in the JSON) as unique. The same key must not create a second memo.

Return a 2xx response after a successful create or update. A 409 for an already processed idempotency key is also safe if the endpoint returns it as a 2xx-equivalent success to its own caller; Mindful Diabetes treats only 2xx as confirmed delivery.

## Payload

```json
{
  "event": "mindful_diabetes.resource.upserted",
  "version": 1,
  "idempotency_key": "mindful-diabetes:cnt_123:2026-09-08T12:00:00+00:00",
  "resource": {
    "external_id": "mindful-diabetes:cnt_123",
    "title": "Example article",
    "blurb": "Example article\n\nA short Resource Blurb...\n\nRead the full Mindful Diabetes guide: https://mindfuldiabetes.org/example-article/",
    "url": "https://mindfuldiabetes.org/example-article/",
    "image_url": "https://...",
    "published_at": "2026-09-08T12:00:00+00:00",
    "author": "Mindful Diabetes",
    "tags": ["resource", "mindful-diabetes"],
    "source": {"name": "Mindful Diabetes", "url": "https://mindfuldiabetes.org"},
    "destination": {"vela": "global", "owner": "Dr. J"}
  }
}
```

Use `external_id` to find and update the existing memo. Save the URL, title, generated `blurb`, image, source attribution, and both tags. The canonical location should then appear at `/memos/global?tag=resource`.
