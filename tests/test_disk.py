from app import disk


def test_empty_folder_removes_contents_and_reports_bytes(tmp_path):
    (tmp_path / "a.bin").write_bytes(b"x" * 10)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.bin").write_bytes(b"y" * 5)

    assert disk.empty_folder(tmp_path) == {"freed_bytes": 15}
    assert list(tmp_path.iterdir()) == []


def test_empty_folder_tolerates_missing_folder(tmp_path):
    assert disk.empty_folder(tmp_path / "nope") == {"freed_bytes": 0}
