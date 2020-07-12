import os, glob, json, sqlite_utils, zipfile, re, time
from sqlite_utils.db import NotFoundError

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def index_zip_media(zf):
    with zipfile.ZipFile(zf, 'r') as archive:
        zipname = os.path.basename(zf)
        media=[];meta=[]
        files = archive.namelist()
        nomedia = ["print-subscriptions", "shared_album_comments"]

        for filepath in files:
            ext = os.path.splitext(filepath)[1]
            if ext == '.json':
                if not any(x in filepath for x in nomedia):
                    meta.append({
                        'meta_path':filepath,
                        'archive':zipname
                    })
            elif ext != '.html':
                media.append({
                    'media_path':filepath,
                    'filename': filepath.rsplit('/',1)[1],
                    'ext': str.upper(ext[1:]),
                    'archive':zipname,
                    'edited':0
                    })
        db['media_files'].upsert_all(media,alter=True,pk="media_path")
        db['meta_files'].upsert_all(meta,alter=True,pk="meta_path")

def get_media_meta(path):
    print(">> Parsing metadata from archives...")
    if "archives_meta" not in db.view_names():
        db.create_view("archives_meta", """select archive from meta_files group by archive""")
    for row in db["archives_meta"].rows:
        with zipfile.ZipFile(path+row["archive"], 'r') as archive:
            for row in db['meta_files'].rows_where("archive = ?", [row["archive"]]):
                with archive.open(row["meta_path"]) as metafile:
                    r = json.loads(metafile.read())
                    try:
                        if 'metadata' in row["meta_path"]:
                            # Extract Album info
                            d = {
                                "type": 'album',
                                "title": r["albumData"]["title"],
                                "description": r["albumData"]["description"]
                            }
                            db['meta_files'].update(row["meta_path"],d, alter=True)
                        else:
                            # Extract Media info
                            ts_taken = time.gmtime(int(r["photoTakenTime"]["timestamp"]))
                            d = {
                                "type": 'media',
                                "year": int(time.strftime("%Y", ts_taken)),
                                "title": r["title"],
                                "ts_taken": int(r["photoTakenTime"]["timestamp"]),
                                "ts_created": int(r["creationTime"]["timestamp"]),
                                "ts_modified": int(r["modificationTime"]["timestamp"]),
                                "tsf_taken": str(time.strftime("%Y-%m-%d %H:%M:%S", ts_taken)),
                                "geo_lat": r["geoDataExif"]["latitude"],
                                "geo_long": r["geoDataExif"]["longitude"],
                                "geo_alt": r["geoDataExif"]["altitude"],
                                "description": r["description"],
                                "imageViews": int(r.get("imageViews",0)),
                                "trashed": r.get("trashed",0)
                            }
                            db['meta_files'].update(row["meta_path"],d, alter=True)

                    except:
                        print("Issue parsing %s" % row["meta_path"])
                        pass

def check_meta(metapath):
    try:
        db['meta_files'].get(metapath)
        return True
    except NotFoundError:
        return False

def match_meta():
    print('>> Matching media files with metadata...')
    if "nomatch" not in db.view_names():
        db.create_view("nomatch", """select * from media_files where metapath is null and edited is not 1""")
    if "matches" not in db.view_names():
        db.create_view("matches", """SELECT * FROM media_files as media
                                    LEFT JOIN meta_files AS meta ON media.metapath=meta.meta_path
                                    WHERE metapath is not null""")

    for r in db['media_files'].rows:
        fullpath, ext = os.path.splitext(r['media_path'])
        folder = fullpath.rsplit('/',1)[0] + '/'
        filename = fullpath.rsplit('/',1)[1] + ext

        #Skip edited versions
        if '-edited' in filename:
            db['media_files'].update(r['media_path'],{"edited":1},alter=True)
            continue
        
        #Try the default json path
        metapath = folder + filename +'.json'
        if check_meta(metapath):
            db['media_files'].update(r['media_path'],{"metapath": metapath}, alter=True)
            continue

        #Handle case: Metafile trims filename at 46 characters
        if len(filename) > 46:
            filename = filename[:46]
            metapath = folder + filename +'.json'
            if check_meta(metapath):
                db['media_files'].update(r['media_path'],{"metapath": metapath}, alter=True)
                continue
            
        #Handle case: Hangouts with account_id drops extension
        if 'account_id' in filename:
            filename = filename.rsplit(ext,1)[0]
            metapath = folder + filename +'.json'
            if check_meta(metapath):
                db['media_files'].update(r['media_path'],{"metapath": metapath}, alter=True)
                continue

        #Handle case: When google adds (1), (2) etc to filename
        re_pattern = '\(\d\)\.'
        re_matches = re.findall(re_pattern,filename)
        if len(re_matches) > 0:
            metapath = fullpath.rsplit('(',1)[0] + ext + '.json'
            if check_meta(metapath):
                db['media_files'].update(r['media_path'],{"metapath": metapath}, alter=True)
                continue

        #Handle other cases where the extension is dropped in metapath
        metapath = fullpath + '.json'
        if check_meta(metapath):
            db['media_files'].update(r['media_path'],{"metapath": metapath}, alter=True)
            continue

        #Catch-all
        print("No match: %s" % filename)

    unmatched = db['nomatch'].count
    matched = db['matches'].count
    print('--- Media Report ---')
    print("%s media files matched with metadata" % matched)
    print("%s remaining with no match" % unmatched)

