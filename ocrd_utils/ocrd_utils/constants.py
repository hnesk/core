"""
Constants for ocrd_utils.
"""
from pkg_resources import get_distribution
import os
from os.path import join, expanduser

__all__ = [
    'EXT_TO_MIME',
    'LOG_FORMAT',
    'LOG_TIMEFMT',
    'MIMETYPE_PAGE',
    'MIME_TO_EXT',
    'MIME_TO_PIL',
    'PIL_TO_MIME',
    'REGEX_PREFIX',
    'VERSION',
    'XDG_CONFIG_HOME',
    'XDG_DATA_HOME',
]

VERSION = get_distribution('ocrd_utils').version

MIMETYPE_PAGE = 'application/vnd.prima.page+xml'

EXT_TO_MIME = {
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.xml': MIMETYPE_PAGE,
    '.jp2': 'image/jp2',
    '.pdf': 'application/pdf',
    '.ps': 'application/postscript',
    '.eps': 'application/postscript',
    '.xps': 'application/oxps',
    '.ppm': 'image/x-portable-pixmap',
    '.pnm': 'image/x-portable-anymap',
    '.pbm': 'image/x-portable-bitmap',
}

MIME_TO_EXT = {
    'image/tiff': '.tif',
    'image/tif': '.tif',
    'image/png': '.png',
    'image/jpg': '.jpg',
    'image/jpeg': '.jpg',
    MIMETYPE_PAGE: '.xml',
    'application/alto+xml': '.xml',
    'image/jp2': '.jp2',
    'application/pdf': '.pdf',
    'application/postscript': '.ps',
    'application/oxps': '.xps',
    'image/x-portable-pixmap': '.ppm',
    'image/x-portable-anymap': '.pnm',
    'image/x-portable-bitmap': '.pbm',
}

#
# Translate between what PIL expects as ``format`` and IANA media types.
#
PIL_TO_MIME = {
    'BMP':  'image/bmp',
    'EPS':  'application/postscript',
    'GIF':  'image/gif',
    'JPEG': 'image/jpeg',
    'JP2':  'image/jp2',
    'PNG':  'image/png',
    'PPM':  'image/x-portable-pixmap',
    'TIFF': 'image/tiff',
}

MIME_TO_PIL = {
    'image/bmp': 'BMP',
    'application/postscript': 'EPS',
    'image/gif': 'GIF',
    'image/jpeg': 'JPEG',
    'image/jp2': 'JP2',
    'image/png': 'PNG',
    'image/x-portable-pixmap': 'PPM',
    'image/tiff': 'TIFF',
}

# Prefix to denote query is regular expression not fixed string
REGEX_PREFIX = '//'

# Log level format implementing https://ocr-d.de/en/spec/cli#logging
LOG_FORMAT = r'%(asctime)s.%(msecs)03d %(levelname)s %(name)s - %(message)s'
LOG_TIMEFMT = r'%H:%M:%S'

# See https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
XDG_DATA_HOME = os.environ['XDG_DATA_HOME'] if 'XDG_DATA_HOME' in os.environ else join(expanduser('~'), '.local', 'share')
XDG_CONFIG_HOME = os.environ['XDG_CONFIG_HOME'] if 'XDG_CONFIG_HOME' in os.environ else join(expanduser('~'), '.config')
