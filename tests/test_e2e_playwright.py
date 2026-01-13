import os
import time
import subprocess
import signal
import urllib.request
import pytest
from pathlib import Path


def shutil_exists():
    try:
        import shutil
        import playwright
        return True
    except Exception:
        return False


def wait_for(url, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen(url, timeout=1.0)
            if r.getcode() == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


@pytest.mark.skipif(not shutil_exists(), reason="playwright not installed locally")
def test_e2e_ui(tmp_path):
    # This test requires Playwright and installed browsers:
    #   pip install -r requirements.txt
    #   playwright install
    import shutil
    from playwright.sync_api import sync_playwright

    dbfile = tmp_path / "e2e.db"
    port = 8001
    env = os.environ.copy()
    env["VIBE_DATABASE_URL"] = f"sqlite:///{dbfile}"
    # start server
    cmd = ["./.venv/bin/uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert wait_for(f"http://127.0.0.1:{port}/openapi.json", timeout=10.0)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/ui/")
            # register
            page.fill('#reg_username', 'e2euser')
            page.fill('#reg_display', 'E2E User')
            page.fill('#reg_password', 'password')
            page.click('#btn_register')
            page.wait_for_timeout(300)
            # post
            page.fill('#post_content', 'hello from e2e')
            page.click('#btn_post')
            page.wait_for_timeout(300)
            # refresh and assert feed contains our post
            page.click('#btn_refresh')
            page.wait_for_timeout(300)
            content = page.content()
            assert 'hello from e2e' in content
            browser.close()
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


def shutil_exists():
    try:
        import shutil
        import playwright
        return True
    except Exception:
        return False
