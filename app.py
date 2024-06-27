from flask import Flask, render_template, request, flash, redirect, session, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from hashlib import md5
from  sqlalchemy.sql.expression import func
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqlamodel import ModelView
from flask_admin import Admin


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['UPLOAD_FOLDER'] = 'static/img/upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
db = SQLAlchemy(app)
ckeditor = CKEditor(app)


class Users(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), unique=True)
    root = db.Column(db.Integer, default=0)
   
    def __repr__(self):
        return 'User %r' % self.id 
    
class Expositions(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100))
    text = db.Column(db.Text)
    image_name = db.Column(db.String(100))

    def __repr__(self):
        return 'Expositions %r' % self.id 
    

class Shows(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100))
    text = db.Column(db.Text)
    image_name = db.Column(db.String(100))
    date_start = db.Column(db.DateTime)
    date_end = db.Column(db.DateTime)

    def __repr__(self):
        return 'Shows %r' % self.id 
    

class Tickets(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100))
    price = db.Column(db.Integer)

    def __repr__(self):
        return 'Tickets %r' % self.id 
    
    
class Orders(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'))
    id_ticket = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Integer, default=0)


    def __repr__(self):
        return 'Orders %r' % self.id 
    
class Payment(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    date_visit = db.Column(db.DateTime)
    name_cart = db.Column(db.String(100))
    number_cart = db.Column(db.String(100))
    date_cart = db.Column(db.String(100))
    cvv_cart = db.Column(db.String(100))
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)

    def __repr__(self):
        return 'Payment %r' % self.id 


class AdminIndex(AdminIndexView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            email = request.form.get('email')
            password = md5(request.form.get('password').encode()).hexdigest()
           
            user = Users.query.filter_by(email=email,password=password).first()
            
            if user:
                session['admin'] = Users.query.filter_by(email=email).first().email
                return self.render('admin/dashboard_index.html')
            else:
                flash("Неправильная почта или пароль!", category="bad")
                return redirect(url_for("admin.index"))
        if 'admin' in session:
            user = Users.query.filter_by(email=session['admin']).first()
            if user.root!=1:
                return self.render('admin/admin_login.html')
            else:
                return self.render('admin/dashboard_index.html')
        else:
            return self.render('admin/admin_login.html')


admin = Admin(app, name='Музей',index_view=AdminIndex(), template_mode='bootstrap4')


class OrdersView(ModelView):
    column_display_pk = True 
    column_hide_backrefs = False
    column_list = ['id','id_user','id_ticket','date']


admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(Expositions, db.session))
admin.add_view(ModelView(Shows, db.session))
admin.add_view(ModelView(Tickets, db.session))
admin.add_view(OrdersView(Orders, db.session))
    
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')   

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    total_user = Users.query.filter_by(email=session['name']).first()
    if request.method == 'POST':
        name = request.form.get('name')
        number = request.form.get('number')
        date_cart = request.form.get('date_cart')
        cvv = request.form.get('cvv')
        date_visit = datetime.strptime(request.form['date_visit'],'%Y-%m-%d')
        flash("ОПЛАЧЕНО!", category="ok")
        
        total_user = Users.query.filter_by(email=session['name']).first()
        orders = Orders.query.filter_by(id_user=total_user.id).all()
        id_list = []
        ticket_list = []
        
        description = ''
        
        for order in orders:
            id_list.append(order.id_ticket)

        for el in id_list:
            ticket_list.append(Tickets.query.filter_by(id=el).first())
            
        for el in ticket_list:
            order = Orders.query.filter_by(id_ticket=el.id, id_user=total_user.id).first()
            if not order.status  == 1:
                description += el.title + "<br>"
            
        for el in orders:
            el.status = 1
            db.session.commit()
            
        pay = Payment(name_cart=name, number_cart=number, date_cart=date_cart, cvv_cart=cvv, date_visit=date_visit, id_user=total_user.id, description=description)
        db.session.add(pay)
        db.session.commit()

    return redirect(url_for('profile'))

    
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not 'name' in session:
        abort(401)
        
    total_user = Users.query.filter_by(email=session['name']).first()
    orders = Orders.query.filter_by(id_user=total_user.id).all()
    payments = Payment.query.filter_by(id_user=total_user.id).all()
    id_list = []
    ticket_list = []
    orders_list = []

    for order in orders:
        id_list.append(order.id_ticket)

    for el in id_list:
        ticket_list.append(Tickets.query.filter_by(id=el).first())
        
    for el in ticket_list:
        order = Orders.query.filter_by(id_ticket=el.id, id_user=total_user.id).first()
        if order.status  == 0:    
            orders_list.append(order)
    print(orders_list)
    return render_template("profile.html",ticket_list=ticket_list,orders=orders,zip=zip,payments=payments,orders_list=orders_list)

@app.route('/rules', methods=['GET', 'POST'])
def rules():
    return render_template("rules.html")


@app.route('/visitors', methods=['GET', 'POST'])
def visitors():
    return render_template("visitors.html")


@app.route('/expositions', methods=['GET', 'POST'])
def expositions():
    expositions = Expositions.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        image = request.files['image']
        filename = secure_filename(image.filename)
        pic_name = str(uuid.uuid4()) + "_" + filename
        image.save("static/img/upload/" + pic_name)
        text = request.form.get('ckeditor')
        exposition = Expositions(title=title,image_name=pic_name,text=text)
        db.session.add(exposition)
        db.session.commit()
        flash("Запись добавлена!", category="ok")
        return redirect(url_for("expositions"))
    return render_template("expositions.html",expositions=expositions)


