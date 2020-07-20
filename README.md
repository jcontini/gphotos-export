# Why I made this
I tried exporting my Google Photos to another service. It didn't go so well:
- Timeline was real messed up - lots of photos defaulted to import date
- There were a LOT of duplicates, caused by albums & edited photos
- Photos from Hangouts were mixed in with everything else

# What it does
Goes through a Takeout archive of GPhotos and:
1. Matches original media files to their metadata files (.json)
   - Find the GPhotos timestamp for each media file
   - Skips the edited versions (these make lots of duplicates)
   - Stores findings & organization plan in a local SQLite database.

2. Organizes media into folders (GPhotos/):
   - **Library/{Year}** - All media in folders by year
   - **Albums/{Album Name}** - A COPY of media in albums (they're also in /Library)
   - **Hangouts/{Conversation Name}** - Media from Google Hangouts chats
   - **Trashed** - Trashed media that was not permanently deleted

3. Updates the dates/times for each media file from GPhotos timestamp
   - Set file modification datetime (works on all file types)
   - If the file supports Exif (eg JPEG), also set the Exif.DateTimeOriginal

Limitations from Google:
- Albums only contain media that you uploaded. Shared albums do not included photos uploaded by others.
- Google Hangouts only includes media sent, not received
- Files can exist in multiple albums, so are downloaded for each album (+ Library)

Limitations from me:
- **I've only tested this on a Mac**. It might run on Linux. I doubt it will on Windows.
- You'll need to have Python 3 installed (already included on newer Macs)

# How to use

## Prepare GPhotos for Takeout
Optional steps to save space on your computer & make organizing easier:
1. Delete any [Albums](https://photos.google.com/albums) you don't need, so that the media isn't downloaded twice.
2. Check your [Archive](https://photos.google.com/archive) and delete any photos you don't want to keep.
3. Check your [GPhotos Trash](https://photos.google.com/trash) to permanently delete any files you don't need.

Then, request a Google Photos archive from [Google Takeout](https://takeout.google.com/?pli=1). This will download archives (zip files) with all of your photos & videos. Splitting into multiple files is fine - I did the 2GB option by email. 

It can take a few days for Google to prepare your archive, some come back after you've downloaded all the zip files to your computer.

## Do the export
This will take a lot of space on your computer! A good way to estimate how much space you will need is to add up the size of the archives you just downloaded, and multiply that by 1.3. In my case I had about 12GB of archives which expanded to 15GB of media files. So I needed about 27GB free - enough for both the archives and the export.

Once you've got the archives downloaded and the free space available:

1. Open the terminal (MacOS: Applications > Utilities > Terminal) 
2. Run `pip install gphotos-export` (requires Python 3)
3. Navigate to the folder with your Takeout archives (zip files), eg `cd ~/Downloads/Takeout`
4. Run `gphotos-export ~/Pictures` to export to a folder of your choosing (eg ~/Pictures)
5. Give it a few minutes to run and check out your handiwork!