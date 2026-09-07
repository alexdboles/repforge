"""Read-only artifact/link/placeholder checks; no app/provider operations."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['README.md', 'PORTFOLIO_CHECKLIST.md', 'docs/DEMO_GUIDE.md', 'docs/ARCHITECTURE.md',
    'docs/VALIDATION.md', 'docs/PROJECT_STATUS.md', 'docs/PUBLIC_RELEASE_AUDIT.md',
    'docs/images/landing-demo.jpg', 'docs/images/simulation-demo.jpg', 'docs/images/coaching-demo.jpg',
    'backend/.env.example', 'frontend/.env.example']


def main():
    for name in REQUIRED:
        assert (ROOT / name).is_file(), f'Missing artifact: {name}'
    readme = (ROOT / 'README.md').read_text()
    assert readme.startswith('# RepForge') and 'bare skeleton' not in readme
    assert 'https://www.therepforge.app/' in readme and 'Emergent' in readme
    assert '```mermaid' in (ROOT / 'docs/ARCHITECTURE.md').read_text()
    docs = [ROOT / 'README.md', ROOT / 'PORTFOLIO_CHECKLIST.md', *list((ROOT / 'docs').glob('*.md'))]
    for doc in docs:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            assert (doc.parent / target.split('#')[0]).exists(), f'Broken local link: {doc.name} -> {target}'
    for name in ('OPENAI_API_KEY', 'EMERGENT_LLM_KEY', 'ELEVENLABS_API_KEY'):
        assert f'{name}=\n' in (ROOT / 'backend/.env.example').read_text() + '\n'
    assert not (ROOT / 'frontend/.env.example').read_text().strip(), 'Frontend needs no environment secrets'
    from PIL import Image
    for name in REQUIRED:
        if name.endswith('.jpg'):
            with Image.open(ROOT / name) as image:
                image.verify()
    print(f'PASS: {len(REQUIRED)} required artifacts, local documentation links, Mermaid, empty provider placeholders and image integrity')


if __name__ == '__main__':
    main()