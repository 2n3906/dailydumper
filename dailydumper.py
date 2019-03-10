#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract Lightroom-ready images from a mirrored IMAP folder."""

__author__ = 'Scott Johnston'
__version__ = '0.0.1'

import os
import sys
import argparse
import mailbox
import email
from email import message_from_binary_file, policy, utils
import string
import gi
gi.require_version('GExiv2', '0.10')
from gi.repository import GExiv2
import inscriptis # for HTML->TXT

def simplify(text, whitespace=string.whitespace, delete=""):
    """Returns the text with multiple spaces reduced to single spaces."""
    result = []
    word = ""
    for char in text:
        if char in delete:
            continue
        elif char in whitespace:
            if word:
                result.append(word)
                word = ""
        else:
            word += char
    if word:
        result.append(word)
    return " ".join(result)

def extract_images(msg, output_path):
    message_id = msg['message-id'].strip()[1:-1] # strip <>
    message_date = utils.parsedate_to_datetime(msg['date'])
    message_from_name = msg['from'].addresses[0].display_name
    message_subj = msg.get('subject', '').strip()
    print("subject:", message_subj)

    # extract simplified message body
    try:
        if msg.get_body(preferencelist=('html', 'plain')).get_content_type() == 'text/html':
            #print('Debug: using text/html')
            message_body = simplify(inscriptis.get_text(msg.get_body(preferencelist=('html', 'plain')).get_content()))
        else:
            #print('Debug: using text/plain')
            message_body = simplify(msg.get_body(preferencelist=('html', 'plain')).get_content())
    except:
        message_body = None

    # loop through message parts looking for images
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type.startswith('image') or content_type.startswith('video'):
            filename_original = part.get_filename().lower()
            filename_new = os.path.join(output_path, message_date.strftime('%Y-%m-%d-') + filename_original)
            if not os.path.isfile(filename_new):
                print('Parsing attachment {} --> {}'.format(filename_original, filename_new))
                img = part.get_content()
                with open(filename_new, 'wb') as f:
                    f.write(img)
                m = GExiv2.Metadata()
                m.open_path(filename_new)
                if m.get_tag_string('Exif.Image.DateTime') is None:
                    # set it!
                    m.set_tag_string('Exif.Image.DateTime', message_date.strftime('%Y:%m:%d %H:%M:%S'))
                if m.get_tag_string('Exif.Photo.DateTimeOriginal') is None:
                    # set it!
                    m.set_tag_string('Exif.Photo.DateTimeOriginal', message_date.strftime('%Y:%m:%d %H:%M:%S'))
                m.set_tag_string('Xmp.dc.creator', message_from_name)
                m.set_tag_string('Xmp.dc.title', message_subj)
                if message_body:
                    m.set_tag_string('Xmp.dc.description', message_body)
                m.set_tag_string('Xmp.dc.subject', 'Daily') # set a keyword!
                m.set_tag_string('Exif.Image.DocumentName', message_id)
                m.save_file(filename_new)
            else:
                print('Skipping attachment {} (already exists)'.format(filename_original))

def main(mailbox_path, output_path):
    """Main program logic."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    inbox = mailbox.Maildir(mailbox_path, factory=None, create=False)
    for key in inbox.iterkeys():
        try:
            message = inbox[key]
        except email.errors.MessageParseError:
            continue                # The message is malformed. Just leave it.
        msg = email.message_from_bytes(message.as_bytes(), policy=policy.default)
        extract_images(msg, output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-m', '--maildir-path', help="Maildir mailbox path (from which to extract images)", required=True)
    parser.add_argument('-o', '--output-path', help="Output directory (where Lightroom-ready images go)", required=True)
    args = parser.parse_args()

    main(args.maildir_path, args.output_path)
