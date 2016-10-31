import os
basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfiguration(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://michael:mypassword@localhost/game'

class TestConfiguration(BaseConfiguration):
    TESTING = True
