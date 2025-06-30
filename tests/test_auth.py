import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Role

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # create default viewer role
        if not Role.query.filter_by(name='viewer').first():
            db.session.add(Role(name='viewer'))
            db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_register(client, app_instance):
    data = {
        'username': 'newuser',
        'email': 'new@example.com',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'secret',
        'confirm': 'secret'
    }
    resp = client.post('/auth/register', data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Welcome' in resp.data
    with app_instance.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.check_password('secret')
        assert user.roles[0].name == 'viewer'


def test_login(client, app_instance):
    with app_instance.app_context():
        role = Role.query.filter_by(name='viewer').first()
        user = User(username='loginuser', email='login@example.com', first_name='Login', last_name='User')
        user.set_password('secret')
        if role:
            user.roles.append(role)
        db.session.add(user)
        db.session.commit()

    resp = client.post('/auth/login', data={'username_or_email': 'loginuser', 'password': 'secret'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Welcome' in resp.data
