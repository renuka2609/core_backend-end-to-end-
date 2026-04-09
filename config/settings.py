from pathlib import Path
from datetime import timedelta

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
SECRET_KEY = 'django-insecure-change-this-key'

# Enable debugging in local development for Swagger UI and schema troubleshooting
DEBUG = True


ALLOWED_HOSTS = ['*']


# APPLICATIONS
INSTALLED_APPS = [
    # Django default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',        # ✅ ADD
    'drf_spectacular',
    'orgs.apps.OrgsConfig',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',


    # Core / base
    'users',
    'accounts',

    # Main workflow apps
    'vendors',
    'templates',
    'assessments',
    'responses',
    'reviews',
    'evidence',
    'remediations',

    # Cross-cutting
    'audit',
]



# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.ErrorHandlerMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # R-08: Input validation and error handling
    'config.middleware.InputValidationMiddleware',
    # R-09: Security headers and rate limiting
    'config.security.SecurityHeadersMiddleware',
    'config.security.RateLimitMiddleware',
    
]

# WhiteNoise static files storage for production-like behavior (serves static assets when DEBUG=False)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# URL CONFIG
ROOT_URLCONF = 'config.urls'


# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# WSGI
WSGI_APPLICATION = 'config.wsgi.application'


# DATABASE (SQLite – default)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 🌟 CUSTOM USER MODEL (VERY IMPORTANT)
AUTH_USER_MODEL = 'users.User'


# LANGUAGE & TIME

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True


# STATIC FILES
STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'


# DEFAULT PK
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # R-08: Custom exception handler for safe error responses
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
    # R-09: Rate limiting and throttling
    # Temporarily disabled due to circular import - rate limiting handled via middleware
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'config.security.UserRateLimitThrottle',
    #     'config.security.IPRateLimitThrottle',
    # ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour',
        'anon': '50/hour',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Core Backend API',
    'DESCRIPTION': 'API documentation',
    'VERSION': '1.0.0',
    'SERVE_PUBLIC': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'presets': [
            'swaggerUIBundle.presets.apis',
            'swaggerUIBundle.SwaggerUIStandalonePreset',
        ],
        'layout': 'StandaloneLayout',
    },
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CACHING (for rate limiting and brute-force defense)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# LOGGING (for audit and security)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'config.middleware': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'config.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
        'audit': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}