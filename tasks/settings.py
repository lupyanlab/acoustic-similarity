from unipath import Path

DOWNLOAD_DIR = Path('downloads')
DATA_DIR = Path('data')
SOUNDS_DIR = Path(DATA_DIR, 'sounds')

for expected_dir in [DOWNLOAD_DIR, DATA_DIR, SOUNDS_DIR]:
    if not expected_dir.isdir():
        expected_dir.mkdir()

BUCKET_NAME = 'words-in-transition'
ALL_FILES = ['words-in-transition.zip',
             'grunt.Message.json']
