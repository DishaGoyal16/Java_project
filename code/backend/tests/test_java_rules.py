"""Run with a Java service on loopback and SCMS_RULES_TOKEN configured."""
import json
import os
import random
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException
from app.services import java_rules

pytestmark = pytest.mark.skipif(not os.getenv("SCMS_RULES_TOKEN"), reason="Java service token not configured")

def test_rank_matches_python_reference():
    rng = random.Random(553)
    for _ in range(100):
        count = rng.randrange(0, 40)
        rows = [(i, rng.randrange(8), rng.choice([0, 0.5, 2, 5, 9999]),
                 datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=rng.randrange(5)))
                for i in range(count)]
        values = {"count": count, "threshold": 2, "weight": 0.5}
        for i, (bid, sessions, days, created) in enumerate(rows):
            values.update({f"c{i}_id":bid, f"c{i}_sessions":sessions,
                           f"c{i}_days":days, f"c{i}_created":created.isoformat()})
        maximum = max([r[1] for r in rows], default=0)
        scored = [(bid, sessions/max(maximum,1) + (max(0,(2-days)*0.5) if days<2 else 0), created)
                  for bid,sessions,days,created in rows]
        expected = sorted(scored, key=lambda r:(r[1],r[2]))
        actual = java_rules.call("rank", values)
        assert [r["id"] for r in actual] == [r[0] for r in expected]
        assert [r["score"] for r in actual] == pytest.approx([r[1] for r in expected], abs=1e-14)

@pytest.mark.parametrize("operation,payload,code,status", [
    ("booking", {"student_status":"SUSPENDED"}, "ACCOUNT_SUSPENDED", 403),
    ("booking", {"student_status":"ACTIVE","defaulter":True}, "ACTIVE_DEFAULTER",403),
    ("booking", {"student_status":"ACTIVE","defaulter":False,"slot_exists":False},"SLOT_NOT_FOUND",404),
    ("cancel", {"owned":False},"BOOKING_NOT_FOUND",404),
    ("cancel", {"owned":True,"status":"COMPLETED"},"BOOKING_CANNOT_CANCEL",400),
    ("issue", {"booking_exists":False},"BOOKING_NOT_FOUND",404),
    ("issue", {"booking_exists":True,"booking_status":"REQUESTED"},"BOOKING_NOT_CONFIRMED",400),
    ("return", {"transaction_exists":False},"TRANSACTION_NOT_FOUND",404),
    ("return", {"transaction_exists":True,"status":"RETURNED"},"INVALID_TRANSACTION_STATE",400),
    ("return", {"transaction_exists":True,"status":"OVERDUE","condition":"DAMAGED","has_report":False},"DAMAGE_REPORT_REQUIRED",400),
])
def test_java_error_contract(operation,payload,code,status):
    with pytest.raises(HTTPException) as result:
        java_rules.call(operation,payload)
    assert result.value.status_code==status
    assert result.value.detail["code"]==code

def test_service_rejects_unauthenticated_requests():
    with pytest.raises(HTTPError) as result:
        urlopen(Request("http://127.0.0.1:8091/internal/health"),timeout=2)
    assert result.value.code==401

def test_service_failure_does_not_silently_fallback(monkeypatch):
    monkeypatch.setenv("SCMS_RULES_URL","http://127.0.0.1:1")
    with pytest.raises(HTTPException) as result:
        java_rules.call("cancel",{"owned":True,"status":"REQUESTED"})
    assert result.value.status_code==503

def test_unknown_engine_rejected(monkeypatch):
    monkeypatch.setenv("SCMS_RULES_ENGINE","typo")
    with pytest.raises(RuntimeError):java_rules.enabled()

def test_full_public_api_workflow(client, session, student_riya, open_slot,
                                  cricket_bat, staff_user, fairness_config):
    from tests.conftest import auth_headers
    from app.models.enums import SlotStatus
    from app.services.fairness_engine import run_batch_allocation
    student_headers = auth_headers(student_riya.id, "STUDENT")
    staff_headers = auth_headers(staff_user.id, "STAFF")
    booking = client.post("/api/bookings", json={"slot_id":open_slot.id}, headers=student_headers)
    assert booking.status_code == 201
    bid = booking.json()["data"]["id"]
    open_slot.status = SlotStatus.PENDING_ALLOCATION
    session.add(open_slot)
    session.commit()
    assert run_batch_allocation(session,open_slot.id)["confirmed"] == 1
    issue = client.post("/api/transactions/issue", json={"booking_id":bid,"equipment_id":cricket_bat.id}, headers=staff_headers)
    assert issue.status_code == 201,issue.text
    tid = issue.json()["data"]["id"]
    returned = client.post(f"/api/transactions/{tid}/return", json={"condition_on_return":"GOOD"}, headers=staff_headers)
    assert returned.status_code == 200,returned.text
    assert returned.json()["data"]["status"] == "RETURNED"
    details = client.get(f"/api/bookings/{bid}", headers=student_headers)
    assert details.json()["data"]["status"] == "COMPLETED"
    assert client.get("/api/notifications", headers=student_headers).status_code == 200
    assert client.get("/api/transactions", headers=student_headers).json()["data"][0]["id"] == tid
