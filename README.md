# Plasma Engine Research

Async research automation service powering Deep Research workflows, parallel search, and GraphRAG knowledge ingestion.

## Stack

- Python 3.11, AsyncIO, Neo4j, Redis, Celery/Prefect (TBD)
- Integrations: Perplexity, Exa, Tavily, custom crawlers

## CI

Pull requests trigger the shared [lint-test](.github/workflows/ci.yml) and security scan workflows. CodeRabbit provides automated review feedback.

## Local Development

```bash
git clone https://github.com/xkonjin/plasma-engine-research.git
cd plasma-engine-research

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # temporary placeholder
```

Start the shared Compose stack (see development handbook) to provision Neo4j/Redis/Postgres dependencies.

## Contribution Checklist

- [ ] Issue linked to Program board (PE-XX)
- [ ] Lint/test locally before PR
- [ ] Update documentation and ADRs when architecture changes
- [ ] Ensure knowledge graph migrations are idempotent

Refer to the [Development Handbook](../plasma-engine-shared/docs/development-handbook.md) for environment details.
