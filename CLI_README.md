# Squeeze Gateway CLI

Terminal agent for LLM token optimization. Reduces token consumption by 30-60% without quality loss.

## Quick Start

### Installation

```bash
# From PyPI (recommended)
pip install squeeze-gateway

# From source
git clone https://github.com/kirill-skoch/squeeze-gateway.git
cd squeeze-gateway
pip install -e .
```

### Initial Setup

```bash
# Install and configure
sqz install

# Set your Gemini API key
sqz config set api_key YOUR_GEMINI_API_KEY

# Start the gateway
sqz start

# Try interactive chat
sqz chat
```

## Usage

### Commands

#### Installation & Configuration

```bash
# Install CLI and create config directory
sqz install

# Configure settings
sqz config set api_key YOUR_KEY
sqz config set default_mode auto
sqz config list

# View current configuration
sqz config get api_key
```

#### Gateway Management

```bash
# Start gateway (foreground)
sqz start

# Start in background
sqz start --daemon

# Check status
sqz status

# Stop gateway
sqz stop
```

#### Interactive Chat

```bash
# Start chat with default settings
sqz chat

# Specify model and optimization
sqz chat --model gemini-3.6-flash --mode auto --thinking low
```

**Chat Commands:**
- `/exit`, `/quit` - Exit chat
- `/clear` - Clear conversation history
- `/stats` - Show session statistics
- `/mode <auto|cpp|llm|off>` - Change compression mode
- `/thinking <auto|low|medium|high|->` - Change thinking level

#### Statistics

```bash
# View optimization statistics
sqz stats

# Show last 20 requests
sqz stats --limit 20

# Export to file
sqz stats --export stats.json
```

## Configuration

Configuration file: `~/.sqz/config.toml`

```toml
[gateway]
host = "127.0.0.1"
port = 8082
upstream = "https://generativelanguage.googleapis.com"

[optimization]
default_mode = "auto"  # auto, cpp, llm, off
default_thinking = "auto"  # auto, low, medium, high, -
llm_compression_threshold = 2000

[api]
gemini_api_key = "YOUR_KEY"

[models]
default = "gemini-3.6-flash"

[logging]
level = "INFO"
metrics_file = "logs/metrics.jsonl"
```

## Integration Examples

### Python SDK

```python
from squeeze_gateway import SqueezeClient

# Initialize client
client = SqueezeClient(
    api_key="YOUR_KEY",
    mode="auto",
    thinking="auto"
)

# Send request
response = client.chat("Explain quantum entanglement")
print(response.text)
print(f"Tokens saved: {response.tokens_saved}")
```

### Direct HTTP

```python
import requests

response = requests.post(
    "http://localhost:8082/v1beta/models/gemini-3.6-flash:generateContent?squeeze=auto&thinking=auto",
    json={
        "contents": [{
            "role": "user",
            "parts": [{"text": "Hello!"}]
        }]
    }
)

data = response.json()
print(data['candidates'][0]['content']['parts'][0]['text'])
```

### OpenAI Compatibility (Coming Soon)

```python
import openai

openai.api_base = "http://localhost:8082/v1"
openai.api_key = "YOUR_GEMINI_KEY"

response = openai.ChatCompletion.create(
    model="gemini-3.6-flash",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Optimization Modes

### Compression Modes

- `auto` - Automatically choose best compression (recommended)
- `cpp` - Fast C++ heuristic compression (5-36% savings)
- `llm` - LLM-based compression for long prompts (only if >2000 chars)
- `off` - No compression, only thinking control

### Thinking Levels

- `auto` - Automatically adjust based on query complexity (recommended)
- `low` - Minimal reasoning (fast, saves 30-50% on simple queries)
- `medium` - Balanced reasoning
- `high` - Deep reasoning (for complex tasks)
- `-` - Don't interfere with thinking level

## Architecture

```
┌─────────────┐
│   Your App  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│     Squeeze Gateway (sqz)           │
│  ┌────────────────────────────────┐ │
│  │  1. C++ Heuristic Compressor  │ │  ←─ Removes filler, politeness
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  2. Thinking Level Controller │ │  ←─ Adjusts reasoning depth
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  3. LLM Compression (optional)│ │  ←─ For long prompts
│  └────────────────────────────────┘ │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│   Gemini API        │
└─────────────────────┘
```

## Performance

Measured on real traffic with `gemini-3.6-flash` (October 2026):

| Metric | Value |
|--------|-------|
| **Token Savings** | 30-60% |
| **C++ Compression** | 5-36% input reduction |
| **Thinking Control** | Up to 46% on simple queries |
| **Latency Overhead** | <1ms (C++ mode) |
| **Quality Loss** | None (verified blind testing) |

## Troubleshooting

### Gateway won't start

```bash
# Check if port is already in use
lsof -i :8082  # macOS/Linux
netstat -ano | findstr :8082  # Windows

# Start on different port
sqz start --port 8083
```

### API key not working

```bash
# Check configuration
sqz config get api_key

# Reconfigure
sqz config set api_key YOUR_NEW_KEY

# Test connection
sqz status
```

### Chat not connecting

```bash
# Verify gateway is running
sqz status

# Check logs
tail -f logs/metrics.jsonl

# Restart gateway
sqz stop
sqz start
```

## Development

### Build from Source

```bash
git clone https://github.com/kirill-skoch/squeeze-gateway.git
cd squeeze-gateway

# Install dependencies
pip install -e ".[dev]"

# Build C++ extension
cd core
mkdir build && cd build
cmake ..
make
```

### Run Tests

```bash
pytest tests/
```

## License

MIT License - see LICENSE file

## Author

Kirill Skoch (@kirill_skoch)
- GitHub: https://github.com/kirill-skoch
- Telegram: https://t.me/kirill_skoch
