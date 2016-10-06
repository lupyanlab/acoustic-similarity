from os import environ
from invoke import task
import boto3
from unipath import Path

BUCKET_NAME = 'words-in-transition'
ALL_FILES = ['words-in-transition.zip',
             'grunt.Message.json']
DOWNLOAD_DIR = Path('downloads')

if not DOWNLOAD_DIR.isdir():
    DOWNLOAD_DIR.mkdir()

@task(help=dict(filename=("The name of the file to download. Defaults to "
                          "downloading all relevant files."),
                profile="The name of the AWS profile to use. Optional.",
                overwrite="Whether to overwrite existing files."))
def download(ctx, filename=None, profile=None, overwrite=False):
    """Download data from the internet."""
    files = _determine_files_to_download(filename, overwrite)

    if profile:
        environ['AWS_PROFILE'] = profile
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)

    for filename in files:
        src = Path(BUCKET_NAME, filename)
        dst = Path(DOWNLOAD_DIR, filename)
        bucket.download_file(src, dst)


def _determine_files_to_download(filename, overwrite):
    files = [filename] if filename else ALL_FILES

    for filename in files:
        if Path(DOWNLOAD_DIR, filename).exists() and not overwrite:
            files.remove(filename)

    return files


def _unpack_and_cleanup_zip(ctx):
    # Unpack and cleanup zip
    cmds = [
        'unzip words-in-transition.zip',
        'mkdir data/',
        'mv webapps/telephone/media/words-in-transition data/imitations',
        'rm -r webapps'
    ]
    for cmd in cmds:
        ctx.run(cmd)
