"""
Sprint Review Generator

Automatically generates a comprehensive sprint review report by aggregating
data from Jira (sprint metrics), GitHub (PRs merged), Confluence (docs created),
and Slack (team highlights).

Usage:
    export ANTHROPIC_API_KEY=your_key
    python examples/sprint_review.py --board-id 42 --sprint-name "Sprint 24"
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


def build_sprint_review_prompt(board_id: int, sprint_name: str, repo: str) -> str:
    return f"""
You are a Sprint Review Agent generating a comprehensive sprint report.

## Sprint Details
- Board ID: {board_id}
- Sprint: {sprint_name}
- Repository: {repo}

## Your Tasks

1. **Jira Sprint Data**
   - Get the active sprint info for board {board_id}
   - Search for all completed issues this sprint: JQL `sprint = "{sprint_name}" AND status = Done`
   - Search for any bugs found this sprint: JQL `sprint = "{sprint_name}" AND issuetype = Bug`

2. **GitHub Activity**
   - List recently merged PRs for the {repo} repository
   - Check for any open issues labeled 'bug' in {repo}

3. **Confluence Documentation**
   - Search for any documentation pages updated this sprint
   - List spaces to identify where to publish the report

4. **Generate Sprint Report**
   Post to Slack's #general channel a sprint summary including:
   - Stories completed vs planned
   - Key features shipped (from Jira/GitHub)
   - Bug count and status
   - Team velocity
   - Documentation updates

5. **Final Report**
   Produce a structured markdown sprint review report with sections:
   - Executive Summary
   - Completed Work
   - Technical Highlights (from GitHub)
   - Bugs & Quality
   - Documentation
   - Next Sprint Preview
"""


async def run_sprint_review(
    board_id: int = 1,
    sprint_name: str = "Sprint 1",
    repo: str = "my-service",
) -> None:
    """Run the sprint review generator."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "enterprise_mcp.server"],
    )

    print(f"\n📊 SPRINT REVIEW GENERATOR")
    print(f"   Board ID:    {board_id}")
    print(f"   Sprint:      {sprint_name}")
    print(f"   Repository:  {repo}\n")

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
                    "content": build_sprint_review_prompt(board_id, sprint_name, repo),
                }
            ]

            step = 0
            while step < 30:
                step += 1
                response = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=8192,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if hasattr(block, "text"):
                            print("\n" + "=" * 70)
                            print("📈 SPRINT REVIEW REPORT")
                            print("=" * 70)
                            print(block.text)
                    break

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if hasattr(block, "text") and block.text.strip():
                            print(f"[Agent] {block.text[:200]}")
                        if block.type == "tool_use":
                            print(f"\n→ [{block.name}] {json.dumps(block.input)[:120]}")

                            result = await session.call_tool(block.name, block.input)
                            result_text = result.content[0].text if result.content else "{}"
                            print(f"  ← {result_text[:200]}")

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result_text,
                                }
                            )

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

            print(f"\n✓ Sprint review completed in {step} step(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated sprint review generator")
    parser.add_argument("--board-id", type=int, default=1, help="Jira board ID")
    parser.add_argument("--sprint-name", default="Sprint 1", help="Sprint name")
    parser.add_argument("--repo", default="my-service", help="GitHub repository name")
    args = parser.parse_args()
    asyncio.run(run_sprint_review(args.board_id, args.sprint_name, args.repo))


if __name__ == "__main__":
    main()
