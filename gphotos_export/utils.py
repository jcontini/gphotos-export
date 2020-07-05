import os, glob, json, sqlite_utils, zipfile, re
from sqlite_utils.db import NotFoundError

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def index_zip_media(zf):
    with zipfile.ZipFile(zf, 'r') as archive:
        zipname = os.path.basename(zf)
        media=[];meta=[]
        files = archive.namelist()
        ignore = ["metadata", "print-subscriptions", "shared_album_comments"]

        for filepath in files:
            ext = os.path.splitext(filepath)[1]
            if ext == '.json':
                if not any(x in filepath for x in ignore):
                    meta.append({
                        'file':filepath,
                        'archive':zipname
                    })
            elif ext == '.html':
                pass
            else:
                media.append({
                    'file':filepath,
                    'ext': str.upper(ext[1:]),
                    'archive':zipname,
                    'hangouts':1 if 'Hangout_' in filepath else 0,
                    'edited':0
                    })
        db['media'].upsert_all(media,alter=True,pk="file")
        db['meta'].upsert_all(meta,alter=True,pk="file")

def pull_metadata(path):
    if "archives" not in db.view_names():
        db.create_view("archives", """select archive from meta group by archive""")
    for row in db["archives"].rows:
        print(">> Parsing metadata from %s..." % row["archive"])
        with zipfile.ZipFile(path+row["archive"], 'r') as archive:
            for row in db["meta"].rows_where("archive = ?", [row["archive"]]):
                with archive.open(row["file"]) as metafile:
                    r = json.loads(metafile.read())
                    try:
                        d = {
                            "title": r["title"],
                            "ts_taken": int(r["photoTakenTime"]["timestamp"]),
                            "ts_created": int(r["creationTime"]["timestamp"]),
                            "ts_modified": int(r["modificationTime"]["timestamp"]),
                            "tsf_taken": r["photoTakenTime"]["formatted"],
                            "tsf_created": r["creationTime"]["formatted"],
                            "tsf_modified": r["modificationTime"]["formatted"],
                            "geo_lat": r["geoDataExif"]["latitude"],
                            "geo_long": r["geoDataExif"]["longitude"],
                            "geo_alt": r["geoDataExif"]["altitude"],
                            "description": r["description"],
                            "imageViews": int(r.get("imageViews",0)),
                            "trashed": r.get("trashed",0)
                        }
                        db["meta"].update(row["file"],d, alter=True)
                    except:
                        print("Issue parsing %s" % row["file"])
                        pass

def check_meta(metapath):
    try:
        db["meta"].get(metapath)
        return True
    except NotFoundError:
        return False

def match_meta():
    if "nomatch" not in db.view_names():
        db.create_view("nomatch", """select * from media where metapath is null and edited is not 1""")
    if "matches" not in db.view_names():
        db.create_view("matches", """select * from media where metapath is not null""")

    for r in db['media'].rows:
        fullpath, ext = os.path.splitext(r['file'])
        folder = fullpath.rsplit('/',1)[0] + '/'
        filename = fullpath.rsplit('/',1)[1] + ext

        #Skip edited versions
        if '-edited' in filename:
            db['media'].update(r['file'],{"edited":1},alter=True)
            continue
        
        #Try the default json path
        metapath = folder + filename +'.json'
        if check_meta(metapath):
            db['media'].update(r['file'],{"metapath": metapath}, alter=True)
            continue

        #Handle case: Metafile trims filename at 46 characters
        if len(filename) > 46:
            filename = filename[:46]
            metapath = folder + filename +'.json'
            if check_meta(metapath):
                db['media'].update(r['file'],{"metapath": metapath}, alter=True)
                continue
            
        #Handle case: Hangouts with account_id drops extension
        if 'account_id' in filename:
            filename = filename.rsplit(ext,1)[0]
            metapath = folder + filename +'.json'
            if check_meta(metapath):
                db['media'].update(r['file'],{"metapath": metapath}, alter=True)
                continue

        #Handle case: When file ends in (1) etc
        re_pattern = '\(\d\)\.'
        re_matches = re.findall(re_pattern,filename)
        if len(re_matches) > 0:
            metapath = fullpath.rsplit('(',1)[0] + ext + '.json' # If google made the (d)
            if check_meta(metapath):
                db['media'].update(r['file'],{"metapath": metapath}, alter=True)
                continue

        #Handle other cases where the extension is dropped in metapath
        metapath = fullpath + '.json' # If the filename originally had (d)
        if check_meta(metapath):
            db['media'].update(r['file'],{"metapath": metapath}, alter=True)
            continue

        #Catch-all
        print("No match: %s" % filename)

    unmatched = db['nomatch'].count
    matched = db['matches'].count
    print('--- Media Report ---')
    print("%s media files matched with metadata" % matched)
    print("%s remaining with no match" % unmatched)
        
def fullrun(path):
    zipfiles = glob.glob(path+'*.zip')
    for zf in zipfiles:
        index_zip_media(zf)
    pull_metadata(path)
    match_meta()