# CBE 4427 · AI in Chemical Engineering

A Jupyter Book website for Dr. Tianlong (Taylor) Liu, Western University. Adapted from John Kitchin's Spring 2026 course materials.

## Course website

[Open the CBE 4427 course book](https://tlliuca.github.io/AI4ChemEng/)

This repository owns the course materials and publishes the book through GitHub Actions. The initial workflow imports the MIT-licensed source at the recorded commit, applies the CBE 4427 adaptation, and saves the complete notebooks and datasets in this repository. Later builds use this repository's own files.

Students can read the public website without GitHub accounts. Python runs in Colab or local Jupyter. Edits pushed to `main` trigger the book build and publication.

Every notebook page has an **Open in Colab** badge above its title. The build generates each badge from that notebook's path and checks that it opens the matching file in this repository. The toolbar's Colab launcher remains available as well.

The workflow also saves the compiled website at the repository root with `.nojekyll`. This keeps the existing GitHub Pages branch publication and the Actions deployment consistent. Edit the course source under `dsmles`; the root HTML files and asset folders are generated automatically. `.course-published-files.json` records those generated files so updates preserve the source and remove obsolete website files.

## Build locally

With Python 3.12:

```bash
python -m pip install -r requirements-book.txt
python scripts/build_book.py
python -m http.server 8000 --directory dsmles/_build/html
```

Open `http://localhost:8000`. Repository and Colab buttons already point to `tlliuca/AI4ChemEng`. When reusing this book in another repository, set `GITHUB_REPOSITORY` to its `OWNER/NAME` before building.

## Edit your course

| Change | File |
|---|---|
| Welcome page | `dsmles/intro.md` |
| Course information and link to approved outline | `dsmles/course-information.md` |
| Navigation | `dsmles/_toc.yml` |
| Lectures and practice activities | Corresponding `.ipynb` files in `dsmles` |
| Colors | `dsmles/_static/cbe4427.css` |
| Title and book settings | `dsmles/_config.yml` |

Push changes to `main` to update the website. CMU's original syllabus is excluded from the book. Official CBE 4427 requirements have not been invented; insert the approved outline before presenting this as the course syllabus.

The notebooks embed their small datasets and quiz definitions. After editing datasets or quizzes, run `python scripts/prepare_notebooks.py` and commit the updated notebooks. Full local checkouts use local files first.

The site displays saved notebook outputs and refreshed self-check quizzes. The build does **not** execute all scientific examples or optional service integrations. Jupyter Book 1 preserves the source site's layout. Optional AI command activities require a separate compatible assistant; they are not website features.

## Credits

See `UPSTREAM.md`, `upstream/README.org`, and `LICENSE`. Original authorship and license notices are retained. The adaptation does not imply endorsement by the original author or Carnegie Mellon University.
