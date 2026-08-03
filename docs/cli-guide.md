# CLI Guide

Scout OSS provides a command-line interface for scanning websites and
generating reports.

## Installation

The CLI is installed as the `aifme-scout` console script when the package
is installed.

## Command Reference

### `aifme-scout scan <url>`

Scan a website and produce JSON and/or Markdown output.

```bash
aifme-scout scan https://www.python.org
```

### `aifme-scout --help`

Print help and exit.

### `aifme-scout --version`

Print version and exit.

## Options

| Flag | Description |
|---|---|
| `--output json\|markdown\|both` | Export format (default: `both`) |
| `--out <directory>` | Output directory (default: current directory) |
| `--config <file>` | Path to configuration file |
| `--timeout <seconds>` | Request timeout in seconds |
| `--user-agent <string>` | Custom User-Agent header |
| `--mode no-llm\|llm` | Summary generation mode (default: `no-llm`) |
| `--verbose` | Enable verbose logging |
| `--quiet` | Suppress all output except errors |
| `--version` | Print version and exit |
| `--help` | Print help and exit |

## Examples

### Basic scan

```bash
aifme-scout scan https://www.python.org
```

### JSON output only

```bash
aifme-scout scan https://www.python.org --output json --out ./reports
```

### Markdown output only

```bash
aifme-scout scan https://www.python.org --output markdown --out ./reports
```

### Custom timeout and user agent

```bash
aifme-scout scan https://www.python.org --timeout 30 --user-agent "MyBot/1.0"
```

### Verbose mode

```bash
aifme-scout scan https://www.python.org --verbose
```

### Quiet mode

```bash
aifme-scout scan https://www.python.org --quiet
```

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Invalid arguments or configuration error |
| `2` | Network failure |
| `3` | Scanner failure |
| `4` | Parser failure |
| `5` | Internal error |

## Configuration

Configuration is resolved with the following precedence:

1. CLI flags
2. Environment variables (`SCOUT_*`)
3. `scout.config.yaml`
4. Built-in defaults

### Environment Variables

| Variable | Description |
|---|---|
| `SCOUT_OUTPUT_DIR` | Output directory |
| `SCOUT_MODE` | Summary mode (`no-llm` or `llm`) |
| `SCOUT_PROVIDER` | LLM provider |
| `SCOUT_CRAWL_DELAY_MS` | Crawl delay in milliseconds |
| `SCOUT_MAX_PAGES` | Maximum pages to scan |
| `SCOUT_LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### Config File

```yaml
output_dir: ./reports
mode: no-llm
crawl_delay_ms: 1000
max_pages: 25
log_level: WARNING
```

## Output Files

When `--output` is `json` or `both`:
- `scan-result.json` in the output directory

When `--output` is `markdown` or `both`:
- `report.md` in the output directory
