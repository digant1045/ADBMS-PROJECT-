from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
import datetime
from logger import logging

# Connection
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/monis"
mongo = PyMongo(app)

# Login Page
@app.route('/',methods=["POST","GET"])
def login():
    return render_template('login_form.html')

# Sign Up
@app.route('/sign_up')
def sign_up():
    return render_template('sign_up.html')

@app.route('/signup_process',methods=['POST','GET'])
def signup_process():
    if request.method=="POST":
        username=request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password!=confirm_password:
            return render_template('password_same.html')
        else:
            mongo.db.login.insert_one({"username":username,'password':password,'email':email})
            logging.info("New User is added to login Collection")
            return render_template('login_form.html')


# Login logic
@app.route('/login_check',methods=['POST','GET'])
def login_check():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        data=mongo.db.login.find({},{'_id':0})
        r='fail'

        for d in data:
            if (d['username']==username and d['password']==password) :
                r='index'
        return redirect(url_for(r))

# If user is invalid
@app.route('/fail')
def fail():
    return render_template('fail.html')
# If user is valid
@app.route('/index')
def index():

    return render_template('index_new.html')
# Order medicine page
@app.route('/medicine_inventory')
def medicine_inventory():
    return render_template('medicine_inventory_new.html')
# Order logic
@app.route('/submit', methods=['POST', 'GET'])
def submit():
    if request.method == 'POST':
        medicine_names = request.form.getlist('medicine_name[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')

        data = []
        amount=[int(i)*int(j) for i,j in zip(quantities,prices)]
        total=sum(amount)

        name_of_medicine=''
        message='result'
        for name, quantity, price in zip(medicine_names, quantities, prices):
            stock_data=list(mongo.db.stock.find({'Name':name}))
            if len(stock_data)>0:
                for i in stock_data:
                    if i['qty']<int(quantity):
                        message='not_availabel'
                        name_of_medicine=name
                        break

                mongo.db.customer_order_collection.insert_one({"Name": name, 'quantity': int(quantity), 'price': float(price),'total':float(total),'date': datetime.datetime.now()})
                data.append({'name': name, 'quantity': int(quantity), 'price': float(price)})
            else:
                message='not_availabel'
                name_of_medicine=name

        if message=="result":
            # This loop is to update stock after billing process
            for name, quantity, price in zip(medicine_names, quantities, prices):
                stock_data = mongo.db.stock.find({'Name': name})
                for i in stock_data:
                    mongo.db.stock.update_one({'Name':name},{'$set':{'qty':i['qty']-int(quantity)}})
            # The Next order
            data_min = list(mongo.db.stock.find({'qty': {'$lt': 5}}))
            for i in data_min:
                temp=list(mongo.db.next_order.find({"Name":i['Name']}))
                if len(temp)==0:
                    mongo.db.next_order.insert_one({'Name':i['Name']})
                    logging.info(f"{i['Name']} Medicine is added to next Order")


            # To delete data which quantity is zero
            for name, quantity, price in zip(medicine_names, quantities, prices):
                stock_data = mongo.db.stock.find({'Name': name})
                for i in stock_data:
                    if i['qty']==0:
                        mongo.db.stock.delete_one({'qty':i['qty']})
            logging.info("Order has been taken and qty is subtracted from Stock Collection")



            return render_template('result_new.html', data=data,total=total)
        else:
            return render_template('not_available.html',data=name_of_medicine)



# Stock page
@app.route('/add_stock')
def add_stock():
    return render_template('add_stock_new.html')

@app.route("/add_medicine", methods=['POST', 'GET'])
def add_medicine():
    if request.method=="POST":
        medicine_names = request.form.getlist('medicine_name[]')
        quantities = request.form.getlist('quantity[]')

        for name,qty in zip(medicine_names,quantities):
            mongo.db.stock.insert_one({"Name":name,'qty':int(qty)})
            logging.info(f"{name} medicine is added to stock")
    return redirect('index')

@app.route('/delete_stock')
def delete_stock():
    return render_template('delete_stock_new.html')

@app.route('/delete_medicine',methods=["POST","GET"])
def delete_medicine():
    if request.method == 'POST':
        medicine_names = request.form.getlist('medicine_name[]')
        quantities = request.form.getlist('quantity[]')

        # This loop is to update stock after billing process
        for name, quantity in zip(medicine_names, quantities):
            stock_data = mongo.db.stock.find({'Name': name})
            for i in stock_data:
                mongo.db.stock.update_one({'Name': name}, {'$set': {'qty': i['qty'] - int(quantity)}})
        # To delete data which quantity is zero
        for name, quantity in zip(medicine_names, quantities):
            stock_data = mongo.db.stock.find({'Name': name})
            for i in stock_data:
                if i['qty'] <= 0 :
                    mongo.db.stock.delete_one({'qty':i['qty']})
        logging.info("Medicine is removed from stock")
        return redirect('index')

@app.route('/display_stock')
def display_stock():
    data=mongo.db.stock.find()
    data_list=[]
    for i in data:
        data_list.append({'Name':i['Name'],'qty':i['qty']})

    logging.info("Stock is displayed")
    return render_template('display_stock_new.html',data=data_list)

if __name__ == '__main__':
    app.run(debug=True,port=5001)


