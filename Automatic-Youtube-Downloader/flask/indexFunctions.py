
@app.route("/")
@app.route("/index.html")
def home():
    if CONN is not None:
        CONN.send(["AYD", "STATUS"])
    aydStatus = readData(5)

    print(aydStatus)
    return render_template('index.html', downloader_status=aydStatus)