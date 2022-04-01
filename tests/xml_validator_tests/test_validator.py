import pytest, os, sys

script_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "..", "..")))
from mavlib_gen.validator import *
import networkx as netx

TEST_CASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_cases"))


@pytest.fixture
def validator():
    validator = MavlinkXmlValidator()
    return validator


################################
# Single XML Tests
################################


def test_bad_filename(validator):
    """Non-existent xml file should fail"""
    assert validator.validate_single_xml("bogus/file.xml") is None


def test_msg_def_duplicate_err(validator):
    mdefa = MavlinkXmlFile("/test/path1/common.xml", {})
    mdefb = MavlinkXmlFile("/test/path2/asdf.xml", {})
    mdefc = MavlinkXmlFile("/test/path2/common.xml", {})
    other_defs = {mdefb.filename: mdefb, mdefc.filename: mdefc}
    assert MSG_DEF_DUPLICATE_ERR == validator.is_msg_def_unique(mdefa, other_defs)


def test_msg_def_duplicate(validator):
    mdefa = MavlinkXmlFile("/test/path/common.xml", {})
    mdefb = MavlinkXmlFile("/test/path2/asdf.xml", {})
    mdefc = MavlinkXmlFile("/test/path/common.xml", {})
    other_defs = {mdefb.filename: mdefb, mdefc.filename: mdefc}
    assert MSG_DEF_DUPLICATE == validator.is_msg_def_unique(mdefa, other_defs)


def test_msg_def_unique(validator):
    mdefa = MavlinkXmlFile("/test/path/common.xml", {})
    mdefb = MavlinkXmlFile("/test/path/asdf.xml", {})
    mdefc = MavlinkXmlFile("/test/path/ghjk.xml", {})
    other_defs = {mdefb.filename: mdefb, mdefc.filename: mdefc}
    assert MSG_DEF_UNIQUE == validator.is_msg_def_unique(mdefa, other_defs)


################################
# Include Expansion Tests
################################


def setup_complex_tree_top_xmls(validator):
    """setup the top-level xmls for the complex include tree tests"""
    files = ["top_level.xml", "top_level2.xml"]
    abs_files = [
        os.path.join(TEST_CASE_DIR, "pass", "complex_include_graph", fname) for fname in files
    ]
    validated = [validator.validate_single_xml(fname) for fname in abs_files]
    validated_complex_xmls = dict(zip(files, validated))
    for fname, xml in validated_complex_xmls.items():
        assert xml is not None
        assert fname == xml.filename
    return validated_complex_xmls


def test_invalid_include_path(validator):
    """include path pointing to non-existent file should fail"""
    good_xml_path = os.path.join(TEST_CASE_DIR, "fail", "invalid_include.xml")
    good_xml = validator.validate_single_xml(good_xml_path)
    assert good_xml is not None
    result = validator.expand_includes({good_xml.filename: good_xml})
    assert result is None


def test_xml_with_no_include(validator):
    """expand_includes should do nothing if xmls dont have include tags"""
    filename = "no_includes.xml"
    includeless_xml_path = os.path.join(TEST_CASE_DIR, "pass", filename)
    includeless_xml = validator.validate_single_xml(includeless_xml_path)
    assert includeless_xml is not None
    xmls_in = {includeless_xml.filename: includeless_xml}
    result = validator.expand_includes(xmls_in)
    assert xmls_in == result[0]
    assert ["no_includes.xml"] == list(netx.topological_sort(result[1]))


def test_complex_include_tree(validator):
    """verify expand_includes successfully/properly parses the complex include graph"""
    # used to verify the generated include graph (in this case successors are xmls DIRECTLY included by the key)
    expected_successors = {
        "top_level.xml": ["m1.xml", "m2.xml", "m3.xml", "m5.xml"],
        "top_level2.xml": ["m5.xml"],
        "m1.xml": ["m4.xml"],
        "m2.xml": ["m4.xml"],
        "m3.xml": ["r1.xml", "r2.xml"],
        "m4.xml": ["r2.xml"],
        "m5.xml": ["r1.xml", "m2.xml"],
        "r1.xml": [],
        "r2.xml": [],
    }
    validated_complex_xmls = setup_complex_tree_top_xmls(validator)

    result = validator.expand_includes(validated_complex_xmls)
    assert result is not None
    include_graph = result[1]
    assert netx.is_directed_acyclic_graph(include_graph)
    all_nodes = list(netx.topological_sort(include_graph))
    assert len(all_nodes) == len(list(expected_successors.keys()))

    for node in all_nodes:
        assert node in expected_successors
        assert sorted(expected_successors[node]) == sorted(list(include_graph.successors(node)))


