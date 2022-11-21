def test_index_not_logged_in(app):
    """Redirect to timeclock.auth.login."""
    with app.test_client() as client:
        resp = client.get("/timeclock")
    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/timeclock/auth/login"


def test_index_employee_not_clocked_in(app, employee_user):
    """Show the default page."""
    with app.test_client(user=employee_user) as client:
        resp = client.get("/timeclock")
    assert resp.status_code == 200
    assert 'hx-put="/timeclock/clock_in">CLOCK IN</button>' in resp.text


def test_index_employee_clocked_in(app, employee_user, employee_workday):
    """Show the default page."""
    with app.test_client(user=employee_user) as client:
        resp = client.get("/timeclock")
    assert resp.status_code == 200
    assert 'hx-post="/timeclock/clock_out">CLOCK OUT</button>' in resp.text
    assert f'hx-post="/timeclock/workday/{employee_workday.id}/notes">' in resp.text
    assert f'hx-put="/timeclock/workday/{employee_workday.id}/photo">' in resp.text


def test_clock_in(app, employee_user):
    with app.test_client(user=employee_user) as client:
        resp = client.put("/timeclock/clock_in")
    assert resp.status_code == 201
    assert 'hx-post="/timeclock/clock_out">CLOCK OUT</button>' in resp.text


def test_clock_out(app, employee_user):
    with app.test_client(user=employee_user) as client:
        resp = client.post("/timeclock/clock_out")
    assert resp.status_code == 200
    assert 'hx-put="/timeclock/clock_in">CLOCK IN</button>' in resp.text


def test_current_timesheet_employee_view(app, employee_user):
    with app.test_client(user=employee_user) as client:
        resp = client.get(
            "/timeclock/timesheet", query_string={"user_id": employee_user.id}
        )
    assert resp.status_code == 200
    print(resp.text)


# def test_index_owner_view(app, owner_user, fake_timesheet_db):
#     with app.test_client(user=owner_user) as client:
#         resp = client.get("/timeclock")
#     assert resp.status_code == 200
#     assert "<th>Employee</th>" in resp.text
