import arrow
import pytest
from pydantic import ValidationError

from api.models import EnumerationQueryArgs


def test_empty_qargs_parse_as_null():
    qargs = EnumerationQueryArgs(**{})

    assert qargs.status is None
    assert qargs.created_at is None
    assert qargs.completed_at is None


def test_multiple_qargs_fail_parsing():
    with pytest.raises(ValidationError):
        EnumerationQueryArgs(
            **{"status": "PENDING", "created_at": str(arrow.utcnow().datetime)}
        )


def test_invalid_status_qarg_fails_parsing():
    with pytest.raises(ValidationError):
        EnumerationQueryArgs(**{"status": "TEST"})


@pytest.mark.parametrize("qarg_value", ["PENDING", "SUCCEEDED", "FAILED"])
def test_valid_status_qargs_parse(qarg_value: str):
    EnumerationQueryArgs(**{"status": qarg_value})


@pytest.mark.parametrize("qarg_value", ["TEST", "", 2])
def test_invalid_datetime_value_qarg_fails_parsing(qarg_value: str):
    with pytest.raises(ValidationError):
        EnumerationQueryArgs(**{"created_at": qarg_value})


def test_valid_datetime_qarg_parses():
    EnumerationQueryArgs(**{"created_at": str(arrow.utcnow().datetime)})
