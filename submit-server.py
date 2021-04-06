#!/usr/bin/env python3

'''
  Simple HTTP server that accepts POST request
  from submit.html and stores them in a folder
'''

import traceback
import argparse
import http.server
import cgi
import uuid
import json
import time
import ssl
import os
import re

# for debugging
import cgitb
cgitb.enable()

# byte size of a single submission
INBOX_SIZE_BYTES = 1_000_000_000

# minimum seconds between submissions
SUBMIT_INTERVAL_SEC = 20


last_submission = 0
fn_regex = re.compile(r'^[0-9a-zA-Z_.-]{3,64}$')


def check_file_name(filename):
    return bool(fn_regex.match(filename))

def check_text_value(text):
    return len(text) < 64

def check_file_size(data):
    return len(data) < (10*1000*1000)

def get_total_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size

def store_submission(form):
    global last_submission

    if (time.time() - last_submission) < SUBMIT_INTERVAL_SEC:
        next = int(SUBMIT_INTERVAL_SEC - (time.time() - last_submission))
        return (False, "Please wait {} seconds for the next submission slot!".format(next))

    os.makedirs("/tmp/sticker_submissions", exist_ok=True)

    if get_total_size("/tmp/sticker_submissions") > INBOX_SIZE_BYTES:
        return (False, "Submission directory is full. Alert the maintainer!")

    output = {}

    for key in ["tags", "notes", "notes", "link", "language", "license"]:
        if key in form:
            value = form[key].value.strip()
            if len(value) == 0:
                continue

            if check_text_value(value):
                output[key] = value
            else:
                return (False, "Invalid field {}.".format(key))

    files = {}
    if "files[]" in form:
        entries = form["files[]"]

        # make sure entries is a list
        if isinstance(entries, cgi.FieldStorage):
            entries = [entries]

        if len(entries) > 3:
            return (False, "Too many files.")

        for entry in entries:
            file_name = os.path.basename(entry.filename)
            file_data = entry.value

            if not check_file_size(file_data):
                return (False, "File too big: {}".format(file_name))

            if not check_file_name(file_name):
                return (False, "Invalid file name: {}".format(file_name))

            files[file_name] = file_data

    # store submission here
    path = "/tmp/sticker_submissions/{}".format(uuid.uuid4())

    print("Create directory {}".format(path))
    os.mkdir(path)

    # write json
    if len(output) > 0:
        with open(f"{path}/data.json", "w") as file:
            json.dump(output, file, indent="  ", sort_keys=True)

    if len(files) > 0:
        for file_name, file_data in files.items():
            with open("{}/{}".format(path, file_name), "wb") as file:
                file.write(file_data)

    last_submission = time.time()
    return (True, "Success - Thank you for your contribution!")

class MyHandler(http.server.BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'false')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_POST(self, *args, **kwargs):
        #content_len = int(self.headers.get('content-length'))
        #pdict['CONTENT-LENGTH'] = content_len
        try:
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))

            success = False
            message = 'unhandled data format'

            if ctype == 'multipart/form-data':
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8") # hack
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD':'POST'})
                success, message = store_submission(form)

            body = bytes(message, 'utf-8')
            code = 200 if success else 400

            self.send_response(200)
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Content-type', 'text/plain')
            self.send_header('Content-length', str(len(body)))
            self.end_headers()

            self.wfile.write(body)
        except Exception as e:
            traceback.print_exc()
            print(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--listen", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=4223)
    parser.add_argument("--certfile", default="", help="Private key file in PEM format.")
    parser.add_argument("--keyfile", default="", help="Public key file in PEM format")

    args = parser.parse_args()

    print("Listen on {} port {}".format(args.listen, args.port))

    try:
        server = http.server.HTTPServer((args.listen, args.port), MyHandler)
        if len(args.certfile) > 0 and len(args.keyfile) > 0:
            server.socket = ssl.wrap_socket(server.socket, certfile=args.certfile, keyfile=args.keyfile, server_side=True)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

