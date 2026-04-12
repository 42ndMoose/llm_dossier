from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
py = sys.executable
subprocess.run([py, str(ROOT / 'tools' / 'build_source.py')], check=True)
subprocess.run([py, str(ROOT / 'tools' / 'split_dossier.py'), str(ROOT / 'dossier' / 'parts'), str(ROOT / 'dossier' / 'site')], check=True)
subprocess.run([py, str(ROOT / 'tools' / 'build_claims.py'), str(ROOT / 'dossier' / 'source.md'), str(ROOT / 'dossier' / 'site')], check=True)
print('Build complete.')
