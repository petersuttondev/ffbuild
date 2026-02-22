import pytest

import ffbuild


def test_check_name_valid():
    name = 'name'
    assert ffbuild.check_name(name) == name


def test_check_name_invalid():
    with pytest.raises(ValueError):
        ffbuild.check_name('@')


def test_value_repr():
    value = ffbuild.Value('a')
    assert repr(value) == "Value('a')"


def test_value_eq():
    v1 = ffbuild.Value('a')
    v2 = ffbuild.Value('a')
    assert v1 == v2
    assert hash(v1) == hash(v2)


def test_value_ne():
    v1 = ffbuild.Value('a')
    v2 = ffbuild.Value('b')
    assert v1 != v2


@pytest.mark.parametrize('special_char', ffbuild.SPECIAL_CHARS)
def test_value_contains_special_chars(special_char):
    v = ffbuild.Value(special_char)
    assert v.contains_special_chars


def test_value_not_contains_special_chars():
    v = ffbuild.Value('a')
    assert not v.contains_special_chars


def test_value_int():
    v = ffbuild.Value(1)
    assert str(v) == '1'


def test_value_str():
    v = ffbuild.Value('a')
    assert str(v) == 'a'


def test_value_str_open_square_bracket():
    v = ffbuild.Value('[')  # ]
    assert str(v) == r'\['  # ]


def test_value_str_close_square_bracker():
    v = ffbuild.Value(']')
    assert str(v) == r'\]'


def test_value_str_equals():
    v = ffbuild.Value('=')
    assert str(v) == r'\='


def test_value_str_semi_colon():
    v = ffbuild.Value(';')
    assert str(v) == r'\;'


def test_value_str_comma():
    v = ffbuild.Value(',')
    assert str(v) == r'\,'


def test_value_str_slash():
    v = ffbuild.Value('\\')  # \
    assert str(v) == '\\'  # \


def test_value_str_slash_with_special_char():
    v = ffbuild.Value('=\\')
    assert str(v) == r'\=\\'  # \=\\


def test_complex_1():
    graph = ffbuild.FilterGraph()
    (split,) = graph.append_filter('split', input='0:v', output=('a', 'b'))
    link_a, link_b = split.output
    graph.append_filter('select', 'eq(n, 0)', input=link_a, output='c')
    graph.append(
        ffbuild.Filter('trim', start_frame=10, end_frame=150, input=link_b),
        ffbuild.Filter('scale', 1280, -1, output='d'),
    )
    assert (
        str(graph)
        == r"""[0:v]split[a][b];[a]select='eq(n\, 0)'[c];[b]trim=start_frame=10:end_frame=150,scale=1280:-1[d]"""
    )
