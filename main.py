#Import all of the things necessary for the project
import os
import re
from flask import Flask, request, url_for, render_template
from werkzeug import secure_filename
from os import listdir
import sqlite3

#Create the database if it is not already created
if not os.path.exists("database.db"):
    conn = sqlite3.connect('database.db')
    #Create the two tables needed for the project
    #"DROP TABLE" will get rid of a table, "CREATE TABLE" will make one
    conn.execute('CREATE TABLE images (FileName TEXT, name TEXT)')
    conn.execute('CREATE TABLE documents (FileName TEXT, name TEXT)')
    conn.close()

#List the allowed extensions, and tell where the files will be uploaded
UPLOAD_FOLDER = './static'
IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
DOCUMENT_EXTENSIONS = set(['txt', 'pdf', 'docx'])

#Intitialize the flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Check whether a given file can be saved or not, and if it's an image or document
def check_file(filename):
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS:
        return "image"
    elif '.' in filename and filename.rsplit('.', 1)[1].lower() in DOCUMENT_EXTENSIONS:
        return "document"
    else:
        return "none"

#Rename the file so there are no duplicates. This goes through 3 steps to rename the file
#Step 1: If there is no file that is the default filename, then save it as the default
#Step 2: If the default name is taken, save the file with the name the user inputted
#Step 3: If niether of those can be done, put a '()' at the end of the default filename,
#Step 3 (cont.) with a unique number inside
def fileRename(fname, folder, name):
    number = 0
    #Get the main parts of the file name (if fname='file.txt', then main='file' and ext='txt')
    main = fname.rsplit('.', 1)[0]
    ext = fname.rsplit('.', 1)[1]
    #Do the renaming thing explained above
    for x in folder:
        if fname == x:
            fname = secure_filename(name + '.' + ext)
            for x in folder:
                if fname == x:
                    #Start original function
                    for x in folder:
                        if x.startswith(main):
                            #Find the '()' part of the relevant filename
                            regx = re.search(r'\(\d+\).' + ext, x)
                            if regx:
                                #Find the number inside of the '()' part
                                regx = int(str(re.search(r'(\d+)', regx.group()).group()))
                                regx = regx + 1
                                if regx > number:
                                    number = regx
                    fname = main + "(%i)" % number + '.' + ext
                    break
            break
    #Return a unique filname
    return fname

#This adds a file to the database once it has been uploaded
def addToDb(fname, name, database):
    try:
        FileName = fname
        name = name
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO " + database + " (FileName, name) VALUES (?,?)",(FileName, name) )
            con.commit()

    except:
        with sqlite3.connect("database.db") as con:
            con.rollback()


#This makes sure there are no extraneous files in the documents or images folders
def syncFileDb(table):
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        cur.execute("SELECT FileName FROM " + table)
        for x in cur.fetchall():
            if not os.path.exists("./static/" + table + "/" + x[0]):
                cur.execute("DELETE FROM " + table + " WHERE FileName = " + '"%s"' % x[0])

#This tells the program what to do when someone connects to the site's main page
@app.route('/')
def index():
    syncFileDb("images")
    syncFileDb("documents")
    #This tells it where the relevant html file is
    return render_template('index.html')

@app.route('/help')
def help():
    return render_template('help.html')

#This is the python code for the page that shows all uploaded images
@app.route('/images',methods=['GET', 'POST'])
def images():
    order = ""
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from images order by rowid desc")
    if request.method == 'POST':
        order = request.form['order']
        if len(order) < 5:
            cur.execute("select * from images order by rowid " + order)
    rows = cur.fetchall()
    return render_template("images.html",rows = rows, order=order)


#This is the python code for the page that shows all uploaded documents
@app.route('/documents',methods=['GET', 'POST'])
def documents():
    order = ""
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from documents order by rowid desc")
    if request.method == 'POST':
        order = request.form['order']
        if len(order) < 5:
            cur.execute("select * from documents order by rowid " + order)
    rows = cur.fetchall()
    return render_template("documents.html",rows = rows, order=order)

#This is the python code for the page that lets one upload a file to the server
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    error = None
    #This tells where the 'images' and 'documents' folders are located
    imupfol = listdir(app.config['UPLOAD_FOLDER'] + '/images/')
    docupfol = listdir(app.config['UPLOAD_FOLDER'] + '/documents/')
    if request.method == 'POST':
        # The File That is Being Uploaded
        file = request.files['file']
        #The name of the file being uploaded (to be used later)
        name = request.form['name']
        #This makes sure is's a legit file and it has a name
        if file and name !="":
            # This checks to see if the uploaded file was an image
            if check_file(file.filename) == "image":
                filename = fileRename(secure_filename(file.filename), imupfol, name)
                addToDb(filename, name, "images")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], "images", filename))
            # This checks to see if the uploaded file was a document
            elif check_file(file.filename) == "document":
                filename = fileRename(secure_filename(file.filename), docupfol, name)
                addToDb(filename, name, "documents")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], "documents", filename))
            else:
                #This error is thrown if for whatever reason it is neither an image nor a document
                error = "Unacceptable File Type"
        else:
            #This error is thrown when the file isn't good or there is no name given for the file
            error = "Please Fill In All of the Required Info"
    #This is around the 'return' function because the webpage requires a connection to the database
    with sqlite3.connect("database.db") as con:
        return render_template('upload.html', error=error)
        con.close()

#This is the part that tells the server to start, and tells what port and ip to use
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
