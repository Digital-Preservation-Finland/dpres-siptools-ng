import runpy
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest


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

    schema_checker_path = shutil.which("check-xml-schema-features-3")
    schematron_checker_path = shutil.which("check-xml-schematron-features-3")

    if not schema_checker_path:
        pytest.skip("dpres-ipt, skipping METS validation")

    extract_path = Path(tmpdir / "extract_sip")
    extract_path.mkdir()

    with tarfile.open(doc_path / output_file) as sip:
        sip.extractall(extract_path)

    mets_path = extract_path / "mets.xml"

    result = subprocess.run(
        [schema_checker_path, str(mets_path)],
        check=False, capture_output=True
    )
    assert result.returncode == 0

    result = subprocess.run(
        [
            schematron_checker_path,
            "-s", "/usr/share/dpres-xml-schemas/schematron/mets_root.sch",
            str(mets_path)
        ],
        check=False, capture_output=True
    )
    assert result.returncode == 0
