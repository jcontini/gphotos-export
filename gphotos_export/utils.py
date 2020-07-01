import os, glob, json, sqlite_utils, zipfile

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def index_zip_media(zf):
    with zipfile.ZipFile(zf, 'r') as archive:
        zipname = os.path.basename(zf)
        print("Reading: "+zipname)
        media=[];meta=[]
        files = archive.namelist()
        for filepath in files:
            ext = os.path.splitext(filepath)[1]
            if ext == '.json':
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
        db['index'].insert_all(media,alter=True)
        db['meta'].insert_all(meta,alter=True,pk="file")

def pull_metadata(path):
    db.create_view("archives", """select archive from meta group by archive""")
    for row in db["archives"].rows:
        with zipfile.ZipFile(path+row["archive"], 'r') as archive:
            for row in db["meta"].rows_where("archive = ?", [row["archive"]]):
                with archive.open(row["file"]) as metafile:
                    print(row["file"])
                    r = json.loads(metafile.read())
                    try:
                        d = {
                            "title": r["title"],
                            "description": r["description"],
                            "ts_taken": r["photoTakenTime"]["formatted"],
                            "ts_created": r["creationTime"]["formatted"],
                            "ts_modified": r["modificationTime"]["formatted"],
                            "geo_lat": r["geoData"]["latitude"],
                            "geo_long": r["geoData"]["longitude"],
                            "geo_alt": r["geoData"]["altitude"],
                            "trashed": r.get("trashed")
                        }
                        print(json.dumps(d,indent=2))
                        db["meta"].update(row["file"],d, alter=True)
                    except:
                        print("Skipping...")
                        pass

def enumerate_zips(path):
    zipfiles = glob.glob(path+'*.zip')
    for zf in zipfiles:
        index_zip_media(zf)
    pull_metadata(path)