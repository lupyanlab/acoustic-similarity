import pandas
from unipath import Path
from tasks.download import _collapse_branches
from tasks.compare import _expand_message_list, _create_mapping_from_chain


def test_collapse_branch():
    branches = {1: [1], 2: [2, 1], 3: [3, 2, 1]}
    expected_branch = [3, 2, 1]
    collapsed = _collapse_branches(branches)
    assert len(collapsed) == 1
    assert collapsed[0] == expected_branch

def test_collapse_branches():
    branches = {1: [1], 2: [2, 1], 3: [3, 1]}
    expected = [[2, 1], [3, 1]]
    collapsed = _collapse_branches(branches)
    assert len(collapsed) == 2
    assert collapsed == expected

def test_expand_branch():
    branch = pandas.Series(dict(branch_id=1, message_list=[1,2,3,4]))
    expanded = _expand_message_list(branch)
    assert len(expanded) == 4
    assert all(expanded.branch_id == [1] * 4)

def test_creating_mapping_from_chain():
    sounds = ('1.wav', '2.wav', '3.wav')
    expected = [('1.wav', '2.wav'), ('2.wav', '3.wav')]
    mapping = _create_mapping_from_chain(sounds)
    given = list(mapping)
    assert len(given) == len(expected)
    assert given == expected
