import pandas
from unipath import Path

from tasks.download import collapse_branches
from tasks.compare_sounds import (calculate_similarities, create_single_edge)
from tasks.util import (expand_message_list, get_linear_edges,
                        get_between_category_edges)


def test_collapse_single_branch():
    branches = {1: [1], 2: [2, 1], 3: [3, 2, 1]}
    expected_branch = [3, 2, 1]
    collapsed = collapse_branches(branches)
    assert len(collapsed) == 1
    assert collapsed[0] == expected_branch

def test_collapse_multiple_branches():
    branches = {1: [1], 2: [2, 1], 3: [3, 1]}
    expected = [[2, 1], [3, 1]]
    collapsed = collapse_branches(branches)
    assert len(collapsed) == 2
    assert collapsed == expected

def test_expand_branch():
    branch = pandas.Series(dict(branch_id=1, message_list=[1,2,3,4]))
    expanded = expand_message_list(branch)
    assert len(expanded) == 4
    assert all(expanded.branch_id == [1] * 4)

def test_get_linear_edges():
    branches = pandas.DataFrame(dict(audio=['1.wav', '2.wav', '3.wav']))
    expected = pandas.DataFrame(dict(
        sound_x=['1.wav', '2.wav'],
        sound_y=['2.wav', '3.wav'],
    ))
    edges = get_linear_edges(branches)
    assert len(edges) == len(expected)
    assert all(edges.columns == expected.columns)
    first_edge = edges.iloc[0, 0:2]
    assert all(first_edge == ['1.wav', '2.wav'])

def test_calculate_similarities():
    edges = create_single_edge('fixtures/1.wav', 'fixtures/2.wav')
    similarities = calculate_similarities(edges)
    assert len(similarities) == 1

def test_between_category_edges():
    messages = pandas.DataFrame({
        'category': ['a', 'b'],
        'audio': ['1.wav', '2.wav'],
    })
    edges = get_between_category_edges(messages, n_sample=1)
    assert edges.iloc[0, 0:2].tolist() == ['1.wav', '2.wav']
