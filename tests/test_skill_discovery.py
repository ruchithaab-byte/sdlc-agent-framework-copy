"""Tests for Julley skill discovery and loading.

This test validates that:
1. Skills directory structure is correct
2. All SKILL.md files have proper YAML frontmatter
3. Skills can be discovered by the agent
"""

import os
import yaml
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills" / "julley"


def test_skills_directory_exists():
    """Verify the skills directory exists."""
    assert SKILLS_DIR.exists(), f"Skills directory not found: {SKILLS_DIR}"
    assert SKILLS_DIR.is_dir(), f"Skills path is not a directory: {SKILLS_DIR}"
    print(f"✅ Skills directory exists: {SKILLS_DIR}")


def test_skills_have_skill_md():
    """Verify each skill directory has a SKILL.md file."""
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name != "template"]
    
    assert len(skill_dirs) > 0, "No skill directories found"
    
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.exists(), f"Missing SKILL.md in {skill_dir.name}"
    
    print(f"✅ All {len(skill_dirs)} skills have SKILL.md files")


def test_skill_frontmatter_valid():
    """Verify each SKILL.md has valid YAML frontmatter."""
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name != "template"]
    
    required_fields = ["name", "description", "version"]
    
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()
        
        # Extract frontmatter
        if not content.startswith("---"):
            raise AssertionError(f"{skill_dir.name}: SKILL.md must start with YAML frontmatter (---)")
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise AssertionError(f"{skill_dir.name}: Invalid YAML frontmatter structure")
        
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            raise AssertionError(f"{skill_dir.name}: Invalid YAML in frontmatter: {e}")
        
        # Check required fields
        for field in required_fields:
            assert field in frontmatter, f"{skill_dir.name}: Missing required field '{field}'"
        
        # Validate description length (SDK limit is 1024 chars)
        desc = frontmatter.get("description", "")
        assert len(desc) <= 1024, f"{skill_dir.name}: Description exceeds 1024 chars ({len(desc)})"
    
    print(f"✅ All {len(skill_dirs)} skills have valid YAML frontmatter")


def test_skill_names_match_directories():
    """Verify skill names in frontmatter match directory names."""
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name != "template"]
    
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()
        
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        
        skill_name = frontmatter.get("name", "")
        assert skill_name == skill_dir.name, \
            f"Skill name mismatch: directory '{skill_dir.name}' vs frontmatter name '{skill_name}'"
    
    print(f"✅ All skill names match directory names")


def test_list_all_skills():
    """List all discovered skills with their descriptions."""
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name != "template"]
    skill_dirs.sort(key=lambda d: d.name)
    
    print("\n📚 Discovered Julley Skills:")
    print("-" * 80)
    
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()
        
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        
        name = frontmatter.get("name", "unknown")
        desc = frontmatter.get("description", "No description")[:80]
        version = frontmatter.get("version", "0.0.0")
        
        print(f"  {name} (v{version})")
        print(f"    {desc}...")
        print()
    
    print(f"Total: {len(skill_dirs)} skills")


if __name__ == "__main__":
    print("=" * 80)
    print("JULLEY SKILL DISCOVERY TESTS")
    print("=" * 80)
    print()
    
    test_skills_directory_exists()
    test_skills_have_skill_md()
    test_skill_frontmatter_valid()
    test_skill_names_match_directories()
    test_list_all_skills()
    
    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)


