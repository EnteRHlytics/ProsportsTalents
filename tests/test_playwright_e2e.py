import threading
import time

import pytest
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

from app import create_app, db
from app.models import AthleteProfile


@pytest.fixture(scope="module")
def flask_app():
    app = create_app('testing')
    app.config['LOGIN_DISABLED'] = True
    with app.app_context():
        db.create_all()
    server = make_server('127.0.0.1', 5000, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    time.sleep(1)
    yield app
    server.shutdown()
    thread.join()
    with app.app_context():
        db.drop_all()


def test_create_and_edit_profile(flask_app):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto('http://localhost:5000/athletes/new')
        page.fill('input#first_name', 'E2E')
        page.fill('input#last_name', 'Tester')
        page.fill('input#date_of_birth', '2000-01-01')
        page.fill('input#nationality', 'USA')
        page.click('input[type=submit]')
        page.wait_for_url('**/athletes/*')
        athlete_id = page.url.rsplit('/', 1)[-1]

        with flask_app.app_context():
            athlete = AthleteProfile.query.get(athlete_id)
            assert athlete is not None
            assert athlete.user.first_name == 'E2E'

        page.click('text=Edit')
        page.fill('input#first_name', 'Updated')
        page.click('input[type=submit]')
        page.wait_for_url(f'**/athletes/{athlete_id}')

        with flask_app.app_context():
            athlete = AthleteProfile.query.get(athlete_id)
            assert athlete.user.first_name == 'Updated'

        browser.close()
