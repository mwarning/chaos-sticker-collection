#!/usr/bin/env python3

import readline
import hashlib
import signal
import json
import glob
import sys
import os


assert sys.version_info >= (3, 6), "Python version too old. Python >=3.6.0 needed."


# subset of https://spdx.org/licenses/
valid_licenses = ["", "CC0-1.0", "Unlicense", "CC-BY-3.0", "CC-BY-NC-SA-3.0", "CC-BY-SA-4.0", "CC-BY-SA-3.0", "GFDL-1.3-or-later", "LAL-1.3"]
valid_languages = ["", "dutch", "english", "french", "german"]

# Only works on *nix systems
def rlinput(prompt, prefill=""):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def check_duplicate_images():
    def hash_file(path):
        with open(path, "rb") as file:
            hasher = hashlib.sha1()
            hasher.update(file.read())
            return hasher.hexdigest()

    dups_found = False
    hashes = {}
    for entry in glob.glob("images/", recursive=True):
        if os.path.isfile(entry):
            hash = hash_file(entry)
            if hash in hashes:
                print("Warning: Files identical: '{}' and '{}'".format(entry, hashes[hash]))
                dups_found = True
            else:
                hashes[hash] = entry
    return dups_found

def get_defaults_entry(db, prev, image):
    name, ext = os.path.splitext(image)
    common_prefix = ''
    common_key = ''

    for key in db:
        p = os.path.commonprefix([key, name])
        if len(p) > len(common_prefix):
            common_prefix = p
            common_key = key

    if len(common_prefix) > 4 and ((100 * len(common_prefix)) / len(name)) > 60:
        # common prefix is >60% of the image name length
        return db[common_key]
    else:
        # use previous image meta data as default
        return prev

def is_valid_author(author):
    return True

def is_valid_title(author):
    return True

def is_valid_notes(notes):
    return True

def is_valid_tags(tags):
    if tags.lower() != tags:
        print("Only lower case letters please.")
        return False
    return True

def is_valid_license(licenses):
    for i, license in enumerate(licenses.split("/")):
        if i >= 2:
            print("Only two licenses allowed")
            return False
        if license not in valid_licenses:
            print("{} no in {}".format(license, valid_licenses))
            return False
    return True

def is_valid_language(language):
    if language not in valid_languages:
        print("Valid languages: {}".format(valid_languages))
        return False
    return True

def is_valid_link(link):
    if len(link) > 0:
        if not link.startswith("https://") and not link.startswith("http://"):
            print("Link must start with https://")
            return False
    return True

def ask_value(prompt, is_valid, prefill=""):
    value = rlinput(prompt, prefill)
    while not is_valid(value):
        value = rlinput(prompt, value)
    return value.strip()

# add or update image
def handle_image(i, n, prev, db, image):
    print('#######################################')
    print('[{}/{}] "images/{}"'.format(i, n, image))
    print('#######################################')

    # get default values
    default = get_defaults_entry(db, prev[0], image)

    tags = default.get("tags", "")
    title = default.get("title", "")
    author = default.get("author", "")
    notes = default.get("notes", "")
    license = default.get("license", "")
    language = default.get("language", "")
    link = default.get("link", "")

    while True:
        tags = ask_value("Tags: ", is_valid_tags, tags)
        title = ask_value("Title: ", is_valid_title, title)
        author = ask_value("Author: ", is_valid_author, author)
        notes = ask_value("Notes: ", is_valid_notes, notes)
        license = ask_value("License: ", is_valid_license, license)
        language = ask_value("Language: ", is_valid_language, language)
        link = ask_value("Link: ", is_valid_link, link)

        answer = ask_value("next (1), again (2), skip (3), exit (4): ",
            lambda v: v in ["1", "2", "3", "4"], "1")

        if answer == "1":
            break
        if answer == "2":
            pass
        if answer == "3":
            return 0
        if answer == "4":
            return -1

    obj = {}

    if len(tags) > 0:
        obj["tags"] = tags
    if len(title) > 0:
        obj["title"] = title
    if len(language) > 0:
        obj["language"] = language
    if len(author) > 0:
        obj["author"] = author
    if len(notes) > 0:
        obj["notes"] = notes
    if len(license) > 0:
        obj["license"] = license
    if len(link) > 0:
        obj["link"] = link

    db[image] = obj
    prev[0] = obj

    print("done")

    return 1

