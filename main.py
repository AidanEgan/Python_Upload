import os
import re
from flask import Flask, request, url_for, render_template
from werkzeug import secure_filename
from os import listdir
import sqlite3

if not os.path.exists("database.db"):
    conn = sqlite3.connect('database.db')

    # "DROP TABLE" will get rid of a table, "CREATE TABLE" will make one
    conn.execute('CREATE TABLE images (FileName TEXT, name TEXT)')
    conn.execute('CREATE TABLE documents (FileName TEXT, name TEXT)')
    conn.close()

UPLOAD_FOLDER = './static'
IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
DOCUMENT_EXTENSIONS = set(['txt', 'pdf'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def check_file(filename):
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS:
        return "image"
    elif '.' in filename and filename.rsplit('.', 1)[1].lower() in DOCUMENT_EXTENSIONS:
        return "document"
    else:
        return "none"

def fileRename(fname, folder, name):
    number = 0
    main = fname.rsplit('.', 1)[0]
    ext = fname.rsplit('.', 1)[1]
    for x in folder:
        if fname == x:
            fname = secure_filename(name + '.' + ext)
            for x in folder:
                if fname == x:
                    #Start original function
                    for x in folder:
                        if x.startswith(main):
                            regx = re.search(r'\(\d+\).' + ext, x)
                            if regx:
                                regx = int(str(re.search(r'(\d+)', regx.group()).group()))
                                regx = regx + 1
                                if regx > number:
                                    number = regx
                    fname = main + "(%i)" % number + '.' + ext
                    break
            break
    return fname

def addToDb(fname, name, database):
    try:
        FileName = fname
        name = name
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO " + database + " (FileName, name) VALUES (?,?)",(FileName, name) )
            con.commit()
            result = "Success!"
            return result

    except:
        with sqlite3.connect("database.db") as con:
            con.rollback()
        result = "error in insert operation"
        return result

    return result

def syncFileDb(table):
    toSearch = []
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        cur.execute("SELECT FileName FROM " + table)
        toSearch = cur.fetchall()
        for x in toSearch:
            if not os.path.exists("./static/" + table + "/" + x[0]):
                cur.execute("DELETE FROM " + table + " WHERE FileName = " + '"%s"' % x[0])

@app.route('/')
def index():
    syncFileDb("images")
    syncFileDb("documents")
    return render_template('index.html')

@app.route('/images')
def images():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute("select * from images order by rowid desc")

    rows = cur.fetchall();
    return render_template("images.html",rows = rows)

@app.route('/documents')
def documents():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute("select * from documents order by rowid desc")

    rows = cur.fetchall();
    return render_template("documents.html",rows = rows)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    error = None
    imupfol = listdir(app.config['UPLOAD_FOLDER'] + '/images/')
    docupfol = listdir(app.config['UPLOAD_FOLDER'] + '/documents/')
    if request.method == 'POST':
        # The File That is Being Uploaded
        file = request.files['file']
        #The name of the file being uploaded (to be used later)
        name = request.form['name']
        if file and name !="":
            # It's a legit file and name
            if check_file(file.filename) == "image":
                # This means that the uploaded file was an image
                filename = fileRename(secure_filename(file.filename), imupfol, name)
                addToDb(filename, name, "images")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], "images", filename))
            elif check_file(file.filename) == "document":
                # This means that the uploaded file was a document
                filename = fileRename(secure_filename(file.filename), docupfol, name)
                addToDb(filename, name, "documents")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], "documents", filename))
            else:
                error = "Unacceptable File Type"
        else:
            error = "Please Fill In All of the Required Info"
    with sqlite3.connect("database.db") as con:
        return render_template('upload.html', error=error)
        con.close()

if __name__ == "__main__":
    app.run(debug=True)
