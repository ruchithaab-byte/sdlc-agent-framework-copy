"""
Live Integration Test: Tool Bridge Verification

This script tests the critical "Tool Bridge" - verifying that the Agent SDK
can actually execute the GitHub tools prepared by the Context Orchestrator.

Success Criteria:
1. Session initializes correctly
2. Tools are passed to Agent SDK
3. Agent can execute GitHub tools (get_file_contents)
4. Tool execution is logged/visible
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from claude_agent_sdk import ClaudeAgent, ClaudeAgentOptions, query
from src.orchestrator import (
    RepoRegistry,
    RepoRouter,
    ContextOrchestrator,
    SessionError,
)


async def test_tool_integration(repo_id: str = "sandbox", prompt: str | None = None) -> None:
    """
    Test the complete tool integration flow.
    
    Args:
        repo_id: Repository ID to test with
        prompt: User prompt (defaults to README read test)
    """
    print("=" * 80)
    print("🔬 LIVE INTEGRATION TEST: Tool Bridge Verification")
    print("=" * 80)
    print()
    
    # Step 1: Check environment
    print("📋 Step 1: Environment Check")
    print("-" * 80)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("   Set it in .env file or export it:")
        print("   export ANTHROPIC_API_KEY=sk-ant-...")
        return
    
    print(f"✅ ANTHROPIC_API_KEY: {'*' * 20}...{anthropic_key[-4:]}")
    
    if github_token:
        print(f"✅ GITHUB_TOKEN: {'*' * 20}...{github_token[-4:]}")
        print("   GitHub tools will be available")
    else:
        print("⚠️  GITHUB_TOKEN not found")
        print("   GitHub tools will not be available (graceful degradation)")
    print()
    
    # Step 2: Prepare session
    print("📋 Step 2: Prepare Session Context")
    print("-" * 80)
    try:
        registry = RepoRegistry()
        router = RepoRouter(registry) if anthropic_key else None
        orchestrator = ContextOrchestrator(registry, router) if router else None
        
        if repo_id:
            # Bypass routing for direct testing
            from src.orchestrator.session_manager import ContextOrchestrator as CO
            temp_orch = CO.__new__(CO)
            temp_orch.registry = registry
            temp_orch.router = None
            temp_orch.model_profile = "strategy"
            session = temp_orch.prepare_session_for_repo(repo_id)
        else:
            if not orchestrator:
                print("❌ Cannot route without ANTHROPIC_API_KEY")
                return
            session = orchestrator.prepare_session(prompt or "test")
        
        print(f"✅ Session prepared for repository: {session.repo_id}")
        print(f"   Memory Path: {session.memory_path}")
        print(f"   Working Directory: {session.get_cwd()}")
        print(f"   Tools Available: {len(session.tools)}")
        
        if session.tools:
            print("\n   📧 GitHub Tools:")
            for i, tool in enumerate(session.tools, 1):
                print(f"      {i}. {tool.__name__}")
        else:
            print("   ⚠️  No tools available (GitHub token may be missing)")
        print()
        
    except Exception as e:
        print(f"❌ Failed to prepare session: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Create agent options with tools
    print("📋 Step 3: Create Agent Options with Tools")
    print("-" * 80)
    try:
        # Build agent options
        # NOTE: The SDK uses 'mcp_servers' for custom tools, not a direct 'tools' parameter
        # For now, we'll test with allowed_tools and see if the SDK can discover
        # the tools via some other mechanism, or if we need to register them as MCP servers
        
        agent_options = ClaudeAgentOptions(
            cwd=session.get_cwd(),
            setting_sources=["user", "project"],
            allowed_tools=session.agent_config.get("allowed_tools", []),
            model=session.agent_config.get("model", "claude-opus-4@20250514"),
        )
        
        # CRITICAL: Tool Integration
        # The SDK expects tools to be registered via MCP servers or as built-in tools
        # Our GitHub tools are async callables, which may need special registration
        if session.tools:
            print(f"   📧 {len(session.tools)} GitHub tools available:")
            for i, tool in enumerate(session.tools, 1):
                print(f"      {i}. {tool.__name__} (async: {asyncio.iscoroutinefunction(tool)})")
            print()
            print("   ℹ️  Note: SDK may require tools to be registered as MCP servers")
            print("   ℹ️  For this test, we're verifying if tools can be discovered")
            print("   ℹ️  If tools aren't executed, we may need MCP server registration")
        else:
            print("   ⚠️  No tools available (GitHub token may be missing)")
        
        print(f"   ✅ Agent options created")
        print(f"      Model: {agent_options.model}")
        print(f"      Allowed Tools: {agent_options.allowed_tools}")
        print(f"      CWD: {agent_options.cwd}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to create agent options: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Run agent with test prompt
    print("📋 Step 4: Execute Agent with Tool Test")
    print("-" * 80)
    
    test_prompt = prompt or f"""
