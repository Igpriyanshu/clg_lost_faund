from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'college_secret_key_for_session'

# Database Connection Function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Agar aapka koi MySQL password hai toh yahan daalein
        database="college_lost_found_db"
    )

# 1. LOGIN ROUTE
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid Username or Password!")
            
    return render_template('login.html')

# 2. REGISTER ROUTE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, phone) VALUES (%s, %s, %s)", (username, password, phone))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/')
        except mysql.connector.Error as err:
            return render_template('register.html', error="Username already exists or Database error!")
            
    return render_template('register.html')

# 3. DASHBOARD ROUTE (Main Premium Interface)
# 3. DASHBOARD ROUTE (Upgraded Multi-Search Filter)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
        
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM items WHERE status='Lost'")
    total_lost = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM items WHERE status='Found'")
    total_found = cursor.fetchone()['count']
    
    if search_query:
        query = """
            SELECT * FROM items 
            WHERE item_name LIKE %s 
            OR category LIKE %s 
            OR location LIKE %s 
            ORDER BY id DESC
        """
        like_string = f"%{search_query}%"
        cursor.execute(query, (like_string, like_string, like_string))
    else:
        cursor.execute("SELECT * FROM items ORDER BY id DESC")
        
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', username=session['user'], items=items, total_lost=total_lost, total_found=total_found)
# 4. REPORT ITEM ROUTE
@app.route('/report-item', methods=['POST'])
def report_item():
    if 'user' not in session:
        return redirect('/')
    item_name = request.form['item_name']
    category = request.form['category']
    status = request.form['status']
    location = request.form['location']
    description = request.form['description']
    reported_by = session['user']
    
    if item_name and category and status and location:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (item_name, category, status, location, description, reported_by) VALUES (%s, %s, %s, %s, %s, %s)",
            (item_name, category, status, location, description, reported_by)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
    return redirect('/dashboard')

# 5. LOGOUT ROUTE
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)