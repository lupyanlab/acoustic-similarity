from invoke import task
import boto3

@task
def download(ctx):
    """Download the imitations."""
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
def compare(ctx):
    """Compare acoustic similarity."""
    pass
