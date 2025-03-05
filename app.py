from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from datetime import datetime, timedelta
import os
import json
import logging

app = Flask(__name__)
app.secret_key = 'e3f1a2b4c6d8e0f9a7b5c3d1e9f2a4c6d8b0e1f3a5c7d9e2b4c6d8a0f1e3b5'  # Ganti dengan secret key yang aman

# Setup logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Dummy users
users = {'admin': 'admin'}

# File untuk menyimpan data
DATA_FILE = 'data.json'

# Load data dari file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save data ke file
def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Data saved successfully: {data}")
    except Exception as e:
        logging.error(f"Failed to save data: {e}")

# Format teks yang diinginkan (tanpa password)
def generate_text_content(data):
    return f"""Nama Pemesan: {data['nama']}
IP Address: {data['ip']}:5000
User: admin
Password: admin
Tanggal Masa Berlaku Sampai: {data['tanggal']}

CARA AKSES
Buka Browser CHROME, Masukkan alamat : http://{data['ip']}:5000
klik lanjutkan ke situs
Masukkan User Dan Passwordnya
Simak Link Tutorialnya Di Sini https://bit.ly/loopstream
Pastikan alamat link ip tidak diberitahukan ke orang lain, cukup Anda saja.
Terima kasih, semoga Sukses dan Lancar, AMINN ."""

# Halaman login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# Halaman admin panel
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nama = request.form['nama']
        ip = request.form['ip']
        tanggal = request.form['tanggal']
        password = request.form['password']
        
        new_data = {
            'nama': nama,
            'ip': ip,
            'tanggal': tanggal,
            'password': password,
            'created_at': datetime.now().strftime('%d/%m/%Y')
        }
        
        data_list = load_data()
        data_list.append(new_data)
        save_data(data_list)
        
        filename = f"config_{nama}_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(generate_text_content(new_data))
        
        flash('Data berhasil disimpan!')
        return send_file(filename, as_attachment=True)
    
    return render_template('admin.html')

# Halaman list data
@app.route('/list', methods=['GET', 'POST'])
def list_data():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    data_list = load_data()
    current_date = datetime.now()
    updated_list = []
    
    search_query = request.form.get('search_ip', '').strip() if request.method == 'POST' else ''
    
    for data in data_list[:]:
        try:
            expiry_date = datetime.strptime(data['tanggal'], '%d/%m/%Y')
            status = 'Aktif' if current_date <= expiry_date else 'Non Aktif'
            data['status'] = status
            
            if status == 'Non Aktif':
                days_diff = (current_date - expiry_date).days
                if days_diff > 7:
                    data_list.remove(data)
                    continue
            
            if not search_query or search_query in data['ip']:
                updated_list.append(data)
        except ValueError:
            data['status'] = 'Error: Format tanggal salah'
            if not search_query or search_query in data['ip']:
                updated_list.append(data)
    
    save_data(data_list)
    indexed_list = [(i, data) for i, data in enumerate(updated_list)]
    
    return render_template('list.html', data_list=indexed_list, search_query=search_query)

# Download data
@app.route('/download/<int:index>')
def download_data(index):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    data_list = load_data()
    if index < 0 or index >= len(data_list):
        return "Data tidak ditemukan", 404
    
    data = data_list[index]
    filename = f"config_{data['nama']}_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(generate_text_content(data))
    
    return send_file(filename, as_attachment=True)

# Edit data
@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_data(index):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    data_list = load_data()
    if index < 0 or index >= len(data_list):
        return "Data tidak ditemukan", 404
    
    if request.method == 'POST':
        data_list[index]['nama'] = request.form['nama']
        data_list[index]['ip'] = request.form['ip']
        data_list[index]['tanggal'] = request.form['tanggal']
        data_list[index]['password'] = request.form['password']
        save_data(data_list)
        flash('Data berhasil diperbarui!')
        return redirect(url_for('list_data'))
    
    return render_template('edit.html', data=data_list[index], index=index)

# Hapus data
@app.route('/delete/<int:index>')
def delete_data(index):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    data_list = load_data()
    if index < 0 or index >= len(data_list):
        return "Data tidak ditemukan", 404
    
    data_list.pop(index)
    save_data(data_list)
    flash('Data berhasil dihapus!')
    return redirect(url_for('list_data'))

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
