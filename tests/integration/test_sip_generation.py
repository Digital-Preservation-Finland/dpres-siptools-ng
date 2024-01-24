"""
Test generation of complete SIPs and validate various traits in the final
SIP
"""
import tarfile

from lxml import etree
from mets_builder import METS, MetsProfile, StructuralMap, StructuralMapDiv
from mets_builder.serialize import _NAMESPACES

from siptools_ng.sip import SIP
from siptools_ng.sip_digital_object import SIPDigitalObject


def _extract_sip(sip_filepath, extract_filepath):
    """Extract tarred SIP to given path."""
    with tarfile.open(sip_filepath) as sip:
        sip.extractall(extract_filepath)


def _get_testing_filepaths(tmp_path_of_test):
    """Get filepaths for directing files produced by the tests to a canonized
    location.
    """
    output_filepath = tmp_path_of_test / "finalized_sip.tar"
    extracted_filepath = tmp_path_of_test / "extracted_sip"
    return output_filepath, extracted_filepath


def test_file_location_in_sip(tmp_path):
    """Test that digital objects are copied to the right path in the finalized
    SIP.
    """
    output_filepath, extracted_filepath = _get_testing_filepaths(tmp_path)

    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
    )
    digital_object_1 = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="data/files/test_file_1.txt"
    )
    digital_object_2 = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="data/files/test_file_2.txt"
    )
    digital_objects = [digital_object_1, digital_object_2]
    root_div = StructuralMapDiv("test_div", digital_objects=digital_objects)
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    sip = SIP(mets=mets)
    sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )

    _extract_sip(output_filepath, extracted_filepath)

    assert extracted_filepath.is_dir()
    datadir = extracted_filepath / "data"
    assert datadir.is_dir()
    assert (datadir / "files").is_dir()
    assert (datadir / "files" / "test_file_1.txt").is_file()
    assert (datadir / "files" / "test_file_2.txt").is_file()


def test_stream_relationships_in_sip_mets(tmp_path):
    """
    Test that relationships between a digital object and bitstreams
    contained within it are added into the generated METS
    """
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
    )
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_video_ffv_flac.mkv",
        sip_filepath="data/files/test_video.mkv"
    )
    digital_object.generate_technical_metadata()
    root_div = StructuralMapDiv("test_div", digital_objects=[digital_object])
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    xml = mets.to_xml()

    xml_root = etree.fromstring(xml)

    # Object identifiers for PREMIS Objects wrapped inside TechMD elements
    bitstream_object_ids = [
        elem.text for elem
        in xml_root.xpath(
            "//premis:relatedObjectIdentifierValue", namespaces=_NAMESPACES
        )
    ]
    bitstream_premis_objects = xml_root.xpath(
        "//premis:object[@xsi:type='premis:bitstream']", namespaces=_NAMESPACES
    )
    # The IDs attached to the TechMD element
    bitstream_ids = [
        obj.getparent().getparent().getparent().attrib["ID"] for obj
        in bitstream_premis_objects
    ]

    # Two object identifiers are created for both of the bitstreams
    assert len(bitstream_object_ids) == 2
    assert len(bitstream_premis_objects) == 2

    # Ensure both bitstreams exist
    for object_id in bitstream_object_ids:
        assert len([
            bitstream for bitstream in bitstream_premis_objects
            if bitstream.xpath(
                ".//premis:objectIdentifierValue", namespaces=_NAMESPACES
            )[0].text == object_id
        ]) == 1

    # Ensure the file group is defined and contains the file and its streams
    file_object = xml_root.xpath("//mets:file", namespaces=_NAMESPACES)[0]

    assert file_object.xpath(
        "./mets:FLocat", namespaces=_NAMESPACES
    )[0].attrib[f"{{{_NAMESPACES['xlink']}}}href"] \
        == "file:///data/files/test_video.mkv"

    # Ensure the file contains links to the bitstreams
    assert len([
        stream for stream in file_object.xpath(
            "./mets:stream", namespaces=_NAMESPACES
        )
        if bitstream_ids[0] in stream.attrib["ADMID"]
    ]) == 1
    assert len([
        stream for stream in file_object.xpath(
            "./mets:stream", namespaces=_NAMESPACES
        )
        if bitstream_ids[1] in stream.attrib["ADMID"]
    ]) == 1

    videomd = xml_root.xpath("//videomd:VIDEOMD", namespaces=_NAMESPACES)[0]
    videomd_id = videomd.getparent().getparent().getparent().attrib["ID"]

    audiomd = xml_root.xpath("//audiomd:AUDIOMD", namespaces=_NAMESPACES)[0]
    audiomd_id = audiomd.getparent().getparent().getparent().attrib["ID"]

    # Ensure the file contains links to the technical media metadata
    assert len([
        stream for stream in file_object.xpath(
            "./mets:stream", namespaces=_NAMESPACES
        )
        if videomd_id in stream.attrib["ADMID"]
    ]) == 1
    assert len([
        stream for stream in file_object.xpath(
            "./mets:stream", namespaces=_NAMESPACES
        )
        if audiomd_id in stream.attrib["ADMID"]
    ]) == 1


