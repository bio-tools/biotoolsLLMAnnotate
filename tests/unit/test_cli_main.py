import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

# Ensure we import the in-repo CLI implementation even if an older installed
# package version was loaded earlier during the pytest session.
for module_name in ["biotoolsllmannotate.cli.main", "biotoolsllmannotate.cli"]:
    sys.modules.pop(module_name, None)

# Test file kept for future CLI validation tests.
# Previous test_conflicting_resume_and_input_exits_with_message was removed
# because resume_from_pub2tools and custom_pub2tools_biotools_json are now
# allowed to work together (custom file is treated as the pub2tools export).
