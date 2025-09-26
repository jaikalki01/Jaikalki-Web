import os
import random
import string

class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    # MySQL Database URI configuration using 'pymysql'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Love1718@localhost/society'
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://gravity_user:Gravity080894@localhost/gravity_db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable SQLAlchemy modification tracking
    session_permanent = False  # Session will not be permanent
    PERMANENT_SESSION_LIFETIME = 90 * 24 * 60 * 60  # Sessions will last 90 days

    # SECRET_KEY for session and CSRF protection
    SECRET_KEY = os.urandom(32).hex()

    # Check if a secret key is defined in the environment; if not, generate one
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

    # Removed SQLite fallback and environmental variable-driven DB configurations

    # Asset Management
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')
    ASSETS_ROOT_NEW = os.getenv('ASSETS_ROOT_NEW', '/static/assets_new')
    JAIKALKI_ROOT = os.getenv('JAIKALKI_ROOT', '/static/assets_jaikalki')

    # Social Auth (Optional Github Integration)
    SOCIAL_AUTH_GITHUB = False
    GITHUB_ID = os.getenv('GITHUB_ID')
    GITHUB_SECRET = os.getenv('GITHUB_SECRET')

    # Enable/Disable Github Social Login
    if GITHUB_ID and GITHUB_SECRET:
        SOCIAL_AUTH_GITHUB = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600  # Remember me duration in seconds


class DebugConfig(Config):
    DEBUG = True


# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
