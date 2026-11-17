# Test program for the RNG microservice
# Run this:  python test_rng.py
# It starts the RNG microservice by itself, tests it, then shuts it down.

import json
import os
import signal
import subprocess
import sys
import time
import requests

RNG_URL = "http://127.0.0.1:5000/random"


def find_service_dir(name, key_file):
    # looks for the microservice in this folder, or in a folder next to this one, e.g. RNG_Microservice
    # (also works if it was downloaded as a zip and ends in -main)
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(os.path.join(tests_dir, key_file)):
        return tests_dir  # this test is inside the microservice's own folder
    parent = os.path.dirname(tests_dir)
    for folder in sorted(os.listdir(parent)):
        path = os.path.join(parent, folder)
        if folder.lower().startswith(name.lower()) and os.path.isfile(os.path.join(path, key_file)):
            return path
    raise SystemExit(f"Could not find the {name} folder. Put it in the same folder as {os.path.basename(tests_dir)}.")


SERVICE_DIR = find_service_dir("RNG_Microservice", "server.py")


# ---------------- Terminal output ----------------

if os.name == "nt":
    os.system("")  # turns on colors in the Windows terminal
USE_COLOR = sys.stdout.isatty()
test_number = 0
next_part = None


def color(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def part(title):
    global next_part
    next_part = title


def test(title):
    global test_number, next_part
    test_number += 1
    upcoming = f"TEST {test_number}: {title}"
    if next_part:
        upcoming = f"{next_part}  >  {upcoming}"
    print(color("\n  Next up: ", "2") + color(upcoming, "1;33"))
    input(color("  Press Enter to start...", "2"))

    if next_part:
        print("\n\n" + color("#" * 60, "1;35"))
        print(color(f"   {next_part}", "1;35"))
        print(color("#" * 60, "1;35"))
        next_part = None
    print("\n" + color("-" * 60, "36"))
    print(color(f" TEST {test_number}: {title}", "1;36"))
    print(color("-" * 60, "36"))


def result(text):
    print(color(f"  => {text}", "1;32"))


def check_rejected(status):
    if status is not None and 400 <= status < 500:
        result(f"PASS: the microservice rejected the bad input ({status}), no crash")
    else:
        print(color(f"  => UNEXPECTED: got status {status}", "1;31"))


# ---------------- Starting / stopping the microservice ----------------

def check_service():
    try:
        return requests.get(RNG_URL, params={"min": 1, "max": 2}, timeout=2).status_code
    except requests.exceptions.ConnectionError:
        return None


def start_service():
    status = check_service()
    if status == 200:
        print(color("[setup] RNG microservice is already running, using that one.", "2"))
        return None
    if status is not None:
        raise SystemExit("Port 5000 is being used by something else (the Sound Player microservice?). Stop it first.")

    print(color("[setup] Starting the RNG microservice (python server.py)...", "2"))
    proc = subprocess.Popen([sys.executable, "server.py"], cwd=SERVICE_DIR,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=(os.name != "nt"))
    for _ in range(30):
        if check_service() == 200:
            print(color("[setup] RNG microservice is running!", "2"))
            return proc
        time.sleep(0.5)
    stop_service(proc)
    raise SystemExit("The RNG microservice did not start. Try running server.py by itself to see the error.")


def stop_service(proc):
    if proc is None:
        return
    print(color("\n[setup] Shutting down the RNG microservice...", "2"))
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGTERM)


# ---------------- Talking to the microservice ----------------

def send(params):
    # REQUEST: send a GET request with min and max as query parameters
    full_url = requests.Request("GET", RNG_URL, params=params).prepare().url
    print(color("  -> REQUEST ", "1;34") + f"  GET {full_url}")
    try:
        response = requests.get(RNG_URL, params=params, timeout=5)
    except requests.exceptions.ConnectionError:
        print(color("  X  Could not connect to the RNG microservice.", "1;31"))
        return None, None

    # RECEIVE: the microservice sends back JSON
    try:
        data = response.json()
        shown = json.dumps(data, indent=2)
    except ValueError:
        data = None
        shown = "(response was not JSON)"

    code = response.status_code
    code_color = "1;32" if code < 300 else "1;33" if code < 500 else "1;31"
    print(color(f"  <- RESPONSE  {code} {response.reason}", code_color))
    for line in shown.splitlines():
        print("     " + line)
    return code, data


def get_random_number(low, high):
    status, data = send({"min": low, "max": high})
    if status == 200:
        return data["result"]
    return None


# ---------------- The tests ----------------

def run_tests():
    part("PART 1: NORMAL USE")

    test("Roll a die (min=1, max=6)")
    number = get_random_number(1, 6)
    result(f"Rolled a die and got: {number}")

    test("Get 5 numbers between 1 and 100")
    results = []
    for i in range(5):
        results.append(get_random_number(1, 100))
    result(f"All 5 numbers received: {results}")

    test("Negative numbers (min=-50, max=50)")
    number = get_random_number(-50, 50)
    result(f"Number between -50 and 50: {number}")

    part("PART 2: FAIL CASES (bad input)")

    test("min is bigger than max")
    status, _ = send({"min": 10, "max": 5})
    check_rejected(status)

    test("min and max are the same")
    status, _ = send({"min": 5, "max": 5})
    check_rejected(status)

    test("Missing the max parameter")
    status, _ = send({"min": 1})
    check_rejected(status)

    test("No parameters at all")
    status, _ = send({})
    check_rejected(status)

    test("Words instead of numbers")
    status, _ = send({"min": "one", "max": "ten"})
    check_rejected(status)

    test("Decimals instead of whole numbers")
    status, _ = send({"min": 1.5, "max": 9.5})
    check_rejected(status)

    part("PART 3: IS IT STILL RUNNING AFTER THE BAD CALLS?")

    test("Normal call after all the bad ones")
    number = get_random_number(1, 6)
    if number is not None:
        result(f"Yes! It still works and rolled: {number}")


print(color("\n========== RNG Microservice Test ==========\n", "1"))
service = start_service()
try:
    run_tests()
finally:
    stop_service(service)
print(color("\n========== Done testing RNG microservice ==========", "1"))
