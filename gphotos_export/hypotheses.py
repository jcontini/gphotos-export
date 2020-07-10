import sqlite_utils

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def can_delete_albums():
    filenames_check = []
    for album in db['albums'].rows:
        if album['newfolder'][:7]=='Albums/':
            print('\n'+'='*80 + '\nAlbum: '+album['newfolder']+'\n'+'='*80)
            album_filenames = db['media_files'].rows_where('newfolder = ?', [album['newfolder']])
            for album_filename in album_filenames:
                print('\nFilename: '+album_filename['filename']+'\n'+'-'*20)
                match = 0
                match_files = db['media_files'].rows_where('filename = ?', [album_filename['filename']])
                for match_file in match_files:
                    print('> ' + match_file['path'])
                    match+=1
            filenames_check.append({'filename': album_filename['filename'],'album': album['newfolder'],'count': match})
    
    for fname in filenames_check:
        print(fname)

    #Result: No. Not all album files necessarily exist in non-album folders (eg /Archive)