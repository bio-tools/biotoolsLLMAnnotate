"""Test bio.tools ID generation from tool names."""

from biotoolsllmannotate.cli.run import generate_biotools_id


def test_generate_biotools_id_lowercase():
    """Test that tool names are converted to lowercase."""
    assert generate_biotools_id("BLAST") == "blast"
    assert generate_biotools_id("DeepRank-GNN") == "deeprank-gnn"


def test_generate_biotools_id_hyphens():
    """Test that hyphens are preserved."""
    assert generate_biotools_id("ARCTIC-3D") == "arctic-3d"
    assert generate_biotools_id("DeepRank-GNN-esm") == "deeprank-gnn-esm"


def test_generate_biotools_id_spaces():
    """Test that spaces are converted to underscores."""
    assert generate_biotools_id("My Tool Name") == "my_tool_name"
    assert generate_biotools_id("RNA Seq Tool") == "rna_seq_tool"


def test_generate_biotools_id_special_chars():
    """Test that special characters are removed."""
    assert generate_biotools_id("Tool@2024") == "tool2024"
    assert generate_biotools_id("My-Tool!") == "my-tool"
    assert (
        generate_biotools_id("Tool (v2)") == "tool_v2"
    )  # Spaces converted to underscores


def test_generate_biotools_id_consecutive_separators():
    """Test that consecutive separators are collapsed."""
    assert generate_biotools_id("My--Tool") == "my-tool"
    assert generate_biotools_id("My__Tool") == "my_tool"
    assert generate_biotools_id("My  Tool") == "my_tool"


def test_generate_biotools_id_leading_trailing():
    """Test that leading/trailing separators are removed."""
    assert generate_biotools_id("-MyTool-") == "mytool"
    assert generate_biotools_id("_MyTool_") == "mytool"
    assert generate_biotools_id(" MyTool ") == "mytool"


def test_generate_biotools_id_empty():
    """Test that empty strings return empty."""
    assert generate_biotools_id("") == ""
    assert generate_biotools_id("   ") == ""


def test_generate_biotools_id_real_examples():
    """Test with real tool names from the test dataset."""
    assert generate_biotools_id("ExomiRHub") == "exomirhub"
    assert generate_biotools_id("ccTCM") == "cctcm"
    assert generate_biotools_id("DockOpt") == "dockopt"
    assert generate_biotools_id("PPSNO") == "ppsno"
    assert generate_biotools_id("BioTreasury") == "biotreasury"
    assert generate_biotools_id("Vulture") == "vulture"
    assert generate_biotools_id("ReMASTER") == "remaster"
    assert generate_biotools_id("Seq-InSite") == "seq-insite"
    assert generate_biotools_id("ECOLE") == "ecole"
