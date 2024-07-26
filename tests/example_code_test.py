import pytest
import runpy
import shutil
from pathlib import Path


@pytest.mark.parametrize(
    ("example_code", "output_file"),
    (
        ("example_automated_sip_creation.py",
         "result/example-automated-sip.tar"),
        ("example_manual_sip_creation.py",
         "result/example-manual-sip.tar")
    )
)
def test_example_automated_sip_creation(example_code, output_file,
                                        monkeypatch, tmpdir):
    """Test that example codes run without error."""
    # Copy doc source files to a temporary location to avoid accidentally
    # modifying the original directory if the test crashes for some reason
    doc_path = Path(tmpdir / "doc")
    test_path = Path(tmpdir / "tests" / "data")

    shutil.copytree("doc", doc_path)
    shutil.copytree("tests/data", test_path)

    monkeypatch.chdir(doc_path)

    runpy.run_path(example_code)
    # Check that output file exists
    assert Path(doc_path / output_file).is_file()
