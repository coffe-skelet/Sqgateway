"""
Squeeze Gateway CLI - Interactive Chat Mode
Terminal-based chat interface with real-time optimization metrics
"""

import asyncio
import sys
from typing import List, Dict, Optional
import httpx
from datetime import datetime

from .utils import (
    logger,
    print_success,
    print_error,
    print_info,
    print_warning,
    format_number,
)


class InteractiveChat:
    """Interactive terminal chat with Squeeze Gateway"""

    def __init__(self, model: str = "gemini-2.5-flash", mode: str = "auto", thinking: str = "auto", base_url: str = "http://127.0.0.1:8082"):
        self.model = model
        self.mode = mode
        self.thinking = thinking
        self.history: List[Dict] = []
        self.base_url = base_url.rstrip("/")
        self.session_stats = {
            'messages': 0,
            'tokens_saved': 0,
            'total_time': 0.0
        }

    def print_header(self):
        """Print chat header."""
        print("\n" + "=" * 70)
        print("   SQUEEZE GATEWAY - INTERACTIVE CHAT")
        print("=" * 70)
        print(f"  Model: {self.model}")
        print(f"  Compression: {self.mode} | Thinking: {self.thinking}")
        print(f"  Gateway: {self.base_url}")
        print("-" * 70)
        print("  Commands:")
        print("    /exit, /quit      - Exit chat")
        print("    /clear            - Clear conversation history")
        print("    /stats            - Show session statistics")
        print("    /mode <mode>      - Change compression mode (auto/cpp/llm/off)")
        print("    /thinking <level> - Change thinking level (auto/low/medium/high/-)")
        print("-" * 70 + "\n")

    def print_stats(self):
        """Print session statistics."""
        stats = self.session_stats
        print("\n" + "-" * 70)
        print("SESSION STATISTICS")
        print("-" * 70)
        print(f"  Messages sent:     {stats['messages']}")
        print(f"  Tokens saved:      {format_number(stats['tokens_saved'])}")
        print(f"  Total time:        {stats['total_time']:.1f}s")
        if stats['messages'] > 0:
            print(f"  Avg time/message:  {stats['total_time'] / stats['messages']:.1f}s")
        print("-" * 70 + "\n")


    def format_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Print a message and its optional gateway metrics."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if role == "user":
            print(f"\nYou [{timestamp}]")
            print(content)
            print("-" * 70)
        elif role == "assistant":
            print(f"\nAssistant [{timestamp}]")
            print(content)
            if metadata:
                print("-" * 70)
                saved = int(metadata.get("saved", 0))
                aux = int(metadata.get("aux", 0))
                print(f"Mode: {metadata.get('mode_label', 'pass')}")
                print(
                    f"Input: {format_number(metadata.get('input_tokens', 0))}"
                    f" / baseline: {format_number(metadata.get('baseline', 0))}"
                )
                print(f"Saved: {format_number(saved)} | Aux: {format_number(aux)} | Net: {format_number(saved - aux)}")
                print(
                    f"Thinking: {metadata.get('thinking_level', '-')}"
                    f" | Time: {float(metadata.get('latency', 0)):.1f}s"
                )
            print("-" * 70 + "\n")
        elif role == "error":
            print_error(content)


    async def send_message(self, text: str) -> Optional[Dict]:
        """Send message to gateway and get response"""

        # Add to history
        self.history.append({
            "role": "user",
            "parts": [{"text": text}]
        })

        # Build query parameters
        params = {"squeeze": self.mode}
        if self.thinking != "-":
            params["thinking"] = self.thinking

        start_time = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1beta/models/{self.model}:generateContent",
                    params=params,
                    json={"contents": self.history}
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    self.history.pop()
                    return {"error": error_msg}

                data = response.json()
                headers = response.headers

                # Extract response
                answer = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

                if not answer:
                    return {'error': 'Empty response from model'}

                # Add to history
                self.history.append({
                    "role": "model",
                    "parts": [{"text": answer}]
                })

                # Extract metrics
                usage = data.get('usageMetadata', {})
                latency = asyncio.get_event_loop().time() - start_time

                metadata = {
                    'mode_label': self._parse_mode_label(headers.get('x-squeeze-mode', 'passthrough')),
                    'input_tokens': int(headers.get('x-squeeze-input', usage.get('promptTokenCount', 0))),
                    'baseline': int(headers.get('x-squeeze-baseline', 0)),
                    'saved': int(headers.get('x-squeeze-saved', 0)),
                    'aux': int(headers.get('x-squeeze-aux', 0)),
                    'thinking_tokens': usage.get('thoughtsTokenCount', 0),
                    'thinking_level': headers.get('x-squeeze-thinking', 'client'),
                    'latency': float(
                        headers.get(
                            'x-squeeze-elapsed-ms',
                            usage.get('latency_ms', latency * 1000),
                        )
                    ) / 1000
                }

                return {
                    'text': answer,
                    'metadata': metadata
                }

        except httpx.TimeoutException:
            self.history.pop()
            return {'error': 'Request timeout. Gateway may be overloaded.'}
        except httpx.ConnectError:
            self.history.pop()
            return {'error': 'Cannot connect to gateway. Is it running?'}
        except Exception as e:
            self.history.pop()
            return {'error': str(e)}

    def _parse_mode_label(self, mode: str) -> str:
        """Parse mode label from header"""
        if mode == 'squeeze_cpp':
            return 'cpp'
        elif mode == 'squeeze_llm':
            return 'llm'
        else:
            return 'pass'

    def handle_command(self, text: str) -> bool:
        """Handle chat slash commands."""
        command, _, value = text.partition(" ")
        value = value.strip()
        if command in ("/exit", "/quit"):
            self.print_stats()
            print("Goodbye!\n")
            return False
        if command == "/clear":
            self.history.clear()
            self.session_stats = {"messages": 0, "tokens_saved": 0, "total_time": 0.0}
            print("Conversation history cleared\n")
            return True
        if command == "/stats":
            self.print_stats()
            return True
        if command == "/mode":
            if value in ("auto", "cpp", "llm", "off"):
                self.mode = value
                print(f"Compression mode changed to: {value}\n")
            else:
                print_error("Use /mode auto, cpp, llm or off")
            return True
        if command == "/thinking":
            if value in ("auto", "low", "medium", "high", "-"):
                self.thinking = value
                print(f"Thinking level changed to: {value}\n")
            else:
                print_error("Use /thinking auto, low, medium, high or -")
            return True
        if command == "/help":
            self.print_header()
            return True
        print_error(f"Unknown command: {command}")
        return True


    async def run_once(self, text: str) -> int:
        """Send one prompt, print the answer and metrics, then exit."""
        if not text.strip():
            print_error("Prompt is empty")
            return 2
        result = await self.send_message(text)
        if "error" in result:
            self.format_message("error", result["error"])
            return 1
        self.format_message(
            "assistant",
            result["text"],
            result.get("metadata"),
        )
        self.session_stats["messages"] = 1
        return 0

    async def run(self) -> int:
        """Run the interactive terminal chat loop."""
        self.print_header()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            print_error(f"Cannot connect to gateway: {exc}")
            return 1
        if not data.get("key_configured"):
            print_warning("Gemini API key is not configured")
            print_info("Run: sqz config set api_key YOUR_KEY")

        print("Ready. Type /help for commands.\\n")
        while True:
            try:
                user_input = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                self.print_stats()
                print("Goodbye!\\n")
                break
            if not user_input:
                continue
            if user_input.startswith("/"):
                if not self.handle_command(user_input):
                    break
                continue

            result = await self.send_message(user_input)
            if "error" in result:
                self.format_message("error", result["error"])
            else:
                self.format_message(
                    "assistant",
                    result["text"],
                    result.get("metadata"),
                )
                self.session_stats["messages"] += 1
        return 0



