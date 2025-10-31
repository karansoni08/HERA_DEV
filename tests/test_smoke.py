from pathlib import Path
def test_layout_exists():
    for folder in ["src", "data", "outputs"]:
        assert Path(folder).exists()
