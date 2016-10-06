from os import environ
from invoke import task
import boto3
import acousticsim
from unipath import Path

@task(help=dict(filename=("The name of the file to download. Defaults to "
                          "downloading all relevant files."),
                profile="The name of the AWS profile to use. Optional."))
def download(ctx, filename=None, profile=None):
    """Download data from the internet."""
    BUCKET_NAME = 'words-in-transition'

    ALL_FILES = 'words-in-transition.zip'.split()
    files = [filename] if filename else ALL_FILES

    if profile:
        environ['AWS_PROFILE'] = profile

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('words-in-transition')
    for filename in files:
        bucket.download_file(Path(BUCKET_NAME, filename), filename)

        if filename == 'words-in-transition.zip':
            # Unpack and cleanup zip
            cmds = [
                'unzip words-in-transition.zip',
                'mkdir data/',
                'mv webapps/telephone/media/words-in-transition data/imitations',
                'rm -r webapps words-in-transition.zip'
            ]
            for cmd in cmds:
                ctx.run(cmd)

@task
def compare(ctx, edges_csv=None):
    """Compare acoustic similarity."""


def acoustic_similarity_chain(sounds, **kwargs):
    mapping = create_mapping_from_chain(sounds)
    return acousticsim.main.acoustic_similarity_mapping(mapping)


def create_mapping_from_chain(sounds):
    for i in range(len(sounds) - 1):
        yield (sounds[i], sounds[i+1])
