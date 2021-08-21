from flask import *
import pyrebase
from datetime import *
import pytz
from flask_qrcode import QRcode

app = Flask(__name__, static_url_path='/static')
QRcode(app)
firebaseConfig = {
    'apiKey': "AIzaSyB3-ixZ8hoB_1nJx5NKp1wZOacnp188K8w",
    'authDomain': "flask-pos.firebaseapp.com",
    'databaseURL': "https://flask-pos-default-rtdb.firebaseio.com",
    'projectId': "flask-pos",
    'storageBucket': "flask-pos.appspot.com",
    'messagingSenderId': "67044427430",
    'appId': "1:67044427430:web:52acbe89934ac7822e9667",
    'measurementId': "G-W3T263FLRN"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
tz = pytz.timezone('Asia/Taipei')


def sortby_deptTime(data, cmd):
    x = []
    for d in data:
        data[d]['key'] = d
        data[d]['rowNum'] = int(data[d]['rowNum'])
        data[d]['colNum'] = int(data[d]['colNum'])
        if not cmd(data[d]):
            continue
        if (x == []):
            x.append(data[d])
            continue
        tmp = True
        for i in x:
            iT = datetime(int(i['year']), int(i['month']), int(i['day']),
                          int(i['hour']), int(i['minute']), 0, 0, tzinfo=tz)
            dT = datetime(int(data[d]['year']), int(data[d]['month']), int(data[d]['day']),
                          int(data[d]['hour']), int(data[d]['minute']), 0, 0, tzinfo=tz)
            if (iT >= dT):
                x.insert(x.index(i), data[d])
                tmp = False
                break
        if tmp == True:
            x.append(data[d])
    return x


def later_than_now(x):
    now = datetime.now(tz)
    xT = datetime(int(x['year']), int(x['month']), int(x['day']),
                  int(x['hour']), int(x['minute']), 0, 0, tzinfo=tz)
    return (xT >= now)


@app.route('/', methods=['GET'])
def root():
    data = db.child("Flights").get()
    if data.val() == None:
        return render_template('selflight.html', flights=[])
    data = sortby_deptTime(data.val(), lambda x: later_than_now(x))
    return render_template('selflight.html', flights=data)


@app.route('/filter/<fmethod>', methods=['GET'])
def filterpg(fmethod):
    data = db.child("Flights").get()
    if data is None:
        return render_template('index.html', flights=data)
    if fmethod == 'today':
        data = sortby_deptTime(data.val(), lambda x: (int(x['year']) == datetime.now(tz).year) and (
            int(x['month']) == datetime.now(tz).month) and (int(x['day']) == datetime.now(tz).day))
    elif fmethod == 'departed':
        data = sortby_deptTime(data.val(), lambda x: x['status'] == 'Departed')
    elif fmethod == 'ticketing':
        data = sortby_deptTime(
            data.val(), lambda x: x['status'] == 'Ticketing' and later_than_now(x))
    elif fmethod == 'boarding':
        data = sortby_deptTime(
            data.val(), lambda x: x['status'] == 'Boarding')
    elif fmethod == 'all':
        data = sortby_deptTime(data.val(), lambda x: True)
    return render_template('selflight.html', flights=data)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        return render_template('addflight.html', now=datetime.now(tz))
    elif request.method == 'POST':
        flight = request.form.to_dict()
        flight['datetime'] = datetime(int(flight['year']), int(flight['month']), int(flight['day']),
                                      int(flight['hour']), int(flight['minute']), 0, 0, tzinfo=tz).strftime("%Y/%m/%d %H:%M:%S")
        flight['status'] = 'Ticketing'
        flight['Seats'] = {}
        for i in range(int(flight['colNum'])):
            flight['Seats'][i] = {}
            for j in range(int(flight['rowNum'])):
                flight['Seats'][i][j] = {'status': 'Available'}
        db.child("Flights").push(flight)
        return redirect('/')
    else:
        return "ERROR"


@app.route('/manage/<id>', methods=['GET'])
def manage(id):
    data = db.child("Flights").child(id).get().val()
    data['rowNum'] = int(data['rowNum'])
    data['colNum'] = int(data['colNum'])
    data['key'] = id
    return render_template('manage.html', flight=data)


@app.route('/manage/<id>/delete', methods=['GET'])
def delflight(id):
    db.child("Flights").child(id).remove()
    return redirect('/')


@app.route('/manage/<id>/cstatus', methods=['POST'])
def cstatus(id):
    db.child("Flights").child(id).child(
        'status').set(request.form['status'])
    return redirect('/manage/'+id)


@app.route('/manage/<id>/seat/<col>/<row>', methods=['GET'])
def manageseat(id, col, row):
    col = int(col)
    row = int(row)
    data = db.child("Flights").child(id).get().val()
    data['key'] = id
    if (data['Seats'][col][row]['status']) == 'Available':
        return render_template('book.html', flight=data, col=col, row=row, edit=False)
    elif (data['Seats'][col][row]['status']) == 'Booked':
        return render_template('checkin.html', flight=data, col=col, row=row, checked=False)
    elif (data['Seats'][col][row]['status']) == 'Checked_In':
        return render_template('checkin.html', flight=data, col=col, row=row, checked=True)
    else:
        return "ERROR"


@app.route('/manage/<id>/seat/<col>/<row>/book', methods=['POST'])
def bookseat(id, col, row):
    col = int(col)
    row = int(row)
    try:
        if request.form['paid'] == 'on':
            db.child("Flights").child(id).child('Seats').child(
                col).child(row).child('firstN').set(request.form['firstN'])
            db.child("Flights").child(id).child('Seats').child(
                col).child(row).child('lastN').set(request.form['lastN'])
            db.child("Flights").child(id).child('Seats').child(
                col).child(row).child('nationality').set(request.form['nationality'])
            db.child("Flights").child(id).child('Seats').child(
                col).child(row).child('passportN').set(request.form['passportN'])
            db.child("Flights").child(id).child('Seats').child(
                col).child(row).child('status').set('Booked')
            return redirect('/manage/'+str(id)+'/seat/'+str(col)+"/"+str(row))
    except:
        return "DID NOT PAY"


@app.route('/manage/<id>/seat/<col>/<row>/edit', methods=['GET'])
def editseat(id, col, row):
    col = int(col)
    row = int(row)
    data = db.child("Flights").child(id).get().val()
    data['key'] = id
    return render_template('book.html', flight=data, col=col, row=row, edit=True)


@app.route('/manage/<id>/seat/<col>/<row>/cancel', methods=['GET'])
def cancelseat(id, col, row):
    col = int(col)
    row = int(row)
    db.child("Flights").child(id).child('Seats').child(col).child(row).set({})
    db.child("Flights").child(id).child('Seats').child(
        col).child(row).child('status').set('Available')
    return redirect('/manage/'+id)


@app.route('/manage/<id>/seat/<col>/<row>/check_in', methods=['GET'])
def checkin(id, col, row):
    db.child("Flights").child(id).child('Seats').child(
        col).child(row).child('status').set('Checked_In')
    return redirect('/manage/'+id)


@app.route('/scan')
def scan():
    return send_from_directory('templates', 'scan.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80, ssl_context='adhoc')
