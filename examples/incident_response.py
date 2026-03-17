"""
Incident Response Automation

Demonstrates an automated incident triage workflow using the Enterprise MCP Server.
The agent:
  1. Identifies the incident in Jira
  2. Correlates with recent GitHub commits
  3. Pulls the runbook from Confluence
  4. Coordinates response via Slack

Usage:
    export ANTHROPIC_API_KEY=your_key
    python examples/incident_response.py --service payment-service --severity P1
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def build_incident_prompt(service: str, severity: str, description: str) -> str:
    return f"""
You are an on-call incident response agent with access to Jira, GitHub, Confluence, and Slack.

## Incident Details
- Service: {service}
- Severity: {severity}
- Description: {description}
- Time: {__import__('datetime').datetime.utcnow().isoformat()}Z

## Your Mission
Perform a complete incident triage:

1. **Jira**: Search for existing {severity} incidents for '{service}'. If none found, create one.
2. **GitHub**: List recent commits and open PRs for the '{service}' repository to identify potential causes.
3. **Confluence**: Search for the incident response runbook for '{service}'.
4. **Slack**: Post an incident update to #incidents with:
   - Incident summary
   - Potential root causes from GitHub
   - Link to the runbook
   - Next steps

Provide a structured incident report at the end with:
- Root cause hypothesis
- Immediate actions taken
- Recommended next steps
- ETA for resolution
"""


async def run_incident_response(
    service: str = "payment-service",
    severity: str = "P1",
    description: str = "Service returning 500 errors on checkout flow",
) -> None:
    """Run an automated incident response workflow."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "enterprise_mcp.server"],
    )

    print(f"\n🚨 INCIDENT RESPONSE INITIATED")
    print(f"   Service:  {service}")
    print(f"   Severity: {severity}")
    print(f"   Issue:    {description}\n")

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

            print(f"✓ MCP Server connected — {len(tools)} tools available\n")

            client = anthropic.Anthropic()
            messages: list[dict] = [
                {
                    "role": "user",
                    "content": build_incident_prompt(service, severity, description),
                }
            ]

            step = 0
            while step < 25:
                step += 1
                response = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=4096,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if hasattr(block, "text"):
                            print("\n" + "=" * 70)
                            print("📋 INCIDENT REPORT")
                            print("=" * 70)
                            print(block.text)
                    break

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if hasattr(block, "text") and block.text.strip():
                            print(f"[Agent] {block.text[:200]}")
                        if block.type == "tool_use":
                            icon = _tool_icon(block.name)
                            print(f"\n{icon} {block.name}")
                            print(f"   → {json.dumps(block.input)[:150]}")

                            result = await session.call_tool(block.name, block.input)
                            result_text = result.content[0].text if result.content else "{}"
                            print(f"   ← {result_text[:200]}")

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result_text,
                                }
                            )

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})


def _tool_icon(tool_name: str) -> str:
    if tool_name.startswith("jira"):
        return "📋"
    elif tool_name.startswith("github"):
        return "🐙"
    elif tool_name.startswith("confluence"):
        return "📚"
    elif tool_name.startswith("slack"):
        return "💬"
    return "🔧"


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated incident response agent")
    parser.add_argument("--service", default="payment-service", help="Affected service name")
    parser.add_argument("--severity", default="P1", choices=["P1", "P2", "P3"], help="Incident severity")
    parser.add_argument(
        "--description",
        default="Service returning 500 errors on checkout flow",
        help="Incident description",
    )
    args = parser.parse_args()
    asyncio.run(run_incident_response(args.service, args.severity, args.description))


if __name__ == "__main__":
    main()
