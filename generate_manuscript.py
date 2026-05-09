import os

files = [
    "README.md",
    "chapter_01_setup/README.md",
    "chapter_02_agent_studio/README.md",
    "chapter_03_council/README.md",
    "chapter_04_memory_and_mcp/README.md",
    "chapter_05_trial_by_fire/README.md",
    "chapter_06_governance/README.md",
    "chapter_07_deployment/README.md",
    "chapter_08_wrap_up/README.md"
]

with open("Course_Manuscript.txt", "w") as out:
    out.write("# AI Service Desk: Architecting a Multi-Agent Support Team\n")
    out.write("# Complete Course Manuscript\n\n")
    for f in files:
        if os.path.exists(f):
            with open(f, "r") as inf:
                out.write(f"\n\n{'='*60}\n")
                out.write(f"--- SOURCE: {f} ---\n")
                out.write(f"{'='*60}\n\n")
                
                # Simple replacement of Operations Council
                content = inf.read()
                content = content.replace("Operations Council", "AI Service Desk")
                
                out.write(content)
                out.write("\n\n")
