"""Import the licensed source once; subsequent builds use this repository only."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import os
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '3352ef2fb897bc250fcd7b20969217daa8dde42c'
URL = 'https://codeload.github.com/jkitchin/s26-06642/tar.gz/' + COMMIT
SHA256 = 'ac3f88fd84c0649977ff6ede489198a587ea1a6b48066e4bc58e5d044c1f43b4'
MARKER = ROOT / 'upstream' / 'import.json'


def report(imported):
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('imported=' + str(imported).lower() + '\n')


def main():
    if MARKER.exists():
        print('Using the course materials in this repository.')
        report(False)
        return
    with urllib.request.urlopen(URL, timeout=60) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise RuntimeError('Source archive does not match the verified course snapshot.')
    archive_paths = {
        'README.org': 'upstream/README.org',
        'CLAUDE.md': 'upstream/CLAUDE.md',
        'Makefile': 'upstream/Makefile',
        'uv.lock': 'upstream/uv.lock',
        'dsmles/syllabus.ipynb': 'upstream/syllabus.ipynb',
        'dsmles/genindex.md': 'upstream/genindex.md',
        'dsmles/intro.md': 'upstream/intro.md',
        'dsmles/_config.yml': 'upstream/config.yml',
        'dsmles/_toc.yml': 'upstream/toc.yml',
    }
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        for entry in archive.getmembers():
            if not entry.isfile():
                continue
            parts = PurePosixPath(entry.name).parts[1:]
            if not parts or '..' in parts or parts[0] in ['.git', '.github']:
                continue
            relative = '/'.join(parts)
            destination = (ROOT / archive_paths.get(relative, relative)).resolve()
            if ROOT not in destination.parents:
                raise ValueError('Invalid source path')
            # The prepared CBE4427/9133 files take precedence over upstream files.
            if destination.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.extractfile(entry).read())
    intro = ROOT / 'dsmles/00-introduction/introduction.ipynb'
    notebook = json.loads(intro.read_text())
    for cell in notebook['cells']:
        text = ''.join(cell['source'])
        if text.startswith('## Environment Setup'):
            cell['source'] = '## Environment setup\n\nSee [Using the course book](../getting-started.md) for downloading notebooks, running them in Colab, or using JupyterLab locally. Run the setup cells at the start of this notebook before the examples. The course data is included in this copy.\n'
        elif 'R² > 0.95 might indicate overfitting.' in text:
            cell['source'] = text.replace('For chemical engineering applications, R² > 0.9 is often excellent for real data. R² > 0.95 might indicate overfitting.', 'A high R² alone does not establish model quality or overfitting. Compare training and held-out performance, inspect residuals, and check for data leakage and the relevance of the validation split.')
    intro.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n')
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(json.dumps({'source': 'https://github.com/jkitchin/s26-06642', 'commit': COMMIT, 'archive_sha256': SHA256, 'license': 'MIT (declared in upstream/README.org)'}, indent=2) + '\n')
    print('Imported the verified source; CBE4427/9133 customizations retained.')
    report(True)


if __name__ == '__main__':
    main()