def add_previews(db):
    def find_images_paths(name):
        images = []
        for entry in glob.glob("images/{}/*".format(name), recursive=True):
            if not os.path.isfile(entry):
                continue
            if entry.endswith(".pdf") or entry.endswith(".png") or entry.endswith(".jpg") or entry.endswith(".svg"):
                images.append(entry)
        return images

    for name in db:
        if not os.path.isfile("images/{}/preview.webp".format(name)):
            image_paths = find_images_paths(name)
            print("Create preview image: 'images/{}/preview.webp'".format(name))

            done = False
            for path in image_paths:
                rc = os.system("convert -resize 300 '{}' 'images/{}/preview.webp'".format(path, name))
                if rc == 0:
                    done = True
                    break

            if not done:
                if len(image_paths) == 0:
                    print("No image found for images/{}/preview.webp".format(name))
                else:
                        print("Failed to create preview for images/{}/preview.webp".format(name))

def update_file_listings(path, create_index=False):
    entries = []
    for entry in glob.glob("{}/*".format(path)):
        if not entry.endswith("/index.html"):
            entries.append(entry)

    if create_index:
        with open("{}/index.html".format(path), "w") as file:
            name = os.path.basename(path)
            file.write("<!DOCTYPE html>\n")
            file.write("<html>\n <head>\n")
            file.write("  <title>Files for {}</title>\n".format(name))
            file.write("  <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n")
            file.write("  <link rel=\"stylesheet\" href=\"../../listing.css\">\n")
            file.write(" </head>\n <body>\n")
            file.write("  <h1>Files for {}</h1>\n".format(name))
            file.write("  <hr>\n  <ul>\n")
            for entry in entries:
                name = os.path.basename(entry)
                if name != "preview.webp":
                    file.write("   <li><a href=\"{}\">{}</a></li>\n".format(name, name))

            file.write("  </ul>\n </body>\n</html>\n")

    for entry in entries:
        if os.path.isdir(entry):
            update_file_listings(entry, True)

def save_database(db, new_image_count):
    # write anyway, this will format manual edits to data.json
    with open("data.json", "w") as outfile:
        json.dump(db, outfile, indent="  ", sort_keys=True)
        print("Wrote {} new entries to data.json => done".format(new_image_count))

def main():
    def get_database():
        with open("data.json") as file:
            return json.load(file)

    def get_image_set():
        images = set()
        for image in os.listdir("images/"):
            if os.path.isdir("images/{}".format(image)):
                images.add(image)
        return images

    db = get_database()
    db_images = db.keys()

    images = []
    if len(sys.argv) > 1:
        for image in sys.argv[1:]:
            if not image.startswith("images/"):
                print("Outside images folder: {}".format(image))
                sys.exit(1)
            elif os.path.isdir(image):
                images.append(os.path.basename(image))
            else:
                print("folder {} does not exist".format(image))
                sys.exit(1)
    else:
        images = list(get_image_set() - set(db_images))

    images.sort()

    if check_duplicate_images():
        print("Please remove duplicate files first!")
        return

    old_image_count = len(db_images)
    new_image_count = 0

    def sigint_handler():
        if new_image_count > 0:
            print("\nNothing saved")
        print("")
        sys.exit(0)

    if len(images) > 0:
        # Exit Ctrl+C gracefully
        signal.signal(signal.SIGINT, lambda sig, frame: sigint_handler())

        answer = input("Start to add {} new image folders [Y, n]? ".format(len(images)))
        if answer == "n":
            return

        prev = [{}] # use list for pass by reference
        for i, image in enumerate(images):
            ret = handle_image(i + 1, len(images), prev, db, image)
            if ret > 0:
                new_image_count += 1
            if ret < 0:
                break

    add_previews(db)
    update_file_listings("images")

    save_database(db, new_image_count)

if __name__ == "__main__":
    main()