@app.route('/exposition/<int:id>', methods=['GET', 'POST'])
def exposition(id):
    exposition = Expositions.query.get(id)
    if request.method == 'POST':
        exposition.title = request.form.get('title')
        exposition.text = request.form.get('ckeditor')
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            pic_name = str(uuid.uuid4()) + "_" + filename
            image.save("static/img/upload/" + pic_name)
            exposition.image_name = pic_name
        db.session.commit()
        flash("Запись обновлена!", category="ok")
        return redirect(url_for("exposition", id=exposition.id))
    return render_template("exposition.html",exposition=exposition)


@app.route('/delete-exposition/<int:id>')
def delete_exposition(id):
    obj = Expositions.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Запись удалена!", category="bad")
    return redirect('/expositions')


@app.route('/shows', methods=['GET', 'POST'])
def shows():
    shows = Shows.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        image = request.files['image']
        date_start = datetime.strptime(request.form['date_start'],'%Y-%m-%d')
        date_end = datetime.strptime(request.form['date_end'],'%Y-%m-%d')

        filename = secure_filename(image.filename)
        pic_name = str(uuid.uuid4()) + "_" + filename
        image.save("static/img/upload/" + pic_name)
        text = request.form.get('ckeditor')
        show = Shows(title=title,image_name=pic_name,text=text,date_start=date_start,date_end=date_end)
        db.session.add(show)
        db.session.commit()
        flash("Запись добавлена!", category="ok")
        return redirect(url_for("shows"))
    return render_template("shows.html",shows=shows)


@app.route('/show/<int:id>', methods=['GET', 'POST'])
def show(id):
    show = Shows.query.get(id)
    if request.method == 'POST':
        show.title = request.form.get('title')
        show.text = request.form.get('ckeditor')
        show.date_start = datetime.strptime(request.form['date_start'],'%Y-%m-%d')
        show.date_end = datetime.strptime(request.form['date_end'],'%Y-%m-%d')
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            pic_name = str(uuid.uuid4()) + "_" + filename
            image.save("static/img/upload/" + pic_name)
            show.image_name = pic_name
        db.session.commit()
        flash("Запись обновлена!", category="ok")
        return redirect(url_for("show", id=show.id))
    return render_template("show.html",show=show)


@app.route('/delete-show/<int:id>')
def delete_show(id):
    obj = Shows.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Запись удалена!", category="bad")
    return redirect('/shows')

@app.route('/tickets', methods=['GET', 'POST'])
def tickets():
    tickets = Tickets.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        ticket = Tickets(title=title,price=price)
        db.session.add(ticket)
        db.session.commit()
        flash("Запись добавлена!", category="ok")
        return redirect(url_for("tickets"))
    return render_template("tickets.html",tickets=tickets)


@app.route('/update-ticket/<int:id>', methods=['GET', 'POST'])
def update_ticket(id):
    ticket = Tickets.query.get(id)
    ticket.title = request.form.get('title')
    ticket.price = request.form.get('price')
    db.session.commit()
    flash("Билет обновлен!", category="ok")
    return redirect(url_for("tickets"))
    
    
@app.route('/delete-tickets/<int:id>')
def delete_tickets(id):
    obj = Tickets.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Билет удален!", category="bad")
    return redirect('/tickets')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('name', None)
    if request.method == 'POST':
        email = request.form.get('email')
        password = md5(request.form.get('password').encode()).hexdigest()
        user = Users.query.filter_by(email=email,password=password).first()
        if user:
            session['name'] = Users.query.filter_by(email=email).first().email
            return redirect(url_for("index"))
        else:
            flash("Неправильная почта или пароль!", category="bad")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            user = Users(name=name,email=email,password=md5(password.encode()).hexdigest())
            db.session.add(user)
            db.session.commit()
            flash("Регистрация прошла успешно!", category="ok")
            return redirect(url_for("reg"))
        except:
            flash("Произошла ошибка! Проверьте введенные данные!", category="bad")
            db.session.rollback()
            return redirect(url_for("reg"))
    return render_template("reg.html")


@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect('/')


@app.route('/add-order/<int:id_ticket>/<int:id_user>', methods=['GET', 'POST'])
def add_order(id_ticket,id_user):
    order = Orders(id_ticket=id_ticket,id_user=id_user)
    db.session.add(order)
    db.session.commit()
    flash("Билет заказан!", category="ok")
    return redirect('/tickets')


@app.route('/delete-order/<int:id>')
def delete_order(id):
    obj = Orders.query.filter_by(id=id).first()
    db.session.delete(obj)
    db.session.commit()
    flash("Заказ удален!", category="bad")
    return redirect('/profile')

@app.context_processor
def inject_user():
    def get_user_name():
        if 'name' in session:
            return Users.query.filter_by(email=session['name']).first()
    return dict(active_user=get_user_name())




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidded(e):
    return render_template('403.html'), 403


@app.errorhandler(401)
def forbidded(e):
    return render_template('401.html'), 401


if __name__ == '__main__':
    app.run(debug=True)