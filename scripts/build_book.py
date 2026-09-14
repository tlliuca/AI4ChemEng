"""Build the CBE 4427 book and verify all local page and asset references."""
from pathlib import Path
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile

from bs4 import BeautifulSoup
import yaml
from prepare_notebooks import colab_url, prepare

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'dsmles'


def validate(output):
    missing = set()
    launchers = 0
    pages = [p for p in sorted(output.rglob('*.html')) if '_static' not in p.relative_to(output).parts]
    for path in pages:
        soup = BeautifulSoup(path.read_text(), 'html.parser')
        for element in soup.select('[href], [src]'):
            reference = element.get('href') or element.get('src')
            if not reference:
                continue
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.exists():
                missing.add((str(path.relative_to(output)), reference))
        if soup.select('a[href*="colab.research.google.com/github/jkitchin/s26-06642"]'):
            raise RuntimeError('A notebook launch still points to the original course.')
        notebook = BOOK / path.relative_to(output).with_suffix('.ipynb')
        if notebook.is_file():
            buttons = soup.select('article a.cbe-colab-launch')
            if len(buttons) != 1 or buttons[0].get('href') != colab_url(notebook):
                raise RuntimeError('Missing or incorrect visible Colab button: ' + str(path))
            if not buttons[0].select('img[alt="Open in Colab"]'):
                raise RuntimeError('Missing Colab button label: ' + str(path))
            launchers += 1
    if missing:
        for page, reference in sorted(missing):
            print('Missing:', page, reference)
        raise RuntimeError(f'{len(missing)} unresolved local links or assets')
    if not (output / 'searchindex.js').is_file():
        raise RuntimeError('Missing book search index')
    print(f'Validated {len(pages)} HTML pages, {launchers} visible Colab buttons, local links, assets, and search index.')


def main():
    prepare()
    downloads = BOOK / '_static' / 'downloads'
    downloads.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(downloads / 'cbe4427-notebooks.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(BOOK.rglob('*')):
            if not path.is_file() or any(x in path.parts for x in ['_build', '_static', '.ipynb_checkpoints', '.claude']):
                continue
            if path.suffix in ['.ipynb', '.csv', '.txt', '.json']:
                archive.write(path, path.relative_to(ROOT))
        for name in ['requirements-student.txt', 'LICENSE', 'UPSTREAM.md']:
            archive.write(ROOT / name, name)
    config = yaml.safe_load((BOOK / '_config.yml').read_text())
    repository = os.environ.get('GITHUB_REPOSITORY', '').strip()
    if repository:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('GITHUB_REPOSITORY must be OWNER/REPOSITORY')
        config['repository'] = {'url': 'https://github.com/' + repository, 'path_to_book': 'dsmles', 'branch': 'main'}
        config['html'].update(use_repository_button=True, use_edit_page_button=True)
        config['launch_buttons']['colab_url'] = 'https://colab.research.google.com'
        owner, name = repository.split('/')
        default_url = 'https://' + owner.lower() + '.github.io/' + ('' if name.lower() == owner.lower() + '.github.io' else name + '/')
        config['sphinx']['config']['html_baseurl'] = os.environ.get('PAGES_BASE_URL', default_url)
    runtime_config = BOOK / '_config.runtime.yml'
    runtime_config.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    result = subprocess.run([sys.executable, '-c', 'from jupyter_book.cli.main import main; main()', 'build', str(BOOK), '--config', str(runtime_config), '--all'], cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
    output = BOOK / '_build' / 'html'
    (output / '.nojekyll').touch()
    validate(output)
    print('Website ready:', output)


if __name__ == '__main__':
    main()
