"""GRS-0172 polish sweep — pipeline input hygiene at the HTTP boundary."""

from __future__ import annotations


def test_create_prospect_refuses_a_name_with_no_substance(client, alice) -> None:
    """GRS-0172 (staging rerun, Marcus): "🚀🚀🚀" became a real CRM record and polluted conversion
    stats. A company name must contain at least one letter or digit — whitespace-only was already
    refused; symbol/emoji-only now refuses loudly too. Real names (unicode included) still pass."""
    from tests.conftest import auth_header

    headers = auth_header(alice)
    refused = client.post("/prospects", json={"company_name": "🚀🚀🚀"}, headers=headers)
    assert refused.status_code == 422
    assert "letter or number" in str(refused.json())
    ok = client.post("/prospects", json={"company_name": "Börse Åhlens 24"}, headers=headers)
    assert ok.status_code == 201
