#!/usr/bin/env python3

import readline
import hashlib
import signal
import json
import sys
import os


# subset of https://spdx.org/licenses/
valid_licenses = ["", "CC0-1.0", "Unlicense", "CC-BY-3.0"]
valid_languages = ["", "dutch", "english", "french", "german"]

# Only works on *nix systems
def rlinput(prompt, prefill=""):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def check_duplicate_images(db_images, images_set):
    def hash_file(path):
        with open(path, "rb") as file:
            hasher = hashlib.sha1()
            hasher.update(file.read())
            return hasher.hexdigest()

    duplicates_found = False
    hashes = {}
    for image in images_set:
        file_hash = hash_file("images/{}".format(image))
        if file_hash in hashes:
            other_image = hashes[file_hash]
            print("Files identical: 'images/{}' and 'images/{}'".format(image, other_image))

            if image in db_images:
                if other_image in db_images:
                    print(" Both already in database. :/")
                else:
                    print(" Remove: {}".format(other_image))
            else:
                if other_image in db_images:
                    print(" Remove: {}".format(image))
                else:
                    print(" Both are not in database. Remove one of them.")

            duplicates_found = True

    return duplicates_found

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

def is_valid_tags(tags):
    if tags.lower() != tags:
        print("Only lower case letters please.")
        return False
    return True

def is_valid_license(license):
    if license not in valid_licenses:
        print("Valid licenses: {}".format(valid_licenses))
        return False
    return True

def is_valid_language(language):
    if language not in valid_languages:
        print("Valid languages: {}".format(valid_languages))
        return False
    return True

def is_valid_link(link):
    if not link.startswith("https://"):
        print("Link must start with https://")
        return False
    return True

def ask_value(prompt, is_valid, prefill=""):
    value = rlinput(prompt, prefill)
    while not is_valid(value):
        value = rlinput(prompt, value)
    return value.strip()

def add_image(i, n, prev, db, image):
    print("[{}/{}] 'images/{}'".format(i, n, image))

    '''
    cool_image.front.png => ("cool_image", "front.png")
    '''
    def split_ext(name):
        i = name.find('.')
        if i == -1:
            return (name, "")
        else:
            return (name[:i], name[i+1:])

    def endswith_any(image, exts):
        for ext in exts:
            if image.endswith(ext):
                return True
        return False

    if not endswith_any(image, [".svg", ".pdf", ".jpg", ".png", ".eps", ".tif"]):
        print("File has invalid format extension => ignore")
        return 0

    name, ext = split_ext(image)

    if len(ext) == 0:
        print("File has no extension => ignore")
        return 0

    # image name exists
    if name in db:
        obj = db[name]
        answer = ask_value("Image exists with extensions {}. Add '{}' to image entry? [Y/n] ".format(obj["exts"], ext),
            lambda v: v in ["", "Y", "n"], "")
        if answer == "" or answer == "Y":
            obj["exts"].append(ext)
            print("done")
            return 1
        else:
            print("ignore")
            return 0

    default = get_defaults_entry(db, prev[0], image)

    tags = default.get("tags", "")
    title = default.get("title", "")
    author = default.get("author", "")
    license = default.get("license", "")
    language = default.get("language", "")
    link = default.get("link", "")

    while True:
        tags = ask_value("Tags: ", is_valid_tags, tags)
        title = ask_value("Title: ", is_valid_title, title)
        author = ask_value("Author: ", is_valid_author, author)
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

    obj = {"exts": [ext]}

    if len(tags) > 0:
        obj["tags"] = tags
    if len(title) > 0:
        obj["title"] = title
    if len(language) > 0:
        obj["language"] = language
    if len(author) > 0:
        obj["author"] = author
    if len(license) > 0:
        obj["license"] = license
    if len(link) > 0:
        obj["link"] = link

    db[name] = obj
    prev[0] = obj

    print("done")

    return 1

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
        for filename in os.listdir("images/"):
            images.add(filename)
        return images

    def get_db_set(db):
        images = set()
        for name, obj in db.items():
            for ext in obj["exts"]:
                images.add("{}.{}".format(name, ext))
        return images


    db = get_database()
    images = get_image_set()

    db_images = get_db_set(db)
    new_images = list(images - db_images)
    new_images.sort()

    if check_duplicate_images(db_images, images):
        print("Please remove duplicate files first!")
        return

    if len(new_images) == 0:
        print("Read {} entries, no new images => abort".format(len(db_images)))
        return

    old_image_count = len(db_images)
    new_image_count = 0

    def sigint_handler():
        if new_image_count > 0:
            print("\nNothing saved")
        sys.exit(0)

    # Exit Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda sig, frame: sigint_handler())

    answer = input("Start to add {} new images [Y, n]? ".format(len(new_images)))
    if answer == "n":
        return

    prev = [{}] # list for pass by reference
    for i, image in enumerate(new_images):
        ret = add_image(i + 1, len(new_images), prev, db, image)
        if ret > 0:
            new_image_count += 1
        if ret < 0:
            break

    save_database(db, new_image_count)

if __name__ == "__main__":
    main()
