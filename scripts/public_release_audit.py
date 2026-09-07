"""Read-only portfolio audit. Reports filenames/types only, NEVER matched values.

Scans proposed public working files and unique blobs reachable from available refs
and reflogs. Does not stage, publish, delete, rotate secrets or rewrite Git history.
This is heuristic detection, not a guarantee that content is safe to publish.
"""
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PREFIXES = ('memory/', 'test_reports/', '.emergent/', 'checkpoints/', '.screenshots/', 'automation_output/')
GENERATED_PREFIXES = ('frontend/dist/', 'frontend/node_modules/', 'tests/node_modules/', '.venv/')
SECRET_NAMES = ('JWT_SECRET', 'EMERGENT_LLM_KEY', 'OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'MONGO_URL')
PATTERNS = {
    'private-key-material': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'provider-key-shaped-string': re.compile(rb'(?<![\w-])(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}|sk_[A-Za-z0-9]{28,}|AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{25,})'),
    'jwt-shaped-session-token': re.compile(rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{16,}'),
    'credential-in-connection-url': re.compile(rb'(?:mongodb(?:\+srv)?|postgres(?:ql)?|mysql)://[^\s/:]+:[^\s/@]+@'),
}


def git(*args, binary=False):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=not binary)


def ignored(path):
    return subprocess.run(['git', 'check-ignore', '--no-index', '-q', path], cwd=ROOT).returncode == 0


def configured_secrets():
    # Read private values in memory ONLY to check for accidental exact copies.
    values = []
    try:
        from dotenv import dotenv_values
        env = dotenv_values(ROOT / 'backend/.env')
    except ImportError:
        env = {}
    for key in SECRET_NAMES:
        value = env.get(key) or os.environ.get(key, '')
        if value and len(value) >= 16 and not value.startswith('mongodb://localhost') and not value.startswith('mongodb://127.0.0.1'):
            values.append(value.encode())
    return values


def inspect(path, content, scope, exact):
    findings = []
    for issue, pattern in PATTERNS.items():
        if pattern.search(content):
            findings.append({'file': path, 'scope': scope, 'issue_type': issue})
    if any(value in content for value in exact):
        findings.append({'file': path, 'scope': scope, 'issue_type': 'exact-copy-of-configured-private-secret'})
    if path.startswith(PRIVATE_PREFIXES):
        findings.append({'file': path, 'scope': scope, 'issue_type': 'internal-record-or-generated-artifact-review-before-publication'})
    if path.endswith(('.bson', '.dump', '.bundle', '.sqlite', '.tar.gz')) or '/logs/' in path or path.endswith('.log'):
        findings.append({'file': path, 'scope': scope, 'issue_type': 'database-backup-log-or-archive'})
    if path.startswith('test_reports/'):
        findings.append({'file': path, 'scope': scope, 'issue_type': 'test-identities-response-bodies-or-transcript-excerpts-may-be-present'})
    emails = re.findall(rb'[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})', content)
    if any(not domain.lower().endswith((b'example.com', b'example.test', b'repforge.test', b'repforge.dev', b'.invalid')) for domain in emails):
        findings.append({'file': path, 'scope': scope, 'issue_type': 'non-fixture-email-address-review'})
    if re.search(rb'[\"\x27]password[\"\x27]\s*:\s*[\"\x27][^\"\x27\n]{6,}[\"\x27]', content):
        findings.append({'file': path, 'scope': scope, 'issue_type': 'literal-password-or-test-fixture-review'})
    return findings


def main():
    exact = configured_secrets()
    tracked = git('ls-files', '-z').split('\0')
    untracked = git('ls-files', '--others', '--exclude-standard', '-z').split('\0')
    findings, working_count = [], 0
    for path in sorted(set(tracked + untracked)):
        if not path or path.startswith(GENERATED_PREFIXES):
            continue
        file = ROOT / path
        if not file.is_file():
            continue
        # Tracked private artifacts are still potential publication risks despite ignore rules.
        findings.extend(inspect(path, file.read_bytes(), 'working-tree', exact))
        working_count += 1
    commits = set(git('rev-list', '--all').split()) | set(git('reflog', '--all', '--format=%H').split())
    objects = {}
    if commits:
        for line in git('rev-list', '--objects', *sorted(commits)).splitlines():
            oid, _, path = line.partition(' ')
            if path:
                objects.setdefault(oid, path)
    inspected = 0
    # One Git process, values kept in memory; the output contains only labels/filenames.
    if objects:
        output = subprocess.check_output(['git', 'cat-file', '--batch'], input=('\n'.join(objects) + '\n').encode(), cwd=ROOT)
        cursor = 0
        for oid, path in objects.items():
            end = output.index(b'\n', cursor)
            header = output[cursor:end].split()
            size = int(header[2]); cursor = end + 1
            content = output[cursor:cursor+size]; cursor += size + 1
            if header[1] == b'blob':
                findings.extend(inspect(path, content, 'available-git-history', exact)); inspected += 1
    unique = {tuple(sorted(f.items())): f for f in findings}
    sensitive = [f for f in unique.values() if f['issue_type'] in PATTERNS or f['issue_type'] == 'exact-copy-of-configured-private-secret']
    result = {'read_only': True, 'working_files_scanned': working_count, 'available_commits': len(commits),
        'unique_history_blobs_scanned': inspected, 'credential_shaped_findings': len(sensitive),
        'findings': sorted(unique.values(), key=lambda f: (f['file'], f['scope'], f['issue_type'])),
        'private_paths_ignored': {p: ignored(p) for p in ('backend/.env', 'frontend/.env', 'memory/test_credentials.md', 'checkpoints/browser-session.json', 'checkpoints/data-before-hardening/users.bson', 'test_reports/iteration_11.json')},
        'limitations': ['Heuristic patterns can miss secrets and can flag synthetic fixtures.', 'Only local refs/reflogs available here were scanned; remote/unreachable history was not fetched.', 'Git author identity metadata still requires the owner’s review; no identities printed.', 'Ignoring an already tracked file does not remove it from Git history.']}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()