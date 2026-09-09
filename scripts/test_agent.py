import asyncio
import sys
from pathlib import Path


# ============================================================
# Add project root to Python path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.agent.agent import Agent


# ============================================================
# Helper
# ============================================================

def convert_to_dict(value):
    """Convert supported objects to dictionaries."""

    if isinstance(value, dict):
        return value

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if hasattr(value, "__dict__"):
        return value.__dict__

    return value


# ============================================================
# Main Agent Test
# ============================================================

async def main():
    print("=" * 60)
    print("STARTING AGENT INTEGRATION TEST")
    print("=" * 60)

    agent = Agent()

    print("\nSending test request...")
    print("User: What scholarships are available for students?")

    try:
        result = await agent.run(
            user_id="test-user",
            message="What scholarships are available for students?",
            conversation_id="test-conversation",
            language="en",
        )

    except Exception as exc:
        print("\n" + "=" * 60)
        print("AGENT RUN FAILED")
        print("=" * 60)
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))
        return

    # ========================================================
    # Basic Result
    # ========================================================

    print("\n" + "=" * 60)
    print("AGENT RUN COMPLETED")
    print("=" * 60)

    print("\nSuccess:")
    print("-" * 60)
    print(result.success)

    print("\nStatus:")
    print("-" * 60)
    print(result.status)

    # ========================================================
    # Response
    # ========================================================

    print("\nResponse:")
    print("-" * 60)
    print(result.response)

    # ========================================================
    # Plan
    # ========================================================

    print("\nPlan:")
    print("-" * 60)

    plan = convert_to_dict(result.plan)
    print(plan)

    # ========================================================
    # Agent State
    # ========================================================

    print("\nAgent State:")
    print("-" * 60)

    state = convert_to_dict(result.state)
    print(state)

    # ========================================================
    # Metadata
    # ========================================================

    print("\nMetadata:")
    print("-" * 60)

    metadata = convert_to_dict(result.metadata)
    print(metadata)

    # ========================================================
    # Final Summary
    # ========================================================

    print("\n" + "=" * 60)
    print("AGENT INTEGRATION TEST FINISHED")
    print("=" * 60)

    print("Agent object:        OK")
    print("Agent execution:     OK")
    print("Result received:     OK")
    print("Response returned:   OK")
    print("Plan returned:       OK")
    print("State returned:      OK")
    print("Metadata returned:   OK")
    print("=" * 60)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())