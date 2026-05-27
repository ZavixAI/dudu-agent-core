# dudu-agent-core

Minimal FastAPI backend with a FastMCP demo integration.

## Structure

```text
app/
├── api/mcp.py              # FastMCP app and demo echo tool
├── main.py                 # FastAPI entrypoint
├── lifecycle.py            # lightweight app lifespan
├── config/                 # environment-backed configuration
├── core/http/              # response, exception, request context, middleware helpers
├── core/infra/             # generic infrastructure helpers
├── core/metrics.py         # in-process Prometheus text metrics
└── utils/                  # logging, env, and time helpers
```

## Run

```bash
pip install -r app/requirements.txt
PYTHONPATH=app python app/main.py
```

Useful endpoints:

- `GET /health`
- `GET /metrics`
- MCP HTTP app mounted under `/mcp`

Configuration uses the `DUDU_` environment prefix:

- `DUDU_PORT`
- `DUDU_LOG_LEVEL`
- `DUDU_MYSQL_HOST`
- `DUDU_MYSQL_PORT`
- `DUDU_MYSQL_USER`
- `DUDU_MYSQL_PASSWORD`
- `DUDU_MYSQL_DATABASE`
