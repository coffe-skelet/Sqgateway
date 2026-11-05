"""
Example usage of Squeeze Gateway SDK
"""

import asyncio
from squeeze_sdk import SqueezeClient, CompressionMode, ThinkingLevel


def example_basic():
    """Basic synchronous usage"""
    print("Example 1: Basic Chat\n" + "="*50)

    with SqueezeClient() as client:
        # Check health
        health = client.health_check()
        print(f"Gateway status: {health['status']}")
        print(f"API key configured: {health['key_configured']}\n")

        # Send message
        response = client.chat("Explain quantum entanglement in simple terms")

        print(f"Response: {response.text}\n")

        if response.metrics:
            m = response.metrics
            print(f"Optimization Metrics:")
            print(f"  Mode: {m.mode}")
            print(f"  Input tokens: {m.input_tokens} (baseline: {m.baseline_tokens})")
            print(f"  Tokens saved: {m.saved_tokens} (aux: {m.aux_tokens})")
            print(f"  Net saved: {m.net_saved}")
            print(f"  Thinking: {m.thinking_level} ({m.thinking_tokens} tokens)")
            print(f"  Latency: {m.latency_ms:.0f}ms")


def example_conversation():
    """Multi-turn conversation"""
    print("\n\nExample 2: Multi-turn Conversation\n" + "="*50)

    with SqueezeClient(mode=CompressionMode.CPP, thinking=ThinkingLevel.LOW) as client:
        history = []

        # First message
        response1 = client.chat("What is Python?", history=history)
        print(f"Q: What is Python?")
        print(f"A: {response1.text[:100]}...")

        # Add to history
        history.append({"role": "user", "parts": [{"text": "What is Python?"}]})
        history.append({"role": "model", "parts": [{"text": response1.text}]})

        # Second message
        response2 = client.chat("What are its main features?", history=history)
        print(f"\nQ: What are its main features?")
        print(f"A: {response2.text[:100]}...")

        print(f"\nNet tokens saved: {response2.metrics.net_saved}")


async def example_async():
    """Async usage"""
    print("\n\nExample 3: Async Operations\n" + "="*50)

    async with SqueezeClient() as client:
        # Parallel requests
        tasks = [
            client.chat_async("What is machine learning?"),
            client.chat_async("What is deep learning?"),
            client.chat_async("What is neural network?")
        ]

        responses = await asyncio.gather(*tasks)

        total_saved = sum(r.metrics.net_saved for r in responses)
        print(f"Processed {len(responses)} requests in parallel")
        print(f"Total tokens saved: {total_saved}")


def example_modes():
    """Different optimization modes"""
    print("\n\nExample 4: Optimization Modes\n" + "="*50)

    question = "Please explain to me, if you could, what exactly quantum computing is and how it works?"

    modes = [
        (CompressionMode.OFF, "No compression"),
        (CompressionMode.CPP, "C++ heuristic"),
        (CompressionMode.AUTO, "Auto mode"),
    ]

    with SqueezeClient() as client:
        for mode, label in modes:
            response = client.chat(question, mode=mode)
            print(f"\n{label}:")
            print(f"  Input tokens: {response.metrics.input_tokens}")
            print(f"  Saved: {response.metrics.saved_tokens}")
            print(f"  Net saved: {response.metrics.net_saved}")


def example_stats():
    """Get gateway statistics"""
    print("\n\nExample 5: Gateway Statistics\n" + "="*50)

    with SqueezeClient() as client:
        stats = client.get_stats()

        s = stats.get('stats', {})
        print(f"Total requests: {s.get('requests', 0):,}")
        print(f"Net tokens saved: {s.get('net_tokens_saved', 0):,}")
        print(f"Savings percentage: {s.get('savings_pct', 0):.1f}%")
        print(f"Average latency: {s.get('avg_latency_ms', 0):.0f}ms")


if __name__ == "__main__":
    try:
        # Run sync examples
        example_basic()
        example_conversation()
        example_modes()
        example_stats()

        # Run async example
        asyncio.run(example_async())

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure gateway is running:")
        print("  sqz start")
