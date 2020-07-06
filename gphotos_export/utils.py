import os, glob, json, sqlite_utils, zipfile, re
from sqlite_utils.db import NotFoundError

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def index_zip_media(zf):
    with zipfile.ZipFile(zf, 'r') as archive:
        zipname = os.path.basename(zf)
        media=[];meta=[];albums=[]
        files = archive.namelist()
        nomedia = ["print-subscriptions", "shared_album_comments"]

        for filepath in files:
            ext = os.path.splitext(filepath)[1]
            if ext == '.json':
                if not any(x in filepath for x in nomedia):
                    meta.append({
                        'path':filepath,
                        'archive':zipname
                    })
            elif ext != '.html':
                media.append({
                    'path':filepath,
                    'ext': str.upper(ext[1:]),
                    'archive':zipname,
                    'hangouts':1 if 'Hangout_' in filepath else 0,
                    'edited':0
                    })
        db['media_files'].upsert_all(media,alter=True,pk="path")
        db['meta_files'].upsert_all(meta,alter=True,pk="path")

def get_media_meta(path):
    if "archives" not in db.view_names():
        db.create_view("archives", """select archive from meta_files group by archive""")
    if "albums" not in db.view_names():
        db.create_view("albums", """select path,archive,title,description from meta_files where type = 'album' order by title asc""")
    for row in db["archives"].rows:
        print(">> Parsing metadata from %s..." % row["archive"])
        with zipfile.ZipFile(path+row["archive"], 'r') as archive:
            for row in db['meta_files'].rows_where("archive = ?", [row["archive"]]):
                with archive.open(row["path"]) as metafile:
                    r = json.loads(metafile.read())
                    try:
                        # Extract Album info
                        if 'metadata' in row["path"]:
                            d = {
                                "type": 'album',
                                "title": r["albumData"]["title"],
                                "description": r["albumData"]["description"]
                            }
                            db['meta_files'].update(row["path"],d, alter=True)

                        # Extract Media info
                        else:
                            d = {
                                "type": 'media',
                                "title": r["title"],
                                "ts_taken": int(r["photoTakenTime"]["timestamp"]),
                                "ts_created": int(r["creationTime"]["timestamp"]),
                                "ts_modified": int(r["modificationTime"]["timestamp"]),
                                "tsf_taken": r["photoTakenTime"]["formatted"],
                                "geo_lat": r["geoDataExif"]["latitude"],
                                "geo_long": r["geoDataExif"]["longitude"],
                                "geo_alt": r["geoDataExif"]["altitude"],
                                "description": r["description"],
                                "imageViews": int(r.get("imageViews",0)),
                                "trashed": r.get("trashed",0)
                            }
                            db['meta_files'].update(row["path"],d, alter=True)

                    except:
                        print("Issue parsing %s" % row["path"])
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
        db.create_view("matches", """select * from media_files where metapath is not null""")

    for r in db['media_files'].rows:
        fullpath, ext = os.path.splitext(r['path'])
        folder = fullpath.rsplit('/',1)[0] + '/'
        filename = fullpath.rsplit('/',1)[1] + ext

        #Skip edited versions
        if '-edited' in filename:
            db['media_files'].update(r['path'],{"edited":1},alter=True)
            continue
        
        #Try the default json path
        metapath = folder + filename +'.json'
        if check_meta(metapath):
            db['media_files'].update(r['path'],{"metapath": metapath}, alter=True)
            continue

        #Handle case: Metafile trims filename at 46 characters
        if len(filename) > 46:
            filename = filename[:46]
            metapath = folder + filename +'.json'
            if check_meta(metapath):
                db['media_files'].update(r['path'],{"metapath": metapath}, alter=True)
                continue
            
        #Handle case: Hangouts with account_id drops extension
        if 'account_id' in filename:
            filename = filename.rsplit(ext,1)[0]
            metapath = folder + filename +'.json'
            if check_meta(metapath):
                db['media_files'].update(r['path'],{"metapath": metapath}, alter=True)
                continue

        #Handle case: When google adds (1), (2) etc to filename
        re_pattern = '\(\d\)\.'
        re_matches = re.findall(re_pattern,filename)
        if len(re_matches) > 0:
            metapath = fullpath.rsplit('(',1)[0] + ext + '.json'
            if check_meta(metapath):
                db['media_files'].update(r['path'],{"metapath": metapath}, alter=True)
                continue

        #Handle other cases where the extension is dropped in metapath
        metapath = fullpath + '.json'
        if check_meta(metapath):
            db['media_files'].update(r['path'],{"metapath": metapath}, alter=True)
            continue

        #Catch-all
        print("No match: %s" % filename)

    unmatched = db['nomatch'].count
    matched = db['matches'].count
    print('--- Media Report ---')
    print("%s media files matched with metadata" % matched)
    print("%s remaining with no match" % unmatched)

def get_album_meta():
    #todo
    pass

def write_exif():
    #todo
    todo = '''
    - make table: export
    - for each row in "matches":
        - open 
        - open the media file
        - update the exif data
        - save the file
    '''
    pass

def fullrun(path):
    zipfiles = glob.glob(path+'*.zip')
    for zf in zipfiles:
        index_zip_media(zf)
    get_media_meta(path)
    match_meta()