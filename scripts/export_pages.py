"""Keep GitHub Pages' branch source in sync with the compiled course book."""
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dsmles' / '_build' / 'html'
MANIFEST = '.course-published-files.json'
PROTECTED = {'.git', '.github', '.gitignore', 'dsmles', 'scripts', 'upstream',
             'README.md', 'LICENSE', 'UPSTREAM.md', 'requirements-book.txt',
             'requirements-student.txt', MANIFEST}


def check_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] in PROTECTED:
        raise ValueError(f'Invalid generated website path: {name}')
    target = ROOT / name
    if not target.resolve().is_relative_to(ROOT):
        raise ValueError(f'Website path escapes the repository: {name}')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', action='store_true', help='Stage generated website files in git')
    args = parser.parse_args()
    for name in ['index.html', 'intro.html', 'searchindex.js', '.nojekyll']:
        if not (OUTPUT / name).is_file():
            raise RuntimeError(f'Build the book before publishing: missing {name}')
    manifest = ROOT / MANIFEST
    previous = set(json.loads(manifest.read_text())['files']) if manifest.exists() else set()
    current = {p.relative_to(OUTPUT).as_posix() for p in OUTPUT.rglob('*') if p.is_file()}
    for name in current | previous:
        target = check_path(name)
        if name in current and name not in previous and target.exists():
            raise RuntimeError(f'Refusing to overwrite a non-generated repository file: {name}')
    for name in sorted(previous - current):
        check_path(name).unlink(missing_ok=True)
    for name in sorted(current):
        target = check_path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUTPUT / name, target)
    manifest.write_text(json.dumps({'version': 1, 'files': sorted(current)}, indent=2) + '\n')
    if args.stage:
        subprocess.run(['git', 'add', '--all', '--', MANIFEST, *sorted(current | previous)], cwd=ROOT, check=True)
    print(f'Exported {len(current)} generated files for GitHub Pages branch publishing.')


if __name__ == '__main__':
    main()
