"""
Airflow Webserver Configuration - Disable Authentication
Enables anonymous access with Admin role for development purposes.
"""
from airflow.www.fab_security.manager import AUTH_DB
from flask_appbuilder.security.manager import AUTH_REMOTE_USER

# Enable anonymous users with Admin role
AUTH_ROLE_PUBLIC = 'Admin'

# Set the authentication type to allow anonymous access
basedir = None

# The SQLAlchemy connection string
SQLALCHEMY_DATABASE_URI = None

# Flask-WTF flag for CSRF
CSRF_ENABLED = True

# Set to False to disable anonymous access
AUTH_USER_REGISTRATION = False

# Allow users who are not already in the FAB DB to login
AUTH_USER_REGISTRATION_ROLE = "Admin"

