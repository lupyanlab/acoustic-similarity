from unipath import Path
from tasks import create_mapping_from_chain
from tasks.download import _determine_files_to_download, collapse_branches

def test_creating_mapping_from_chain():
    sounds = ('1.wav', '2.wav', '3.wav')
    expected = [('1.wav', '2.wav'), ('2.wav', '3.wav')]
    mapping = create_mapping_from_chain(sounds)
    given = list(mapping)
    assert len(given) == len(expected)
    assert given == expected

def test_collapse_branch():
    branches = {1: [1], 2: [2, 1], 3: [3, 2, 1]}
    expected_branch = [3, 2, 1]
    collapsed = collapse_branches(branches)
    assert len(collapsed) == 1
    assert collapsed[0] == expected_branch

def test_collapse_branches():
    branches = {1: [1], 2: [2, 1], 3: [3, 1]}
    expected = [[2, 1], [3, 1]]
    collapsed = collapse_branches(branches)
    assert len(collapsed) == 2
    assert collapsed == expected
