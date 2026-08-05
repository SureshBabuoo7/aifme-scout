# CLI Reference

Complete command reference for the `aifme-scout` CLI.

## Synopsis

```bash
aifme-scout [OPTIONS] scan <URL>
aifme-scout --version
aifme-scout --help
```

## Commands

### `aifme-scout scan <URL>`

Scan a website and produce JSON and/or Markdown output.

**Positional Arguments:**

| Argument | Description |
|----------|-------------|
| `<URL>` | The target URL to scan. Must be a valid HTTP or HTTPS URL. |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--output <FORMAT>` | Export format: `json`, `markdown`, or `both` | `both` |
| `--out <DIR>` | Output directory for report files | Current directory |
| `--config <FILE>` | Path to YAML configuration file | None |
| `--timeout <SECONDS>` | HTTP request timeout in seconds | `10` |
| `--user-agent <STRING>` | Custom User-Agent header | `AIFME-Scout-OSS/1.0.0` |
| `--mode <MODE>` | Summary mode: `no-llm` or `llm` | `no-llm` |
| `--verbose` | Enable verbose (DEBUG) logging | Disabled |
| `--quiet` | Suppress all output except errors | Disabled |
| `--version` | Print version and exit | — |
| `--help` | Print help message and exit | — |

## Options

### `--output`

Controls which output files are generated:

- `json` — Only `scan-result.json`
- `markdown` — Only `report.md`
- `both` — Both files (default)

### `--out`

Directory where output files are written. Created if it does not exist.

```bash
aifme-scout scan https://www.python.org --out ./reports
```

### `--timeout`

HTTP request timeout in seconds. Applies to connect, read, and write phases.

```bash
aifme-scout scan https://www.python.org --timeout 30
```

### `--user-agent`

Custom User-Agent header sent with every HTTP request.

```bash
aifme-scout scan https://www.python.org --user-agent "MyBot/1.0"
```

### `--mode`

Summary generation mode:

- `no-llm` (default) — Deterministic, template-based summary. Zero network calls beyond the target site.
- `llm` — Attempts LLM-backed summary generation. Falls back to `no-llm` when no provider is configured.

### `--verbose` / `--quiet`

Mutually exclusive. Controls logging verbosity:

- Default — INFO level (progress and summary)
- `--verbose` — DEBUG level (full request/response details)
- `--quiet` — ERROR level only

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Invalid arguments or configuration error |
| `2` | Network failure |
| `3` | Scanner failure (robots.txt, anti-bot, timeout) |
| `4` | Parser failure |
| `5` | Internal error |

## Configuration

Configuration is resolved with the following precedence (highest to lowest):

1. **CLI flags** — Command-line options
2. **Environment variables** — `SCOUT_*` variables
3. **Config file** — `scout.config.yaml` (YAML format)
4. **Built-in defaults** — Hardcoded fallbacks

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SCOUT_OUTPUT_DIR` | Output directory | `.` (current directory) |
| `SCOUT_MODE` | Summary mode | `no-llm` |
| `SCOUT_PROVIDER` | LLM provider | None |
| `SCOUT_CRAWL_DELAY_MS` | Crawl delay in milliseconds | `1000` |
| `SCOUT_MAX_PAGES` | Maximum pages to scan | `25` |
| `SCOUT_LOG_LEVEL` | Log level | `INFO` |
| `SCOUT_TIMEOUT` | Request timeout | `10` |

### Config File

Create `scout.config.yaml` in your working directory:

```yaml
output_dir: ./reports
mode: no-llm
crawl_delay_ms: 1000
max_pages: 25
log_level: WARNING
timeout: 10
user_agent: AIFME-Scout-OSS/1.0.0
```

## Examples

### Scan with all options

```bash
aifme-scout scan https://www.python.org \
  --output json \
  --out ./reports \
  --timeout 30 \
  --user-agent "CustomBot/1.0" \
  --verbose
```

### Quiet CI/CD scan

```bash
aifme-scout scan https://www.python.org --quiet --output json --out ./ci-reports
```

### Batch scan

```bash
for url in https://python.org https://openai.com; do
  aifme-scout scan "$url" --quiet || echo "Failed: $url"
done
```

### Scan with config file

```bash
aifme-scout scan https://www.python.org --config ./scout.config.yaml
```

## See Also

- [Quick Start](QUICK_START.md) — Getting started guide
- [Report Reference](REPORT_REFERENCE.md) — Markdown report structure
- [JSON Reference](JSON_REFERENCE.md) — JSON schema documentation
- [CLI Guide](cli-guide.md) — Additional CLI usage notes
