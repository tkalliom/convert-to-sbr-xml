# convert-to-sbr-xml
A script for converting SMS/MMS/call history backups into the XML format of Android SMS Backup &amp; Restore. Woefully undertested, and provided as-is! Dataloss at input stage should be improbable, as anything is opened read-only, but the import to Android stage is a question mark.

## Supported inputs

At the moment, there is support for Sailfish `commhistory.db` files. From these, SMS, calls, and MMS with locally stored contents and a readable SMIL file are supported. This means that some MMS are skipped.

## Usage

`python __main__.py [--type {smses,calls}] infile [infile ...]`

By default, all calls and messages are read and output into two files; `calls-timestamp-xml` and `smses-timestamp-xml`. You can use the `type` switch to only get one.

If there are MMS to parse, the `commhistory` `data` directory must be in the current working directory.

## Development notes

The output is an XML in the format used by the SMS Backup & Restore tool for Android. It is seemingly a straightforward port of Android messaging databases into an XML format. Unfortunately, there is no documentation on which fields can be left out and what need fillers like the string `"null"` or a zero integer. [Sms-dump](https://together.jolla.com/question/54249/how-to-saving-sms-text-conversations/) and [Windows Phone to Android message importer](https://gist.github.com/ovatsus/2dd82172dcd8308d559c) were used for reference and the findings are in the two XML Schema files, but it is likely they are not perfect. Future development idea: automatically validate the output XML against these schemas (since this app is untested, you may want to do this manually).

The support for individual formats is decoupled, so support for another format should be straightforward. If that is done, this application can be used to merge inputs in different formats into one output XML.

The inputs are treated as binary. This means that e.g. line breaks as `\n` or `\r\n` are preserved, mirroring the SMS Backup & Restore behavior. It seems that e.g. messages originating from Nokia phones have `\n` linebreaks, while Windows Phone produces `\r`s.