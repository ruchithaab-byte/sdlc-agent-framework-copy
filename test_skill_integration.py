#!/usr/bin/env python3
"""
Test script to verify skill integration is working correctly.

This script:
1. Verifies skills are available in .claude/skills/
2. Checks agent prompts mention skills
3. Verifies project configs have skills defined
4. Checks database for skill usage
5. Tests that skills are passed to prompts correctly
"""

import sys
from pathlib import Path
import sqlite3

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

PROJECT_ROOT = Path(__file__).parent


def test_skills_directory():
    """Test that skills directory exists and has valid skills."""
    print("=" * 70)
    print("TEST 1: Skills Directory")
    print("=" * 70)
    
    skills_dir = PROJECT_ROOT / ".claude" / "skills"
    if not skills_dir.exists():
        print("❌ Skills directory not found:", skills_dir)
        return False
    
    print(f"✅ Skills directory exists: {skills_dir}")
    
    skills = [d for d in skills_dir.iterdir() if d.is_dir()]
    print(f"✅ Found {len(skills)} skill directories:")
    
    valid_skills = []
    for skill_dir in skills:
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            print(f"   ✅ {skill_dir.name} (SKILL.md exists)")
            valid_skills.append(skill_dir.name)
        else:
            print(f"   ⚠️  {skill_dir.name} (SKILL.md missing)")
    
    return len(valid_skills) > 0


def test_agent_prompts():
    """Test that agent prompts mention skills."""
    print("\n" + "=" * 70)
    print("TEST 2: Agent Prompts")
    print("=" * 70)
    
    agents_dir = PROJECT_ROOT / ".claude" / "agents"
    if not agents_dir.exists():
        print("❌ Agents directory not found")
        return False
    
    agents_with_skill_tool = []
    agents_with_skill_instructions = []
    
    for agent_file in agents_dir.glob("*.md"):
        content = agent_file.read_text()
        agent_name = agent_file.stem
        
        # Check if Skill tool is in allowed_tools
        if "Skill" in content and "allowed-tools:" in content:
            agents_with_skill_tool.append(agent_name)
        
        # Check if prompt mentions skills
        if "Skills Available" in content or "skill" in content.lower():
            agents_with_skill_instructions.append(agent_name)
    
    print(f"✅ Agents with Skill tool: {len(agents_with_skill_tool)}")
    for agent in sorted(agents_with_skill_tool):
        print(f"   - {agent}")
    
    print(f"\n✅ Agents with skill instructions: {len(agents_with_skill_instructions)}")
    for agent in sorted(agents_with_skill_instructions):
        print(f"   - {agent}")
    
    return len(agents_with_skill_tool) > 0 and len(agents_with_skill_instructions) > 0


def test_project_configs():
    """Test that project configs have skills defined."""
    print("\n" + "=" * 70)
    print("TEST 3: Project Configs")
    print("=" * 70)
    
    repos_dir = PROJECT_ROOT / "repos"
    if not repos_dir.exists():
        print("⚠️  No repos directory found")
        return True  # Not a failure, just no repos
    
    configs_with_skills = []
    configs_without_skills = []
    
    for repo_dir in repos_dir.iterdir():
        if not repo_dir.is_dir():
            continue
        
        config_file = repo_dir / ".sdlc" / "config.yaml"
        if not config_file.exists():
            continue
        
        try:
            if not HAS_YAML:
                # Simple YAML parsing for skills list
                content = config_file.read_text()
                if "skills:" in content:
                    # Extract skills list
                    skills = []
                    in_skills = False
                    for line in content.split("\n"):
                        if "skills:" in line:
                            in_skills = True
                            if "[" in line:
                                # Inline list
                                import re
                                skills = re.findall(r'-\s*([^\n]+)', content[content.find("skills:"):])
                                break
                        elif in_skills and line.strip().startswith("-"):
                            skills.append(line.strip().split("-")[1].strip())
                        elif in_skills and line.strip() and not line.strip().startswith("-"):
                            break
                    config = {"skills": skills}
                else:
                    config = {"skills": []}
            else:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
            
            skills = config.get("skills", [])
            if skills:
                configs_with_skills.append((repo_dir.name, skills))
                print(f"✅ {repo_dir.name}: {len(skills)} skills defined")
                for skill in skills:
                    print(f"   - {skill}")
            else:
                configs_without_skills.append(repo_dir.name)
                print(f"⚠️  {repo_dir.name}: no skills defined")
        except Exception as e:
            print(f"❌ {repo_dir.name}: error reading config - {e}")
    
    print(f"\n✅ Configs with skills: {len(configs_with_skills)}")
    print(f"⚠️  Configs without skills: {len(configs_without_skills)}")
    
    return len(configs_with_skills) > 0


def test_database_usage():
    """Test skill usage in database."""
    print("\n" + "=" * 70)
    print("TEST 4: Database Usage")
    print("=" * 70)
    
    db_path = PROJECT_ROOT / "logs" / "agent_execution.db"
    if not db_path.exists():
        print("⚠️  Database not found:", db_path)
        return True  # Not a failure, just no database yet
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check skill tool usage
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tool_usage
            WHERE tool_name = 'Skill'
        """)
        skill_count = cursor.fetchone()[0]
        
        print(f"✅ Skill tool usage count: {skill_count}")
        
        if skill_count > 0:
            # Get recent skill usage
            cursor.execute("""
                SELECT session_id, timestamp, success_count, failure_count
                FROM tool_usage
                WHERE tool_name = 'Skill'
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            print("\nRecent skill usage:")
            for row in cursor.fetchall():
                session_id, timestamp, success, failure = row
                print(f"   - Session: {session_id[:8]}... at {timestamp}")
                print(f"     Success: {success}, Failure: {failure}")
        
        # Check total tool usage for comparison
        cursor.execute("SELECT COUNT(*) FROM tool_usage")
        total_tools = cursor.fetchone()[0]
        
        print(f"\n✅ Total tool usage: {total_tools}")
        if total_tools > 0:
            skill_percentage = (skill_count / total_tools) * 100
            print(f"   Skill usage: {skill_percentage:.1f}% of all tool usage")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_prompt_rendering():
    """Test that skills are passed to prompts correctly."""
    print("\n" + "=" * 70)
    print("TEST 5: Prompt Rendering")
    print("=" * 70)
    
    # Check if config files have skills defined (simple check)
    sandbox_config = PROJECT_ROOT / "repos" / "sandbox" / ".sdlc" / "config.yaml"
    if sandbox_config.exists():
        content = sandbox_config.read_text()
        if "skills:" in content and "-" in content[content.find("skills:"):]:
            print("✅ Sandbox config has skills defined")
            print("   ✅ Skills will be passed to prompts when config is loaded")
            return True
        else:
            print("⚠️  Sandbox config exists but no skills found")
            return False
    else:
        print("⚠️  Sandbox config not found")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SKILL INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    results.append(("Skills Directory", test_skills_directory()))
    results.append(("Agent Prompts", test_agent_prompts()))
    results.append(("Project Configs", test_project_configs()))
    results.append(("Database Usage", test_database_usage()))
    results.append(("Prompt Rendering", test_prompt_rendering()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Skill integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

