import os, glob, json, sqlite_utils, zipfile

db_file = 'data.db'
db = sqlite_utils.Database(db_file)

def list_zipped_files(zf):
    with zipfile.ZipFile(zf, 'r') as archive:
        zipname = os.path.basename(zf)
        print("Reading: "+zipname)
        d=[]
        files = archive.namelist()
        for filepath in files:
            ext = os.path.splitext(filepath)[1]
            if ext != '.json':
                d.append({
                    'file':filepath,
                    'ext': str.upper(ext[1:]),
                    'archive':zipname,
                    'app':'Hangouts' if 'Hangout_' in filepath else 'Photos'
                    })
        db['index'].insert_all(d,alter=True)

def enumerate_zips(path):
    zipfiles = glob.glob(path+'*.zip')
    for zf in zipfiles:
        list_zipped_files(zf)