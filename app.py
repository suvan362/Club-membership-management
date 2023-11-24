from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta



db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "club_mem_db"
     }
connection = mysql.connector.connect(**db_config)
cursor=connection.cursor()
cursor.callproc("check_paid3")
cursor.close()
connection.commit()


app = Flask(__name__)
app.secret_key="passroot"

@app.route('/')
def home():


    return render_template("home.html")
# Define a route to display the form
@app.route('/Create_user')
def create_user():
    
    error=request.args.get("err")
    if error==None:
        return render_template('create_user.html')
    else:
        return render_template('create_user.html',error=error)

# Define a route to handle form submission
@app.route('/Create_user/submit', methods=['POST'])
def submit():

    

    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        address = request.form['address']

        # Insert data into the database
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO Members (first_name, middle_name, last_name, phone_number, email, address) VALUES (%s, %s, %s, %s, %s, %s)",
                           (first_name, middle_name, last_name, phone_number, email, address))
            connection.commit()
            cursor.callproc("sub_link2",[email])
            connection.commit()
            cursor.close()
            return render_template('Thank_you_create_user.html')
        except Exception as e:
            connection.rollback()
            cursor.close()
            flash('An error occurred: {}'.format(str(e)))
            return redirect(url_for('create_user',err=e))
@app.route("/payment")
def payment():
       cursor=connection.cursor()
       cursor.execute("select * from services")
       res=cursor.fetchall()
       service={}
       for i in res:
           service[i[1]]=float(i[3])
       error=request.args.get("err")
       cursor.close()
       if(error==None):
          return render_template('payment.html',service=service)
       else:
           return render_template('payment.html',service=service,error=error)
       
@app.route("/payment/submit",methods=["post"])
def payment_submit():
       cursor=connection.cursor()
       mem_id=request.form["member_id"]
       service_name=request.form["service"]
       booking_date = request.form.get('booking_date')
       booking_time = request.form.get('booking_time')
       payment_mode = request.form.get('payment_mode')
       UPI_Id_Card_Number=request.form.get("UPI_ID_Card_Number")
       
       cursor.execute("select service_duration,service_id from services where service_name=%s",(service_name,))
       data=cursor.fetchall()
       data=data[0]
       service_duration=data[0]
       service_id=data[1]

       cursor.execute("select * from members where member_id=%s",(mem_id,))
       members=cursor.fetchall()
       if members==[]:
            return redirect(url_for("payment",err="Member ID not found, Enter Valid Member ID"))

       res=1
       res=cursor.callproc("is_subscribed3",[int(mem_id),res])

       
       
       
       res=res[1]
       if res==0:
           cursor.close()
           return redirect(url_for("payment",err="not subscribed"))
       
       cursor.execute("select sub_tier_id from subscription where sub_mem_id=%s and sub_tier_id>= (select service_tier_id from services where service_name=%s)",(mem_id,service_name))
       res=cursor.fetchone()
       if res==None:
           cursor.close()
           return redirect(url_for("payment",err="cannot access this service, please upgrade your membership"))

       booking_datetime = f"{booking_date} {booking_time}"
       booking_datetime = datetime.strptime(booking_datetime, "%Y-%m-%d %H:%M")
       sql_query="insert into payment (payment_type,payment_date,UPI_Id_Card_Number,service_request_id,service_request_name,service_request_time,service_duration,member_id) values(%s,now(),%s,%s,%s,%s,%s,%s)"
       cursor.execute(sql_query,(payment_mode,UPI_Id_Card_Number,service_id,service_name,booking_datetime,service_duration,mem_id))
       connection.commit()
       cursor.close()
       return render_template("thank_you_payment.html")
       
@app.route("/view_members",methods=["get"])
def view_memeber_():
    cursor=connection.cursor()
    sql_query="select * from members m inner join subscription s on m.subscription_id=s.subscription_id"
    cursor.execute(sql_query)
    data=cursor.fetchall()
    cursor.close()
    return render_template("viewmembers.html",data=data,search_term="",category="All") 
    