def prep_folder_structure():
    print('>> Preparing new folder structure...')
    re_pattern = '[0-9]{4}-[0-9]{2}-[0-9]{2}'
    for r in db['media_files'].rows_where("metapath is not null"):
        current_folder = r['media_path'].rsplit('/',2)[1]
        meta = db['meta_files'].get(r['metapath'])
        lib_add = 0

        # If Hangouts, put in /Hangouts folder
        if current_folder[:8] == 'Hangout_':
            subfolder = current_folder[9:]
            folder = 'Hangouts/' + subfolder

        # If file is in trash, put in /Trash folder
        elif meta['trashed'] == 1:
            folder = 'Trashed/' + current_folder

        # If current folder has 0000-00-00 format, put in Library/[year] folders
        elif re.match(re_pattern,current_folder[:10]):
            folder = 'Library/' + str(meta['year'])
            lib_add = 1

        # Otherwise, put in Album folder
        else:
            folder = 'Albums/' + current_folder
        db['media_files'].update(r['media_path'],{"newfolder": folder, "lib_add": lib_add}, alter=True)

def add_album_media():
    print('>> Scanning Albums for images not in library...')
    library = []
    for r in db['matches'].rows_where("newfolder LIKE 'Library/%'"):
        library.append({'filename': r['filename'],'ts_taken': r['ts_taken'], 'media_path': r['media_path']})

    for r in db['matches'].rows_where("newfolder LIKE 'Albums/%'"):
        lib_add = 1;source = ''
        lib_filenames = [i for i in library if i['filename'] == r['filename']]
        if len(lib_filenames) > 0:
            for possible_match in lib_filenames:
                if r['ts_taken'] == possible_match['ts_taken']:
                    lib_add = 0
                    source = possible_match['media_path']

        db['media_files'].update(r['media_path'],{"lib_add": lib_add, "source": source}, alter=True)

def prep_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def write_exif():
    todo = '''
    - open the media file
    - update the exif data
    - save the file
    '''

def export_files(path):
    print(">> Extracting files with EXIF data to new folder structure...")
    if "archives_media" not in db.view_names():
        db.create_view("archives_media", """select archive from media_files group by archive""")
    for row in db["archives_media"].rows:
        with zipfile.ZipFile(path+row["archive"], 'r') as archive:
            for row in db['matches'].rows:
                with archive.open(row["meta_path"]) as metafile:
                    pass #todo

    for r in db['matches'].rows:
        prep_folder(r['newfolder'])
        #TODO zip.extract pathfile to newfolderpath
        #write_exif('...')
        if r['newfolder'][7:] == 'Albums/' and r['lib_add'] == 1:
            lib_folder = 'Library/' + str(r['year'])
            prep_folder(lib_folder)
            #TODO zip.extract pathfile to newfolderpath
            #write_exif('...')


def fullrun(path):
    zipfiles = glob.glob(path+'*.zip')
    for zf in zipfiles:
        index_zip_media(zf)
    get_media_meta(path)
    match_meta()
    prep_folder_structure()
    add_album_media()
    #export_files(path)

# Notes to make clear to users:
# /Trashed contains deleted files. NOT in lib
# /Hangouts contains files from hangout conversations. NOT in lib.
# /Library contains everything else, both photos that were and were not in albums

# /Albums contains a COPY of photos that were also in named albums. All files in here are safe in /Library as well.