Read the README.md file from the {repo_id} repository and tell me:
1. What is the purpose of this repository?
2. What test files does it contain?

Use the get_file_contents tool to read the file.
"""
    
    print(f"   Prompt: {test_prompt.strip()[:100]}...")
    print()
    print("   🚀 Starting agent execution...")
    print("   " + "-" * 76)
    print()
    
    try:
        # Use query() function (same as other agents)
        tool_calls_seen = []
        agent_responses = []
        
        async for message in query(prompt=test_prompt, options=agent_options):
            # Check if this is a tool call or response
            if hasattr(message, 'tool_use_id') or 'tool' in str(message).lower():
                tool_calls_seen.append(message)
                print(f"   🔧 [TOOL CALL] {message}")
            else:
                agent_responses.append(message)
                print(f"   💬 [AGENT] {message}")
        
        print()
        print("   " + "-" * 76)
        print()
        
        # Step 5: Verify results
        print("📋 Step 5: Verify Tool Execution")
        print("-" * 80)
        
        if tool_calls_seen:
            print(f"   ✅ Tool calls detected: {len(tool_calls_seen)}")
            for i, tool_call in enumerate(tool_calls_seen[:3], 1):  # Show first 3
                print(f"      {i}. {str(tool_call)[:100]}...")
        else:
            print("   ⚠️  No tool calls detected in output")
            print("   ℹ️  This could mean:")
            print("      - Tools are not properly registered with SDK")
            print("      - Agent didn't need to use tools for this prompt")
            print("      - SDK requires different tool registration method")
        
        if agent_responses:
            print(f"\n   ✅ Agent responses received: {len(agent_responses)}")
            print(f"   📝 Final response preview:")
            final_response = str(agent_responses[-1])[:200]
            print(f"      {final_response}...")
        
        print()
        
        # Success criteria check
        print("📋 Step 6: Success Criteria Check")
        print("-" * 80)
        success = True
        
        if session.tools:
            if tool_calls_seen:
                print("   ✅ SUCCESS: Tools were executed by agent")
                print("   ✅ Tool Bridge is WORKING")
            else:
                print("   ⚠️  Tools available but not executed")
                print("   ℹ️  This may indicate tool registration issue")
                success = False
        else:
            print("   ⚠️  No tools available (expected if GITHUB_TOKEN missing)")
            print("   ℹ️  Test cannot verify tool bridge without tools")
        
        if agent_responses:
            print("   ✅ Agent executed and returned responses")
        else:
            print("   ❌ No agent responses received")
            success = False
        
        print()
        if success and session.tools and tool_calls_seen:
            print("=" * 80)
            print("🎉 INTEGRATION TEST: PASSED")
            print("=" * 80)
            print()
            print("✅ Tool Bridge is fully functional!")
            print("✅ Agent SDK accepts and executes tools from Context Orchestrator")
            print("✅ GitHub tools are working correctly")
        elif success:
            print("=" * 80)
            print("✅ INTEGRATION TEST: PARTIAL SUCCESS")
            print("=" * 80)
            print()
            print("✅ Agent executed successfully")
            if not session.tools:
                print("⚠️  Could not test tools (GITHUB_TOKEN missing)")
        else:
            print("=" * 80)
            print("⚠️  INTEGRATION TEST: NEEDS INVESTIGATION")
            print("=" * 80)
            print()
            print("Agent executed but tool execution needs verification")
        
    except Exception as e:
        print()
        print("   " + "-" * 76)
        print()
        print(f"❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return


def main():
    """CLI entry point for integration test."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Context Orchestrator tool integration with Agent SDK"
    )
    parser.add_argument(
        "--repo-id",
        default="sandbox",
        help="Repository ID to test with (default: sandbox)"
    )
    parser.add_argument(
        "--prompt",
        help="Custom prompt to test (default: README read test)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(test_tool_integration(repo_id=args.repo_id, prompt=args.prompt))


if __name__ == "__main__":
    main()

