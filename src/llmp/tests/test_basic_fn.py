

def test_tuple_list_unpacking():
    tuple_list = [(1, "a"), (2, "b"), (3, "c")]
    list_num, list_str = (list(i) for i in zip(*tuple_list))
    assert list_num == [1, 2, 3]
    assert list_str == ["a", "b", "c"]