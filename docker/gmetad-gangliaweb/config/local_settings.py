SECRET_KEY = 'Akjdjwdgferoiuhfreuotiu5fgreuhguhkjhkjfh'
LOG_RENDERING_PERFORMANCE = True
LOG_CACHE_PERFORMANCE = True
LOG_METRIC_ACCESS = True
FLUSHRRDCACHED = 'unix:/tmp/rrdcached.limited.sock'
GRAPHITE_ROOT = '/usr/share/graphite-web'
CONF_DIR = '/etc/graphite'
STORAGE_DIR = '/var/lib/graphite/whisper'
CONTENT_DIR = '/usr/share/graphite-web/static'
RRD_DIR = '/var/lib/ganglia/rrds'
DATA_DIRS = [RRD_DIR] # Default: set from the above variables
LOG_DIR = '/var/log/graphite'
INDEX_FILE = '/var/lib/graphite/search_index'  # Search index file
DATABASES = {
    'default': {
        'NAME': '/var/lib/graphite/graphite.db',
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': ''
    }
}
