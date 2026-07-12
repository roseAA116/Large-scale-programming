# Troubleshooting

## Trace ID

Every API response includes `trace_id`. Use it to locate structured backend logs for failed requests.

## Material Stuck

Check Redis queue status, worker logs, material status, and object storage connectivity. Failed materials are visible in the admin failed-material view.

## LLM or Embedding Failure

If external API keys are missing, local deterministic fallbacks are used for development. In production, verify URL, key, model name, timeout, and network egress.

## Readiness Failure

`/api/v1/readyz` reports database, Redis, and object storage configuration checks. Fix failed dependencies before enabling traffic.
