"""
Enterprise MCP Demo Agent

Demonstrates how Claude uses the Enterprise MCP Server to navigate
a realistic enterprise scenario: handling a production incident.

Usage:
    export ANTHROPIC_API_KEY=your_key
    python examples/agent_demo.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEMO_SCENARIO = """
You are an Enterprise Integration Agent with access to Jira, GitHub, Confluence, and Slack.

A production incident has been reported: the payment service is returning 500 errors.

Please:
1. Search Jira for any open P1/P2 incidents related to the payment service
2. Check GitHub for recent commits to the payment-service repository
3. Look up the incident response runbook in Confluence
4. Post a status update to the #incidents Slack channel

Be thorough and systematic. After each tool call, explain what you found.
"""


async def run_demo() -> None:
    """Run the enterprise agent demo with MCP tooling."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "enterprise_mcp.server"],
        env=None,
    )

    print("Connecting to Enterprise MCP Server…")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tools_response.tools
            ]

            print(f"✓ Connected to Enterprise MCP Server")
            print(f"✓ {len(tools)} tools available")
            print(f"  First 5: {[t['name'] for t in tools[:5]]}\n")

            client = anthropic.Anthropic()
            messages: list[dict] = [{"role": "user", "content": DEMO_SCENARIO}]

            iteration = 0
            while iteration < 20:
                iteration += 1
                response = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=4096,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(f"\n{'='*60}")
                            print("AGENT FINAL REPORT:")
                            print("=" * 60)
                            print(block.text)
                    break

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if hasattr(block, "text") and block.text.strip():
                            print(f"\n[Agent] {block.text[:300]}")
                        if block.type == "tool_use":
                            print(f"\n→ Calling: {block.name}")
                            print(
                                f"  Input: {json.dumps(block.input, indent=2)[:300]}"
                            )

                            result = await session.call_tool(block.name, block.input)
                            result_text = (
                                result.content[0].text if result.content else "{}"
                            )

                            print(f"  Result preview: {result_text[:400]}")

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result_text,
                                }
                            )

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # Unexpected stop reason
                    print(f"Unexpected stop_reason: {response.stop_reason}")
                    break

            print(f"\n✓ Demo completed in {iteration} iteration(s)")


if __name__ == "__main__":
    asyncio.run(run_demo())
