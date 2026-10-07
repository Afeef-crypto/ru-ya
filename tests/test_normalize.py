from ru_ya.ingest.normalize import normalize_arabic


def test_strip_diacritics_and_unify_alef():
    assert normalize_arabic("أَحْمَد") == "احمد"
    assert "َ" not in normalize_arabic("الرُّؤْيَا")
