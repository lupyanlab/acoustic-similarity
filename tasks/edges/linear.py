import pandas

from .messages import get_messages_by_branch


def get_linear_edges(branches=None):
    if branches is None:
        branches = get_messages_by_branch()
        branches = branches.ix[(branches.generation > 0) & (~branches.rejected)]

    def _get_linear_edges(branch):
        sounds = branch.audio.tolist()
        edges = []
        for i in range(len(sounds) - 1):
            edges.append((sounds[i], sounds[i+1]))
        return pandas.DataFrame.from_records(edges,
                                             columns=['sound_x', 'sound_y'])

    if 'branch_id' in branches:
        edges = branches.groupby('branch_id').apply(_get_linear_edges)
        edges = edges.reset_index(level=0).reset_index(drop=True)
    else:
        edges = _get_linear_edges(branches)
    return edges