@app.route("/view_members",methods=["post"])
def view_member():
       cursor=connection.cursor()
       search_term=request.form.get("search_term")
       category=request.form.get("category")
       if search_term=="":
            if category=="All":
                 sql_query="select * from members m inner join subscription s on m.subscription_id=s.subscription_id"
                 cursor.execute(sql_query)
                 data=cursor.fetchall()
                 cursor.close()
                 return render_template("viewmembers.html",data=data,search_term=search_term,category=category) 
            elif category=="Gold":
               cat_num="3"
            elif category=="Silver":
               cat_num="2"       
            elif category=="Bronze":
               cat_num="1" 
            sql_query="select * from members m inner join subscription s on m.subscription_id=s.subscription_id where m.member_tier_id=%s"
            cursor.execute(sql_query,(cat_num,))
            data=cursor.fetchall()
            cursor.close()
            return render_template("viewmembers.html",data=data,search_term=search_term,category=category)
       
       search_term_html=search_term
       search_term=search_term+"%"
       if category=="All":
          sql_query="select * from members m inner join subscription s on m.subscription_id=s.subscription_id where (m.first_name like %s)"
          cursor.execute(sql_query,(search_term,))
          data=cursor.fetchall()
          cursor.close()
          return render_template("viewmembers.html",data=data,search_term=search_term_html,category=category)   
       
       elif category=="Gold":
             cat_num="3"
       elif category=="Silver":
             cat_num="2"       
       elif category=="Bronze":
            cat_num="1"

       sql_query="select * from members m inner join subscription s on m.subscription_id=s.subscription_id where (m.first_name like %s) and m.member_tier_id=%s"
       print(sql_query)
       cursor.execute(sql_query,(search_term,cat_num))
       data=cursor.fetchall()
       cursor.close()
       return render_template("viewmembers.html",data=data,search_term=search_term_html,category=category)


@app.route("/Subscription",methods=['get','post'])
def subscription():
    cursor=connection.cursor()
    if request.method=="GET":
         cursor.execute("select sub_mem_id,subscription_member_name,member_tier_name,sub_start_date,sub_next_due_date,sub_pay_status from subscription left outer join membershiptier on sub_tier_id=member_tier_id")
         data=cursor.fetchall()
         return render_template("subscription.html",data=data)
    if request.method=="POST":
         membership_id=request.form.get("membership_id")
         if membership_id=="":
                cursor.execute("select sub_mem_id,subscription_member_name,member_tier_name,sub_start_date,sub_next_due_date,sub_pay_status from subscription left outer join membershiptier on sub_tier_id=member_tier_id")
                data=cursor.fetchall()
                return render_template("subscription.html",data=data)
         cursor.execute("select sub_mem_id,subscription_member_name,member_tier_name,sub_start_date,sub_next_due_date,sub_pay_status from subscription left outer join membershiptier on sub_tier_id=member_tier_id where sub_mem_id=%s",(membership_id,))
         data=cursor.fetchall()
         if data==[]:
             cursor.close()
             return render_template("subscription.html",error="No member found")
         return render_template("subscription.html",data=data)
         
@app.route("/PaySubscription",methods=["get","post"])
def paysubscription():
    cursor=connection.cursor()
    
    if request.method=="GET":
        member_id=request.args.get("member_id")
        cursor.execute("select first_name,middle_name,last_name from members where member_id=%s ",(member_id,))
        data=cursor.fetchall()
        data=data[0]
        data=data[0]+" "+data[1]+" "+data[2]
        cursor.execute("select * from membershiptier")
        member_tier=cursor.fetchall()
        end_date=datetime.now()+relativedelta(years=1)
        end_date=end_date.strftime('%Y-%m-%d %H:%M')
        return render_template("pay_membership.html",member_id=member_id,full_name=data,end_date=end_date,member_tier=member_tier)
    if request.method=="POST":
        member_id=request.form.get("member_id")
        tier=request.form.get("tier_id")
        tier=tier.split()
        end_date=request.form.get("end_date")
        cursor.execute("update subscription set sub_tier_id=%s ,sub_tier_name=%s,sub_next_due_date=%s,sub_pay_status='paid' where sub_mem_id=%s",(tier[0],tier[1],end_date,member_id))
        connection.commit()
        cursor.execute("update members set member_tier_id=%s where member_id=%s",(tier[0],member_id))
        connection.commit()
        return redirect(url_for("pay_subscription_success"))
@app.route("/PaySubscription/Success")
def pay_subscription_success():
        return render_template("Thank_you_pay_subscription.html")

@app.route("/UpgradeSubscription/Success")
def upgrade_subscription_success():
        return render_template("Thank_you_upgrade_subscription.html")

@app.route('/Current_date')
def current_date():
     cursor=connection.cursor()
     cursor.execute("select members.first_name,members.member_id,service_request_name,service_request_time,service_duration from payment,members where payment.member_id=members.member_id and DATE(service_request_time) = CURDATE(); ")
     data=cursor.fetchall()
     return render_template("current_date.html",data=data)

