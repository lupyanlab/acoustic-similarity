import logging

from os import environ
from invoke import task, run
import boto3
from unipath import Path
import pydub

from .edges.messages import (read_downloaded_messages, label_branch_id_list,
                             label_seed_id, update_audio_filenames)
from .settings import *

logger = logging.getLogger(__name__)

@task(help=dict(
    filename=("The name of the file to download. Defaults to "
              "downloading all relevant files."),
    profile="The name of the AWS profile to use. Optional.",
    overwrite="Overwrite existing files? Default is false.",
    verbose="Should all info be printed to stdout?",
))
def download(ctx, filename=None, profile=None, overwrite=False, verbose=False):
    """Download the data from the Telephone app."""
    if verbose:
        logger.setLevel(logging.INFO)

    files = determine_files_to_download(filename, overwrite)

    if profile:
        environ['AWS_PROFILE'] = profile
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)

    for filename in files:
        src = Path(BUCKET_NAME, filename)
        dst = Path(DOWNLOAD_DIR, filename)
        bucket.download_file(src, dst)

    format_messages()
    if 'words-in-transition.zip' in files:
        unpack_and_cleanup_zip()


def determine_files_to_download(filename, overwrite):
    # Create a list of files and remove the ones that exist unless overwriting
    files = [filename] if filename else ALL_FILES

    for filename in files:
        if Path(DOWNLOAD_DIR, filename).exists() and not overwrite:
            files.remove(filename)

    return files


def format_messages():
    # Turn Django model data into a csv of messages with all parts labeled
    output_columns = ['message_id', 'category', 'seed_id', 'branch_id_list',
                      'generation', 'audio']

    messages = read_downloaded_messages()
    messages = label_branch_id_list(messages)
    messages = label_seed_id(messages)
    messages = update_audio_filenames(messages)

    messages = messages[output_columns]
    messages.to_csv(Path(DATA_DIR, 'sounds.csv'), index=False)


def unpack_and_cleanup_zip():
    # Unpack and cleanup zip
    run('unzip -o {}/words-in-transition.zip'.format(DOWNLOAD_DIR))
    messages = read_downloaded_messages()
    nginx_media_root = 'webapps/telephone/media'
    messages['src'] = messages.audio.apply(lambda x: Path(nginx_media_root, x))
    messages['dst'] = new_audio_filenames(messages.message_id)

    for message in messages.itertuples():
        try:
            audio = pydub.AudioSegment.from_wav(message.src)
        except Exception as e:
            logger.warning('Sound {} was not a wav file'.format(message.audio))
            try:
                audio = pydub.AudioSegment.from_mp3(message.src)
            except Exception as e:
                raise e

        # Trim sounds
        start_at = getattr_null(message, 'start_at', 0)
        end_at = getattr_null(message, 'end_at', audio.duration_seconds * 1000)
        trimmed = audio[start_at:end_at]

        if trimmed.duration_seconds < 0.4:
            logger.warning('Sound {} was too short ({} seconds)'.format(
                Path(message.audio).name, trimmed.duration_seconds))

        trimmed.export(message.dst, format='wav')

    run('rm -r webapps')  # remove zip dir
