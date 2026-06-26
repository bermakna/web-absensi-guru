import threading
import webbrowser
import time
import uvicorn

def buka_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")

threading.Thread(target=buka_browser).start()

uvicorn.run(
    "main:app",
    host="127.0.0.1",
    port=8000,
    reload=False,
    log_config=None
)