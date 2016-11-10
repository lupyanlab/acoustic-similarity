from invoke import task
from unipath import Path
import requests

from .settings import *


@task
def compare_words(ctx, force=False):
    corpus = Path(DOWNLOAD_DIR, 'lemurian.corpus')

    if not corpus.exists():
        lemurian_corpus_url = \
            'https://www.dropbox.com/s/v6jwgym7tc98v4c/lemurian.corpus?dl=1'
        r = requests.get(lemurian_corpus_url)
        open(corpus, 'wb').write(r.content)

    words = Path(WORDS_DIR, 'words.txt')
    if not words.exists() or force:
        ctx.run('Rscript {}'.format(Path(PROJ_ROOT, 'R/select_words.R')))
        assert words.exists(), 'select_words.R didn\'t create words.txt'

    kwargs = dict(corpus=corpus, words=words,
                  algorithm='phonological_edit_distance',
                  output=Path(WORDS_DIR, 'distances.txt'))
    cmd = """
    pct_neighdens {corpus} {words} -a {algorithm} -o {output}
    """
    ctx.run(cmd.format(**kwargs))