def test_generate_dependency_list_complex_tree(validator):
    """verify generate_dependency_list produces accurate results for a complex tree"""
    expected_dep_lists = {
        "top_level.xml": ["m1.xml", "m2.xml", "m3.xml", "m4.xml", "m5.xml", "r1.xml", "r2.xml"],
        "top_level2.xml": ["m2.xml", "m4.xml", "m5.xml", "r1.xml", "r2.xml"],
        "m1.xml": ["m4.xml", "r2.xml"],
        "m2.xml": ["m4.xml", "r2.xml"],
        "m3.xml": ["r1.xml", "r2.xml"],
        "m4.xml": ["r2.xml"],
        "m5.xml": ["m2.xml", "m4.xml", "r1.xml", "r2.xml"],
        "r1.xml": [],
        "r2.xml": [],
    }
    validated_complex_xmls = setup_complex_tree_top_xmls(validator)
    result = validator.expand_includes(validated_complex_xmls)
    assert result is not None
    expanded_xmls = result[0]
    include_graph = result[1]

    validator.generate_dependency_list(expanded_xmls, include_graph)

    for fname, xml in expanded_xmls.items():
        assert fname in expected_dep_lists
        assert sorted(expected_dep_lists[fname]) == sorted(xml.dependencies)


###################################
# Unique MsgId Across Dependencies
###################################


@pytest.fixture
def msg_id_name_validator():
    msg_id_name_validator = UniqueMsgIdNameAcrossDependencies()
    return msg_id_name_validator


def setup_msg_info(validator):
    """setup the top-level xmls for a complex include tree test"""
    files = ["top_level.xml", "top_level2.xml"]
    abs_files = [
        os.path.join(TEST_CASE_DIR, "pass", "complex_include_graph", fname) for fname in files
    ]
    validated = [validator.validate_single_xml(fname) for fname in abs_files]
    validated_complex_xmls = dict(zip(files, validated))
    result = validator.expand_includes(validated_complex_xmls)
    assert result is not None
    complex_expanded_xmls = result[0]
    complex_include_graph = result[1]
    validator.generate_dependency_list(complex_expanded_xmls, complex_include_graph)
    return complex_expanded_xmls, complex_include_graph


def test_empty_dict(msg_id_name_validator):
    assert msg_id_name_validator.validate({}, netx.DiGraph())


def test_single_xml(validator, msg_id_name_validator):
    mdef = validator.validate_single_xml(os.path.join(TEST_CASE_DIR, "pass", "no_includes.xml"))
    assert mdef is not None
    assert msg_id_name_validator.validate({mdef.filename: mdef}, netx.DiGraph())


def test_few_messages(validator, msg_id_name_validator):
    """Verify returns True with the complex_include_graph example that only has a couple messages"""
    complex_expanded_xmls, complex_include_graph = setup_msg_info(validator)
    assert msg_id_name_validator.validate(complex_expanded_xmls, complex_include_graph)


def test_conflicting_ids(validator, msg_id_name_validator):
    """verify returns False when a msg id conflicts"""
    top_xml = validator.validate_single_xml(
        os.path.join(TEST_CASE_DIR, "fail", "include_with_conflicting_msgid", "top.xml")
    )
    assert top_xml is not None

    result = validator.expand_includes({top_xml.filename: top_xml})
    assert result is not None
    validator.generate_dependency_list(result[0], result[1])
    assert not msg_id_name_validator.validate(result[0], result[1])


def test_conflicting_names(validator, msg_id_name_validator):
    """verify returns False when a msg name conflicts"""
    top_xml = validator.validate_single_xml(
        os.path.join(TEST_CASE_DIR, "fail", "include_with_conflicting_msgname", "top.xml")
    )
    assert top_xml is not None
    result = validator.expand_includes({top_xml.filename: top_xml})
    assert result is not None
    validator.generate_dependency_list(result[0], result[1])
    assert not msg_id_name_validator.validate(result[0], result[1])
