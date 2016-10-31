from flask_testing import TestCase

from app import create_app, db

class BaseTestCase(TestCase):

    def create_app(self):
        app.config.from_object('config.TestConfiguration')
        return create_app(self)

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()