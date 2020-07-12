# Google Photos Export
If you've tried exporting your Google Photos to another service like iPhoto or Synology Moments, you'll quickly find a few problems:
- Photo dates are all over the place, messing up the timeline
- Photos from Google Hangouts/GVoice show up in the library
- Deleted (but not purged) images remain


This tool attempts to fix all of that by:
- Creating a separate folder for Voice/Hangouts photos
- Correcting the photo date with the date set in GPhotos

It also gives you a SQLite database to easily explore metadata.

## Notes
- /Trashed contains deleted media, without any subfolder structure.
- /Hangouts contains media from hangout conversations. Subfolders for each convo.
- /Library contains everything else, both photos that were and were not in albums
- /Albums contains a COPY of photos that were also in named albums. If you delete this folder, you'll still have all the photos safe in /Library