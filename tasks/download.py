from os import environ
from invoke import task
import boto3
from unipath import Path
import pandas

BUCKET_NAME = 'words-in-transition'
ALL_FILES = ['words-in-transition.zip',
             'grunt.Message.json']
DOWNLOAD_DIR = Path('downloads')
OUTPUT_DIR = Path('output')

for expected_dir in [DOWNLOAD_DIR, OUTPUT_DIR]:
    if not expected_dir.isdir():
        expected_dir.mkdir()

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

    if 'grunt.Message.json' in files:
        _format_messages()


def _determine_files_to_download(filename, overwrite):
    files = [filename] if filename else ALL_FILES

    for filename in files:
        if Path(DOWNLOAD_DIR, filename).exists() and not overwrite:
            files.remove(filename)

    return files


def _unpack_and_cleanup_zip():
    # Unpack and cleanup zip
    cmds = [
        'unzip words-in-transition.zip',
        'mkdir data/',
        'mv webapps/telephone/media/words-in-transition data/imitations',
        'rm -r webapps'
    ]
    for cmd in cmds:
        run(cmd)


def _format_messages():
    output_columns = ['category', 'seed_id', 'branch_id_list', 'generation',
                      'message_id', 'audio']

    messages = pandas.read_json(Path(DOWNLOAD_DIR, 'grunt.Message.json'))
    field_names = messages.iloc[0].fields.keys()
    for field in field_names:
        messages[field] = messages.fields.apply(lambda x: x[field])
    del messages['fields']

    messages.rename(columns={'pk': 'message_id'}, inplace=True)

    path_data = messages.audio.str.split('/')
    messages['game'] = path_data.str.get(0)
    messages['category'] = path_data.str.get(1)

    messages = messages.ix[messages.game == 'words-in-transition']
    del messages['game']

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

    def find_all_branches(message_id):
        is_in = labeled_branches.message_list.apply(lambda x: message_id in x)
        return labeled_branches.ix[is_in, 'branch_id'].tolist()

    messages['branch_id_list'] = messages.message_id.apply(find_all_branches)

    def find_seed_id(message):
        message_data = messages.ix[messages.message_id == message].squeeze()
        if pandas.isnull(message_data['parent']):
            return message
        else:
            parent = message_data['parent']
            return find_seed_id(parent)

    messages['seed_id'] = messages.message_id.apply(find_seed_id).astype(int)

    messages = messages[output_columns]
    messages.to_csv(Path(OUTPUT_DIR, 'sounds.csv'), index=False)


def _extract_category(path):
    game, category, filename = path.split('/')


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
