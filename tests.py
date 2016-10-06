from unipath import Path
from tasks import create_mapping_from_chain
from tasks.download import _determine_files_to_download

def test_creating_mapping_from_chain():
    sounds = ('1.wav', '2.wav', '3.wav')
    expected = [('1.wav', '2.wav'), ('2.wav', '3.wav')]
    mapping = create_mapping_from_chain(sounds)
    given = list(mapping)
    assert len(given) == len(expected)
    assert given == expected
