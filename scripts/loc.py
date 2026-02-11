from pathlib import Path

roots = ["apps/api", "apps/dashboard", "docs", "scripts"]
for root in roots:
    total = 0
    for file in Path(root).rglob('*'):
        if file.suffix in {'.py', '.ts', '.tsx', '.md', '.sh', '.css'} and file.is_file():
            total += sum(1 for _ in file.open())
    print(f"{root}: {total}")
