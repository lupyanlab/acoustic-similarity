from invoke import task
import boto3
import acousticsim
from path import Path

@task
def download(ctx, filename=None):
    """Download the imitations."""
    ALL_FILES = ['words-in-transition.zip', 'messages']
    files = [filename] if filename else ALL_FILES
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('words-in-transition')
    bucket.download_file(
        'words-in-transition/words-in-transition.zip',
        'words-in-transition.zip'
    )
    ctx.run('unzip words-in-transition.zip')
    ctx.run('mkdir data/ && mv webapps/telephone/media/words-in-transition data/imitations')
    ctx.run('rm -r webapps words-in-transition.zip')

@task
def compare(ctx, edges_csv=None):
    """Compare acoustic similarity."""


def acoustic_similarity_chain(sounds, **kwargs):
    mapping = create_mapping_from_chain(sounds)

def create_mapping_from_chain(sounds):
    for i in range(len(sounds) - 1):
        yield (sounds[i], sounds[i+1])
