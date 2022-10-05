from flask import Flask, render_template, request, redirect, url_for
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
    
)
output = {}
table = 'employee',


@app.route("/", methods=['GET', 'POST'])
def home():
    select_emp = "SELECT * FROM employee"
    cursor = db_conn.cursor()
    cursor.execute(select_emp)
    count = cursor.rowcount
    data = cursor
    cursor.close()

    if count == 0:
        return render_template('index.html', noget=True,numEmployee=count)
    else:
        return render_template('index.html', employee=data,noget=False,numEmployee=count)
    

@app.route("/addemp/", methods=['GET', 'POST'])
def addEmp():
    return render_template('addEmployee.html')

@app.route("/searchemp/", methods=['GET', 'POST'])
def searchEmp():
    return render_template('searchEmployee.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone_no = request.form['phoneno']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, email, phone_no))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return redirect(url_for('/'),name=emp_name)


@app.route("/searchemp",methods=['POST','GET'])
def SearchEmp():
    emp_id = request.form['emp_id']

    select_emp = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_emp,{'emp_id':int(emp_id)})
        count = cursor.rowcount
       
        for result in cursor:
            print(result)
            
    except Exception as e:
        return str(e)
        
    finally:
        cursor.close()

    if count == 0:
        return render_template('searchEmployee.html', alert=True,searchFail=True)
    else:
        return render_template("searchOutput.html",result=result)
    

@app.route("/delete",methods=['POST','GET'])
def deleteEmp():
    emp_id = request.form['emp_id']
    select_emp = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
    delete_emp = "DELETE FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_emp, {'emp_id': int(emp_id)})
        for result in cursor:
            print(result)
        emp_name = "" + result[1] + " " + result[2]
    
        
        try:
            cursor.execute(delete_emp, {'emp_id': int(emp_id)})
            db_conn.commit()
        
        finally:
            cursor.close()
            return render_template("message.html",name=emp_name,alert=True,delete=True)

    except Exception as e:
        return str(e)

    
@app.route("/edit",methods=['POST','GET'])
def editEmp():
    emp_id = request.form['emp_id']
    select_emp = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    key = "emp-id-" + str(emp_id) + "_image_file"

    url = "https://%s.s3.amazonaws.com/%s" % (custombucket, key)
    try:
        cursor.execute(select_emp, {'emp_id': int(emp_id)})
        for result in cursor:
            print(result)
        db_conn.commit()
        
    except Exception as e:
            db_conn.rollback()
            return str(e)

    finally:
        cursor.close()
    return render_template("editEmployee.html",result=result,url=url)

@app.route("/editemp",methods=['POST','GET'])
def EditEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone_no = request.form['phoneno']
    emp_image_file = request.files['emp_image_file']

    update_sql = "UPDATE employee set first_name =  %s , last_name = %s , email =  %s, phone_no =  %s , WHERE emp_id =  %s"
    cursor = db_conn.cursor()

    try:

        cursor.execute(update_sql, ( first_name, last_name, email, phone_no,emp_id))
        db_conn.commit()
        
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')
        if emp_image_file.filename != "":
            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)

            except Exception as e:
                return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('index.html',alert=True,edit=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
