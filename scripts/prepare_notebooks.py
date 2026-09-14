"""Refresh portable course resources and browser quizzes without executing lessons."""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import zlib

import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from jupyterquiz import display_quiz

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'dsmles'
RAW = 'https://raw.githubusercontent.com/jkitchin/s26-06642/main/dsmles/'
PACKAGES = '"numpy<2.4" pandas matplotlib scikit-learn pycse shap xgboost umap-learn jupyterquiz==2.9.6.2 uncertainties'


def prepare():
    InteractiveShell.instance()
    count = quizzes = 0
    for path in sorted(BOOK.rglob('*.ipynb')):
        if '_build' in path.parts or '.ipynb_checkpoints' in path.parts:
            continue
        notebook = nbformat.read(path, as_version=4)
        cells = []
        for cell in notebook.cells:
            if cell.metadata.get('cbe_generated'):
                continue
            source = cell.source
            if cell.cell_type == 'markdown' and source.strip().startswith('[![Open In Colab]'):
                continue
            if cell.cell_type == 'code' and 'uv pip install' in source and 's26-06642' in source:
                continue
            if cell.cell_type == 'code':
                if 'base_url =' in source and RAW in source and 'urlretrieve' in source:
                    source = ('# Copy the included example data into the working folder.\n'
                              'import shutil\n'
                              'for name in ["reactor_data.csv", "catalyst_experiments.txt"]:\n'
                              '    shutil.copyfile(course_file("data/" + name), name)\n'
                              'print("Example data ready.")')
                    cell.outputs = []
                source = re.sub(r'([\"\'])' + re.escape(RAW) + r'([^\"\']+)\1',
                                lambda m: 'course_file(' + repr(m[2]) + ')', source)
                source = source.replace('import urllib.request', 'import shutil') if 'urllib.request.urlretrieve' in source else source
                source = source.replace('urllib.request.urlretrieve', 'shutil.copyfile')
                source = re.sub(r'display_quiz\(([\"\'])(quizzes/[^\"\']+)\1\)',
                                lambda m: 'display_quiz(course_file(' + repr(str(path.parent.relative_to(BOOK) / m[2])) + '))', source)
            cell.source = source
            if cell.cell_type != 'code':
                cell.pop('outputs', None)
                cell.pop('execution_count', None)
            cells.append(cell)

        text = '\n'.join(c.source for c in cells)
        names = set(re.findall(r'course_file\(([\"\'])([^\"\']+)\1\)', text))
        resources = {name for _, name in names}
        if path.parent.name == '01-numpy':
            resources.update(['data/reactor_data.csv', 'data/catalyst_experiments.txt'])
        # All small existing local input files mentioned in this notebook.
        for _, name in re.findall(r'([\"\'])([^\"\'\n]+\.(?:csv|txt|json))\1', text):
            p = path.parent / name
            if not name.startswith(('http:', 'https:')) and p.is_file() and BOOK in p.resolve().parents:
                resources.add(str(p.resolve().relative_to(BOOK)))
        contents = {name: (BOOK / name).read_text() for name in sorted(resources)}
        payload = base64.b64encode(zlib.compress(json.dumps(contents).encode(), 9)).decode()
        bootstrap = '''# Included CBE 4427 data; no original-course server is contacted.
from pathlib import Path
import base64, json, tempfile, zlib
_course_embedded = json.loads(zlib.decompress(base64.b64decode(PAYLOAD)))
_course_cache = Path(tempfile.mkdtemp(prefix="cbe4427-"))
def course_file(name):
    """Use a local course file, or the copy embedded in this notebook."""
    for root in [Path.cwd(), *Path.cwd().parents]:
        for candidate in [root / "dsmles" / name, root / name]:
            if candidate.is_file():
                return str(candidate)
    if name not in _course_embedded:
        raise FileNotFoundError("Course resource not included: " + name)
    target = (_course_cache / name).resolve()
    if _course_cache not in target.parents:
        raise ValueError("Invalid course resource path")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(_course_embedded[name])
    return str(target)
'''.replace('PAYLOAD', repr(payload))
        extra = ''
        if 'import jaxsr' in text or 'from jaxsr' in text:
            extra += ' jaxsr'
        if path.name == 'deep-learning.ipynb':
            extra += ' torch'
        if path.name == 'symbolic-regression.ipynb':
            extra += ' pysr'
        setup = nbformat.v4.new_code_cell('# Run this cell first in a fresh notebook environment.\n%pip install -q ' + PACKAGES + extra,
                metadata={'cbe_generated': True, 'tags': ['remove-cell']})
        data_cell = nbformat.v4.new_code_cell(bootstrap,
                metadata={'cbe_generated': True, 'tags': ['remove-cell']})
        prefix = [setup, data_cell]
        if path.parent.name in ['assignments', 'participation']:
            prefix.append(nbformat.v4.new_markdown_cell('```{note}\nPractice resource for CBE 4427. Your instructor specifies assigned activities, deadlines, submission requirements, and assessment criteria. Example points or rubrics below are part of the practice material.\n```', metadata={'cbe_generated': True}))
        for cell in cells:
            if cell.cell_type != 'code' or 'display_quiz(' not in cell.source:
                continue
            match = re.search(r'display_quiz\(course_file\(([\"\'])([^\"\']+)\1\)\)', cell.source)
            if not match:
                raise ValueError('Unresolved quiz: ' + str(path))
            questions = json.loads((BOOK / match[2]).read_text())
            state = random.getstate()
            random.seed(str(path.relative_to(BOOK)))
            with capture_output() as output:
                display_quiz(questions, max_width=760, colors={'--jq-multiple-choice-bg': '#4f2683'})
            random.setstate(state)
            cell.outputs = [nbformat.v4.new_output('display_data', data=o.data, metadata=o.metadata) for o in output.outputs]
            cell.execution_count = None
            cell.metadata.setdefault('tags', [])
            if 'remove-input' not in cell.metadata.tags:
                cell.metadata.tags.append('remove-input')
            quizzes += 1
        notebook.cells = prefix + cells
        notebook.nbformat_minor = max(5, notebook.nbformat_minor)
        # Stable cell IDs keep builds and changes easy to review.
        for i, cell in enumerate(notebook.cells):
            if not cell.get('id') or cell.metadata.get('cbe_generated'):
                cell.id = hashlib.sha256((str(path.relative_to(BOOK)) + ':' + str(i)).encode()).hexdigest()[:12]
        nbformat.validate(notebook)
        nbformat.write(notebook, path)
        count += 1
    print(f'Prepared {count} notebooks and {quizzes} self-check quizzes.')


if __name__ == '__main__':
    prepare()
