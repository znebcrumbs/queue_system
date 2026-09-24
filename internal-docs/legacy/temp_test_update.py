import re
import requests

s = requests.Session()
login_url = 'http://127.0.0.1:8000/accounts/login/'
resp = s.get(login_url)
print('login page', resp.status_code)
match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text)
if not match:
    raise SystemExit('csrf not found')
csrf = match.group(1)
post = s.post(login_url, data={
    'username': 'superadmin',
    'password': 'superadmin123',
    'csrfmiddlewaretoken': csrf,
}, headers={'Referer': login_url})
print('login', post.status_code, post.url)
url = 'http://127.0.0.1:8000/queues/update/1/'
headers = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': s.cookies.get('csrftoken'),
}
resp = s.post(url, json={'status': 'IN_PROGRESS'}, headers=headers)
print('update', resp.status_code, resp.headers.get('Content-Type'))
print(resp.text)
