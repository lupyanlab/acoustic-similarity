import pandas
from unipath import Path

from ..settings import DOWNLOAD_DIR, SOUNDS_DIR


def read_downloaded_messages(game='words-in-transition'):
    """Convert the json dump of message models to a friendly csv."""
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


def label_branch_id_list(messages):
    """Append a column containing ids for all branches each message is in."""
    messages = messages.copy()
    labeled_branches = label_branches(messages)

    def find_all_branches(message_id):
        is_in = labeled_branches.message_list.apply(lambda x: message_id in x)
        return labeled_branches.ix[is_in, 'branch_id'].tolist()

    messages['branch_id_list'] = messages.message_id.apply(find_all_branches)
    return messages


def label_branches(messages):
    """Determine the unique branches in a table of messages."""

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


def label_seed_id(messages):
    """Determine the seed message for each message."""
    messages = messages.copy()

    def find_seed_id(message):
        message_data = messages.ix[messages.message_id == message].squeeze()
        if pandas.isnull(message_data['parent']):
            return message
        else:
            parent = message_data['parent']
            return find_seed_id(parent)

    messages['seed_id'] = messages.message_id.apply(find_seed_id).astype(int)
    return messages


def update_audio_filenames(messages):
    messages = messages.copy()
    messages['audio'] = new_audio_filenames(messages.message_id)
    return messages


def new_audio_filenames(message_ids, absolute=True):
    return message_ids.apply(
        lambda x: Path(SOUNDS_DIR, '{}.wav'.format(x)).absolute()
    ).astype(str)


def get_messages_by_branch():
    messages = read_downloaded_messages()
    messages = update_audio_filenames(messages)
    branches = label_branches(messages)
    expanded = [expand_message_list(branch) for branch in branches.itertuples()]
    labeled = (pandas.concat(expanded, ignore_index=True)
                     .merge(messages))
    labeled = (labeled.sort_values(['branch_id', 'generation'])
                      .reset_index(drop=True))
    return labeled


def expand_message_list(branch):
    expanded = pandas.DataFrame(dict(
        message_id=branch.message_list,
        branch_id=branch.branch_id
    ))
    return expanded


def getattr_null(obj, name, default):
    result = getattr(obj, name)
    return result if not pandas.isnull(result) else default


def message_id_from_wav(x):
    name = Path(x).stem
    try:
        return int(name)
    except ValueError:
        return name