@app.route("/UpgradeSubscription",methods=["get","post"])
def upgrade_subscription():
     cursor=connection.cursor()
     if request.method=="GET":
        member_id=request.args.get("member_id")
        cursor.execute("select first_name,middle_name,last_name from members where member_id=%s ",(member_id,))
        data=cursor.fetchall()
        data=data[0]
        data=data[0]+" "+data[1]+" "+data[2]
        cursor.execute("select * from subscription where sub_mem_id=%s",(member_id,))
        sub=cursor.fetchall()
        sub=sub[0]
        mem_tier_id=sub[3]
        end_date=sub[6]
        sql_query="with upgrade_membership(member_tier_id, member_tier_name, member_tier_details, upgrade_price) as (select member_tier_id,member_tier_name,member_tier_details,member_tier_price-(select member_tier_price from membershiptier where member_tier_id=%s) from membershiptier) select * from upgrade_membership where member_tier_id>%s"
        cursor.execute(sql_query,(mem_tier_id,mem_tier_id))
        member_tier=cursor.fetchall()
        return render_template("upgrade_subscription.html",member_id=member_id,full_name=data,end_date=end_date,member_tier=member_tier)
     if request.method=="POST":
        member_id=request.form.get("member_id")
        tier=request.form.get("tier_id")
        if tier==None:
             return render_template("upgrade_unsuccesful.html")
        tier=tier.split()
        end_date=request.form.get("end_date")
        cursor.execute("update subscription set sub_tier_id=%s ,sub_tier_name=%s,sub_next_due_date=%s,sub_pay_status='paid' where sub_mem_id=%s",(tier[0],tier[1],end_date,member_id))
        connection.commit()
        cursor.execute("update members set member_tier_id=%s where member_id=%s",(tier[0],member_id))
        connection.commit()
        return redirect(url_for("upgrade_subscription_success"))
    
@app.route('/Create_service', methods=['POST', 'GET'])
def create_service():
    if request.method == 'POST':
        service_name = request.form['service_name']
        service_details = request.form['service_details']
        service_price = request.form['service_price']
        service_tier_id = request.form['service_tier_id']
        service_duration=request.form['timeInput']
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Services (service_name, service_details, service_price,service_duration, service_tier_id) VALUES (%s, %s, %s,%s, %s)",
                       (service_name, service_details, service_price, service_duration,service_tier_id))
        connection.commit()
        cursor.close()
        return redirect(url_for("Success_create_service"))
    
    cursor=connection.cursor(dictionary=True)
    cursor.execute("select * from membershiptier")
    data=cursor.fetchall()

    return render_template('create_services.html',data=data)


@app.route('/Create_service/Success')
def Success_create_service():
     return render_template('Success_create_service.html')

@app.route('/view_services', methods=['GET','POST'])
def view_services():
    if request.method=="POST":
         service_id=request.form.get("service_id")
         cursor=connection.cursor(dictionary=True)
         cursor.execute("delete from services where service_id=%s",(service_id,))
         connection.commit()
         cursor.close()
         return render_template("delete_service.html")

    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Services inner join membershiptier on service_tier_id=member_tier_id")
    services = cursor.fetchall()
    cursor.close()
    return render_template('view_services.html', services=services)


@app.route('/cancel_payment',methods=['POST'])
def cancel_payment():
     payment_id=request.form.get("payment_id")
     cursor=connection.cursor(dictionary=True)
     cursor.execute("select service_request_time from payment where payment_id=%s",(payment_id,))
     res=cursor.fetchall()
     print(res)
     if res[0]["service_request_time"]<datetime.now():
        return render_template("cancel_payment.html",header="Sorry can't cancel booking",message="Payments/bookings can only be cancelled alteast 1 hour before booking time ")
     cursor.execute("delete from payment where payment_id=%s",(payment_id,))
     connection.commit()
     return render_template("cancel_payment.html",header="Booking Cancelled",message="Payment ammount will be refunded to you within 48 hours, Thank You! ")


@app.route('/view_payments', methods=['GET', 'POST'])
def display_payments():
    cursor=connection.cursor(dictionary=True)
    if request.method == 'POST':
        # Handle filtering by member_id
        member_id = request.form.get('member_id')
        query = """
            SELECT * FROM payment
            INNER JOIN services ON payment.service_request_id = services.service_id
            WHERE payment.member_id = %s
        """
        cursor.execute(query, (member_id,))
        payments=cursor.fetchall()
        # Calculate the sum of total payments for the member
        total_payment_query = """
            SELECT SUM(services.service_price) as total_payment
            FROM payment
            INNER JOIN services ON payment.service_request_id = services.service_id
            WHERE payment.member_id = %s
        """
        cursor.execute(total_payment_query, (member_id,))
        total_payment = cursor.fetchall()
        

    else:
        # Display all payments
        query = """
            SELECT * FROM payment
            INNER JOIN services ON payment.service_request_id = services.service_id
        """
        cursor.execute(query)
        payments = cursor.fetchall()
        
        total_payment = None  # Set to None if not filtering by member_id
        member_id=None

    return render_template('view_payment.html', payments=payments, total_payment=total_payment,member_id=member_id)

     
     
     


        
        
    
       
           


       
      

if __name__ == '__main__':
    app.run(debug=True)
