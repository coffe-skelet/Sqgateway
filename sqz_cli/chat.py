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
    format_number,
)


class InteractiveChat:
    """Interactive terminal chat with Squeeze Gateway"""

    def __init__(self, model: str = "gemini-3.6-flash", mode: str = "auto", thinking: str = "auto"):
        self.model = model
        self.mode = mode
        self.thinking = thinking
        self.history: List[Dict] = []
        self.base_url = "http://127.0.0.1:8082"
        self.session_stats = {
            'messages': 0,
            'tokens_saved': 0,
            'total_time': 0.0
        }

    def print_header(self):
        """Print chat header"""
        print("\n" + "═" * 70)
        print("   SQUEEZE GATEWAY - INTERACTIVE CHAT")
        print("═" * 70)
        print(f"  Model: {self.model}")
        print(f"  Compression: {self.mode} | Thinking: {self.thinking}")
        print(f"  Gateway: {self.base_url}")
        print("─" * 70)
        print("  Commands:")
        print("    /exit, /quit      - Exit chat")
        print("    /clear            - Clear conversation history")
        print("    /stats            - Show session statistics")
        print("    /mode <mode>      - Change compression mode (auto/cpp/llm/off)")
        print("    /thinking <level> - Change thinking level (auto/low/medium/high/-)")
        print("─" * 70 + "\n")

    def print_stats(self):
        """Print session statistics"""
        stats = self.session_stats
        print("\n" + "─" * 70)
        print("📊 SESSION STATISTICS")
        print("─" * 70)
        print(f"  Messages sent:     {stats['messages']}")
        print(f"  Tokens saved:      {format_number(stats['tokens_saved'])}")
        print(f"  Total time:        {stats['total_time']:.1f}s")
        if stats['messages'] > 0:
            print(f"  Avg time/message:  {stats['total_time'] / stats['messages']:.1f}s")
        print("─" * 70 + "\n")

    def format_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Format and print message"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if role == "user":
            print(f"\n┌─ You [{timestamp}]")
            print(f"│ {content}")
            print("└" + "─" * 68 + "\n")

        elif role == "assistant":
            print(f"┌─ Assistant [{timestamp}]")
            # Word wrap for long responses
            lines = content.split('\n')
            for line in lines:
                if len(line) <= 66:
                    print(f"│ {line}")
                else:
                    # Simple word wrap
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 66:
                            current_line += word + " "
                        else:
                            print(f"│ {current_line}")
                            current_line = word + " "
                    if current_line:
                        print(f"│ {current_line}")

            # Print optimization metrics
            if metadata:
                print("│")
                print("│ " + "─" * 66)
                print("│ 📈 Optimization Metrics:")

                mode_label = metadata.get('mode_label', 'pass')
                mode_color = {
                    'cpp': '🟢',
                    'llm': '🟣',
                    'pass': '⚪'
                }.get(mode_label, '⚪')

                input_tok = metadata.get('input_tokens', 0)
                baseline = metadata.get('baseline', 0)
                saved = metadata.get('saved', 0)
                aux = metadata.get('aux', 0)
                thinking = metadata.get('thinking_tokens', 0)
                thinking_level = metadata.get('thinking_level', '-')
                latency = metadata.get('latency', 0)

                print(f"│   {mode_color} Mode: {mode_label.upper():<6} │ "
                      f"Input: {format_number(input_tok):<8} / {format_number(baseline):<8} baseline")
                print(f"│   💰 Saved: {format_number(saved):<8} │ "
                      f"Aux: {format_number(aux):<8} │ "
                      f"Net: {format_number(saved - aux):<8}")
                print(f"│   🧠 Thinking: {thinking_level:<6} │ "
                      f"Tokens: {format_number(thinking):<8} │ "
                      f"Time: {latency:.1f}s")

                # Update session stats
                self.session_stats['tokens_saved'] += (saved - aux)
                self.session_stats['total_time'] += latency

            print("└" + "─" * 68 + "\n")

        elif role == "system":
            print(f"ℹ️  {content}\n")

        elif role == "error":
            print(f"❌ Error: {content}\n")

    async def send_message(self, text: str) -> Optional[Dict]:
        """Send message to gateway and get response"""

        # Add to history
        self.history.append({
            "role": "user",
            "parts": [{"text": text}]
        })

        # Build query parameters
        qs = f"?squeeze={self.mode}"
        if self.thinking != "-":
            qs += f"&thinking={self.thinking}"

        start_time = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1beta/models/{self.model}:generateContent{qs}",
                    json={"contents": self.history}
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    return {'error': error_msg}

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
                    'latency': latency
                }

                return {
                    'text': answer,
                    'metadata': metadata
                }

        except httpx.TimeoutException:
            return {'error': 'Request timeout. Gateway may be overloaded.'}
        except httpx.ConnectError:
            return {'error': 'Cannot connect to gateway. Is it running?'}
        except Exception as e:
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
        """Handle special commands. Returns True if should continue."""

        if text in ['/exit', '/quit']:
            self.print_stats()
            print("👋 Goodbye!\n")
            return False

        elif text == '/clear':
            self.history.clear()
            self.session_stats = {'messages': 0, 'tokens_saved': 0, 'total_time': 0.0}
            print("✅ Conversation history cleared\n")
            return True

        elif text == '/stats':
            self.print_stats()
            return True

        elif text.startswith('/mode '):
            new_mode = text.split(' ', 1)[1].strip()
            if new_mode in ['auto', 'cpp', 'llm', 'off']:
                self.mode = new_mode
                print(f"✅ Compression mode changed to: {new_mode}\n")
            else:
                print(f"❌ Invalid mode. Use: auto, cpp, llm, or off\n")
            return True

        elif text.startswith('/thinking '):
            new_thinking = text.split(' ', 1)[1].strip()
            if new_thinking in ['auto', 'low', 'medium', 'high', '-']:
                self.thinking = new_thinking
                print(f"✅ Thinking level changed to: {new_thinking}\n")
            else:
                print(f"❌ Invalid thinking level. Use: auto, low, medium, high, or -\n")
            return True

        return True  # Continue for non-command text

    async def run(self) -> int:
        """Run interactive chat loop"""

        self.print_header()

        # Check gateway health
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                data = response.json()

                if data.get('status') != 'ok':
                    print_error("Gateway is not healthy")
                    return 1

                if not data.get('key_configured'):
                    print("⚠️  Warning: Gemini API key not configured")
                    print("   Configure with: sqz config set api_key YOUR_KEY\n")

        except Exception as e:
            print_error(f"Cannot connect to gateway: {e}")
            print_info("Start gateway with: sqz start")
            return 1

        print("🚀 Ready! Type your message or /help for commands.\n")

        # Main chat loop
        try:
            while True:
                # Get user input
                try:
                    user_input = input("You > ").strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Display user message
                self.format_message("user", user_input)

                # Show thinking indicator
                print("⏳ Gateway optimizing and processing...", end='', flush=True)

                # Send message and get response
                result = await self.send_message(user_input)

                # Clear thinking indicator
                print('\r' + ' ' * 50 + '\r', end='', flush=True)

                if 'error' in result:
                    self.format_message("error", result['error'])
                else:
                    self.format_message("assistant", result['text'], result.get('metadata'))
                    self.session_stats['messages'] += 1

        except KeyboardInterrupt:
            print("\n\n⚡ Interrupted\n")
            self.print_stats()

        return 0
