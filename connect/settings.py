from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'connect/static',
]

# Create a 'staticfiles' directory in your project root
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create the directories if they don't exist
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
]  # Closed the TEMPLATES list

# M-Pesa Configuration
MPESA_ENVIRONMENT = 'sandbox' 
MPESA_CONSUMER_KEY = 'IguAYbVAU1X9HN5az9BoswAWCMvp1vACZMdne4ZUhOZWAxKt'
MPESA_CONSUMER_SECRET = 'OvQiZuUZpOckscsyi1CmsaAg9dmNwTGUbdIo1KnWjLKP2N9x9DRlylY86yvz91U3'
MPESA_SHORTCODE = '174349' 
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'  


