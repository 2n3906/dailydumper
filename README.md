# dailydumper
Harvest e-mail image attachments in an IMAP folder as Lightroom-ready files.

We will do this in two stages:

1. Using `offlineimap` 1-way sync to mirror a remote IMAP folder to a maildir
on the local machine, then
2. Using the `dailydumper` script to extract all the image/* and video/*
attachments to a directory of files ready for Lightroom import.

The script uses GExiv2 to modify the EXIF metadata in the extracted images
to ensure Lightroom readiness, namely:

* It checks that the image has a valid DateTime and DateTimeOriginal tag;
if not (as is sometimes the case with cameraphone attachments) it will
provide one from the e-mail timestamp.
* It sets the Creator tag to the name of the e-mail sender.
* It sets the Title tag (caption) to a simplified version of the e-mail body text.
* It sets the DocumentName to the Message-ID of the original e-mail.
* It adds a subject tag (presently hard-coded to "Daily")

## Usage

First, copy the provided offlineimap configuration to `~/.offlineimaprc` and edit it.
Run `offlineimap`.  Doing so will mirror your chosen IMAP folder to your local
machine. Note that if you activate `--dry-run` mode the first time, it
will fail.

Then extract the images:

```
./dailydumper.py -m ~/dailydumper-imap-mirror -o ~/dailydumper-lightroom-ready
```

That's all!