def test_mets_technical_metadata_deduplicate(tmp_path):
    """
    Test that identical technical metadata shared by multiple digital objects
    is deduplicated in the generated METS.
    """
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
    )
    # Four instances of the same Matroska video file
    digital_objects = [
        SIPDigitalObject(
            source_filepath="tests/data/test_video_ffv_flac.mkv",
            sip_filepath=f"data/files/test_video_{i}.mkv"
        )
        for i in range(0, 4)
    ]
    # One different digital object
    digital_objects.append(
        SIPDigitalObject(
            source_filepath="tests/data/test_video.dv",
            sip_filepath="data/files/test_video.dv"
        )
    )
    for digital_object in digital_objects:
        digital_object.generate_technical_metadata()

    root_div = StructuralMapDiv("test_div", digital_objects=digital_objects)
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    xml = mets.to_xml()
    xml_root = etree.fromstring(xml)

    # Ensure the file group is defined and contains the file and its streams
    assert len(xml_root.xpath("//mets:file", namespaces=_NAMESPACES)) == 5

    # Only two VideoMD objects are generated:
    # one for MKV which is reused for all 4 MKV files,
    # and another for the sole DV file
    assert len(xml_root.xpath("//videomd:VIDEOMD", namespaces=_NAMESPACES)) == 2
    mkv_videomd_id = next(
        vmd for vmd
        in xml_root.xpath("//videomd:VIDEOMD", namespaces=_NAMESPACES)
        if vmd.xpath(
            ".//videomd:codecName[text()='FFV1']", namespaces=_NAMESPACES
        )
    ).xpath("../../..")[0].attrib["ID"]
    dv_videomd_id = next(
        vmd for vmd
        in xml_root.xpath("//videomd:VIDEOMD", namespaces=_NAMESPACES)
        if vmd.xpath(
            ".//videomd:codecName[text()='DV']", namespaces=_NAMESPACES
        )
    ).xpath("../../..")[0].attrib["ID"]

    # Only one AudioMD object is generated
    assert len(xml_root.xpath("//audiomd:AUDIOMD", namespaces=_NAMESPACES)) == 1
    mkv_audiomd = xml_root.xpath("//audiomd:AUDIOMD", namespaces=_NAMESPACES)[0]
    mkv_audiomd_id = mkv_audiomd.xpath("../../..")[0].attrib["ID"]

    # Get MKV file references
    mkv_files = xml_root.xpath(
        "//mets:FLocat[contains(@xlink:href, '.mkv')]/..",
        namespaces=_NAMESPACES
    )
    assert len(mkv_files) == 4

    for mkv_file in mkv_files:
        # Each MKV file contains a reference to deduplicated VideoMD and
        # AudioMD streams
        assert mkv_file.xpath(
            f"./mets:stream[contains(@ADMID, '{mkv_videomd_id}')]",
            namespaces=_NAMESPACES
        )
        assert mkv_file.xpath(
            f"./mets:stream[contains(@ADMID, '{mkv_audiomd_id}')]",
            namespaces=_NAMESPACES
        )

        # There are *no* references to the DV VideoMD data
        assert not mkv_file.xpath(
            f"./mets:stream[contains(@ADMID, '{dv_videomd_id}')]",
            namespaces=_NAMESPACES
        )



