
from contextlib import nullcontext as does_not_raise
from jsonschema.exceptions import ValidationError
import pytest

from cads_catalogue.sanity_check import sanity_check_item_validate, sanity_check_validate

item_ok = {
    "req_id": "064cae29-eafb-4ab1-ae8a-34172ec124d0",
    "success": True,
    "started_at": "2025-07-23T07:08:01.859196+00:00",
    "finished_at": "2025-07-23T07:18:28.331018+00:00"
}

item_ok_null_request = {
    "req_id": None,
    "success": False,
    "started_at": "2025-07-23T07:08:01.859196+00:00",
    "finished_at": "2025-07-23T07:18:28.331018+00:00"
}

item_wrong_missing_part = {
    "req_id": "064cae29-eafb-4ab1-ae8a-34172ec124d0",
    "started_at": "2025-07-23T07:08:01.859196+00:00",
    "finished_at": "2025-07-23T07:18:28.331018+00:00"
}

item_wrong_empty_time = {
    "req_id": "064cae29-eafb-4ab1-ae8a-34172ec124d0",
    "success": True,
    "started_at": "2025-07-23T07:08:01.859196+00:00",
    "finished_at": None
}

item_wrong_not_uuid = {
    "req_id": "064cae29",
    "success": True,
    "started_at": "2025-07-23T07:08:01.859196+00:00",
    "finished_at": "2025-07-23T07:18:28.331018+00:00"
}


@pytest.mark.parametrize("item, expectation", [
    (item_ok, does_not_raise()),
    (item_ok_null_request, does_not_raise()),
    (item_wrong_missing_part, pytest.raises(ValidationError)),
    (item_wrong_empty_time, pytest.raises(ValidationError)),
    (item_wrong_not_uuid, pytest.raises(ValidationError)),
])
def test_sanity_check_item_validate(item, expectation) -> None:
    with expectation:
        sanity_check_item_validate(item)


@pytest.mark.parametrize("items, expectation", [
    ([], does_not_raise()),
    ([item_ok], does_not_raise()),
    ([item_ok, item_ok_null_request], does_not_raise()),
    ([item_ok, item_ok], pytest.raises(ValidationError)),
    ([item_ok, item_wrong_empty_time], pytest.raises(ValidationError)),
    ([item_wrong_not_uuid, item_ok], pytest.raises(ValidationError)),
])
def test_sanity_check_validate(items, expectation) -> None:
    with expectation:
        sanity_check_validate(items)
