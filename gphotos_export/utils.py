import os, glob, json, sqlite_utils, zipfile
from sqlite_utils.db import NotFoundError

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def index_zip_media(zf):
    with zipfile.ZipFile(zf, 'r') as archive:
        zipname = os.path.basename(zf)
        print(">> Indexing: "+zipname)
        media=[];meta=[]
        files = archive.namelist()
        for filepath in files:
            ext = os.path.splitext(filepath)[1]
            if ext == '.json':
                if 'metadata' not in filepath:
                    meta.append({
                        'file':filepath,
                        'archive':zipname
                    })
            else:
                media.append({
                    'file':filepath,
                    'ext': str.upper(ext[1:]),
                    'archive':zipname,
                    'hangouts':1 if 'Hangout_' in filepath else 0
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

def match_meta():
    num_match=0;num_nomatch=0
    for r in db['media'].rows:
        filepath, ext = os.path.splitext(r['file'])
        filepath = filepath.split('(')[0]
        if filepath[-7:] == '-edited':
            metapath = filepath[:-7] + ext + '.json'
            #TODO: Fix case problem
        else:
            metapath = filepath + ext + '.json'
        try:
            metadata = db["meta"].get(metapath)
            d = {"metapath": metapath}
            db['media'].update(r['file'],d, alter=True)
            num_match +=1
        except NotFoundError:
            print('%s != %s' % (r['file'],metapath))
            num_nomatch +=1
    print("%s medias matched with metadata" % num_match)
    print("%s medias with no match" % num_nomatch)
        
def fullrun(path):
    zipfiles = glob.glob(path+'*.zip')
    for zf in zipfiles:
        index_zip_media(zf)
    pull_metadata(path)
    match_meta()