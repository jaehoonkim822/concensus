import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin"))
sys.path.insert(0, os.path.dirname(__file__))

from snapshot_utils import validate_schema, save_run_log


class SnapshotE2E:
    def validate(self, test_name, schema_name, input_data, output, exit_code, duration_ms):
        schema_result = validate_schema(output, schema_name)
        save_run_log(
            test_name=test_name,
            input_data=input_data,
            output=output,
            exit_code=exit_code,
            duration_ms=duration_ms,
            schema_result=schema_result,
        )
        assert schema_result["passed"], (
            f"Schema validation failed for '{schema_name}': "
            f"{json.dumps(schema_result['check_results'], indent=2)}"
        )
        return schema_result


@pytest.fixture
def snapshot_e2e():
    return SnapshotE2E()
