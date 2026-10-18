"""Keep the kids' page viewport fixed while their canvases handle gestures."""
import re
from flask import request
from riley_creative import app

VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">'
HEAD = (VIEWPORT + '<script id="kids-page-zoom-lock" src="/static/kids-touch-lock.js?v=20261018-1"></script>'
        '<style id="kids-page-zoom-style">html,body{touch-action:pan-x pan-y}button,a,input,select,textarea{touch-action:manipulation}'
        'input:not([type=range]):not([type=color]):not([type=checkbox]):not([type=radio]),select,textarea{font-size:16px!important}</style>')

def is_kids_page(path):
    return (path in ('/riley','/hyeon') or path.startswith(('/riley/','/hyeon/'))
            or path in ('/static/hyeon-dressup.html','/static/hyeon-princess.html'))

@app.after_request
def kids_fixed_page_viewport(response):
    if not is_kids_page(request.path) or response.status_code != 200 or response.mimetype != 'text/html':
        return response
    response.direct_passthrough = False
    markup = response.get_data(as_text=True)
    if 'id="kids-page-zoom-lock"' in markup:
        return response
    # Remove old viewport declarations so a later tag cannot re-enable page zoom.
    markup = re.sub(r'<meta\b(?=[^>]*\bname\s*=\s*(?:[\'"]viewport[\'"]|viewport\b))[^>]*>', '', markup, flags=re.I)
    # Keep the original charset first and add the lock before any application scripts.
    charset = re.search(r'<meta\b[^>]*\bcharset\s*=[^>]*>', markup, flags=re.I)
    if charset:
        end = charset.end()
        markup = markup[:end] + HEAD + markup[end:]
    else:
        markup = re.sub(r'(<head\b[^>]*>)', lambda m: m.group(1) + '<meta charset="utf-8">' + HEAD, markup, count=1, flags=re.I)
    response.set_data(markup)
    response.headers.pop('ETag', None)
    response.headers.pop('Last-Modified', None)
    response.headers['Cache-Control'] = 'no-store'
    return response
