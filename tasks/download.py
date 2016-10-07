from os import environ
from invoke import task, run
import boto3
from unipath import Path
import pandas

from .settings import *

@task(help=dict(
    filename=("The name of the file to download. Defaults to "
              "downloading all relevant files."),
    profile="The name of the AWS profile to use. Optional.",
    overwrite="Overwrite existing files? Default is false.",
))
def download(ctx, filename=None, profile=None, overwrite=False):
    """Download the data."""
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
    if 'words-in-transition.zip' in files and overwrite:
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
    label_branch_id_list(messages)
    label_seed_id(messages)
    update_audio_filenames(messages)

    messages = messages[output_columns]
    messages.to_csv(Path(DATA_DIR, 'sounds.csv'), index=False)


def label_branch_id_list(messages):
    labeled_branches = label_branches(messages)

    def find_all_branches(message_id):
        is_in = labeled_branches.message_list.apply(lambda x: message_id in x)
        return labeled_branches.ix[is_in, 'branch_id'].tolist()

    messages['branch_id_list'] = messages.message_id.apply(find_all_branches)


def label_branches(messages):

    def find_messages_on_branch(message, found):
        message_data = messages.ix[messages.message_id == message].squeeze()
        found.append(message_data['message_id'])
        if pandas.isnull(message_data['parent']):
            return found
        else:
            parent = message_data['parent']
            return find_messages_on_branch(parent, found)

    branches = {}
    for message in messages.message_id:
        branches[message] = find_messages_on_branch(message, [])

    unique_branches = collapse_branches(branches)
    labeled_branches = pandas.DataFrame({'message_list': unique_branches})
    labeled_branches['branch_id'] = range(len(labeled_branches))
    return labeled_branches


def label_seed_id(messages):

    def find_seed_id(message):
        message_data = messages.ix[messages.message_id == message].squeeze()
        if pandas.isnull(message_data['parent']):
            return message
        else:
            parent = message_data['parent']
            return find_seed_id(parent)

    messages['seed_id'] = messages.message_id.apply(find_seed_id).astype(int)


def read_downloaded_messages(game='words-in-transition'):
    messages = pandas.read_json(Path(DOWNLOAD_DIR, 'grunt.Message.json'))

    # unfold django model fields
    field_names = messages.iloc[0].fields.keys()
    for field in field_names:
        messages[field] = messages.fields.apply(lambda x: x[field])
    del messages['fields']

    messages.rename(columns={'pk': 'message_id'}, inplace=True)

    path_data = messages.audio.str.split('/')
    messages['game'] = path_data.str.get(0)
    messages['category'] = path_data.str.get(1)

    messages = messages.ix[messages.game == game]
    del messages['game']

    return messages


def collapse_branches(branches):
    all_branches = sorted(branches.values(), key=len, reverse=True)

    def remove_sub_branch(branch):
        if len(branch) > 1:
            sub_branch = branch[1:]
            try:
                all_branches.remove(sub_branch)
            except ValueError:
                pass
            remove_sub_branch(sub_branch)

    for branch in all_branches:
        remove_sub_branch(branch)

    return all_branches


def update_audio_filenames(messages):
    messages['audio'] = new_audio_filenames(messages.message_id)


def new_audio_filenames(message_ids):
    return message_ids.apply(
        lambda x: Path(SOUNDS_DIR, '{}.wav'.format(x)).absolute()
    ).astype(str)


def unpack_and_cleanup_zip():
    # Unpack and cleanup zip
    run('unzip -o {}/words-in-transition.zip'.format(DOWNLOAD_DIR))
    messages = read_downloaded_messages()[['message_id', 'audio']]
    nginx_media_root = 'webapps/telephone/media'
    messages['src'] = messages.audio.apply(lambda x: Path(nginx_media_root, x))
    messages['dst'] = new_audio_filenames(messages.message_id)
    for message in messages.itertuples():
        Path(message.src).move(message.dst)
    run('rm -r webapps')  # remove zip dir
