import enhancements_wrapper as enhancements
import app as base

app = enhancements.app

# This family site is intentionally open: no admin session is required.
base.admin = lambda: True
base.must = lambda: None


def open_nav():
    return '<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b><div class="nav"><a href="/">홈</a><a href="/past">과거 여행</a><a href="/future">향후 여행</a><a href="/travel-map">여행 지도</a><a href="/travel-search">검색</a><a href="/calendar">가족 달력</a><a href="/riley">지유 주간 일정</a></div></nav></header>'

base.nav = open_nav

# Disable the old login/logout pages as well, so authentication disappears
# from both navigation and direct URL access.
def _go_home():
    return base.redirect('/')

for rule in list(app.url_map.iter_rules()):
    if rule.rule in ('/login', '/logout'):
        app.view_functions[rule.endpoint] = _go_home
