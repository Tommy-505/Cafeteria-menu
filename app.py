from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cafeterias (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          name TEXT UNIQUE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS menu (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          cafeteria_id INTEGER,
                          item TEXT,
                          available INTEGER DEFAULT 1,
                          dietary TEXT,
                          FOREIGN KEY (cafeteria_id) REFERENCES cafeterias(id))''')
        
        # Predefined cafeteria names
        cafeterias = ["Kulirma", "Garden Cafe", "Woods", "College Cafeteria"]
        for cafeteria in cafeterias:
            cursor.execute("INSERT OR IGNORE INTO cafeterias (name) VALUES (?)", (cafeteria,))
        
        conn.commit()

@app.route('/')
def home():
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM cafeterias")
        cafeterias = [row[0] for row in cursor.fetchall()]
    return render_template('index.html', cafeterias=cafeterias)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    cafeteria_id = request.args.get('cafeteria_id', '')
    
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menu WHERE cafeteria_id=? AND item LIKE ? AND available=1", (cafeteria_id, f"%{query}%"))
        results = cursor.fetchall()
    
    return jsonify(results)

@app.route('/cafeteria/<cafeteria_name>')
def cafeteria_menu(cafeteria_name):
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cafeterias WHERE name=?", (cafeteria_name,))
        cafeteria_id = cursor.fetchone()
        if cafeteria_id:
            cafeteria_id = cafeteria_id[0]
            cursor.execute("SELECT item, available, dietary FROM menu WHERE cafeteria_id=?", (cafeteria_id,))
            items = cursor.fetchall()
            return render_template('cafeteria.html', cafeteria_name=cafeteria_name, items=items)
    return "Cafeteria not found", 404

@app.route('/admin')
def admin_panel():
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM cafeterias")
        cafeterias = cursor.fetchall()
        cafeteria_menus = {}
        for cafeteria_id, name in cafeterias:
            cursor.execute("SELECT * FROM menu WHERE cafeteria_id=?", (cafeteria_id,))
            cafeteria_menus[name] = cursor.fetchall()
    
    return render_template('admin.html', cafeterias=[name for _, name in cafeterias], cafeteria_menus=cafeteria_menus)

@app.route('/add_item', methods=['POST'])
def add_item():
    cafeteria_name = request.form['cafeteria_name']
    item = request.form['item']
    available = 1 if request.form.get('available') == 'on' else 0
    dietary = request.form.get('dietary', '')
    
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cafeterias WHERE name=?", (cafeteria_name,))
        cafeteria_id = cursor.fetchone()
        if cafeteria_id:
            cafeteria_id = cafeteria_id[0]
            cursor.execute("INSERT INTO menu (cafeteria_id, item, available, dietary) VALUES (?, ?, ?, ?)", (cafeteria_id, item, available, dietary))
            conn.commit()
    
    return redirect(url_for('admin_panel'))

@app.route('/toggle_availability/<int:item_id>')
def toggle_availability(item_id):
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE menu SET available = NOT available WHERE id=?", (item_id,))
        conn.commit()
    
    return redirect(url_for('admin_panel'))

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    with sqlite3.connect("cafeteria.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM menu WHERE id=?", (item_id,))
        conn.commit()
    
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
