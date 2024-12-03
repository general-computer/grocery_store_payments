import os

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/student_payments')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Stripe Configuration
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

    # Email Configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    DEFAULT_FROM_EMAIL = 'payments@studentprocessor.com'

    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'development_secret_key')

    # Internationalization
    SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'zh']
    DEFAULT_LANGUAGE = 'en'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
