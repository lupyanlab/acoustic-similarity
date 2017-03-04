from unipath import Path

PROJ_ROOT = Path(__file__).ancestor(2).absolute()
DOWNLOAD_DIR = Path(PROJ_ROOT, 'downloads')
DATA_DIR = Path(PROJ_ROOT, 'data')
SOUNDS_DIR = Path(DATA_DIR, 'sounds')
WORDS_DIR = Path(DATA_DIR, 'words')
SIMILARITIES_DIR = Path(DATA_DIR, 'similarities')
EDGES_DIR = Path(DATA_DIR, 'edges')

expected_dirs = [DOWNLOAD_DIR, DATA_DIR, SOUNDS_DIR,
                 SIMILARITIES_DIR, EDGES_DIR]
for expected_dir in expected_dirs:
    if not expected_dir.isdir():
        expected_dir.mkdir()

BUCKET_NAME = 'words-in-transition'
ALL_FILES = ['words-in-transition.zip',
             'grunt.Message.json']
