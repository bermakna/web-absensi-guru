from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import sqlite3
import qrcode
import os
import sys



def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# =====================================
# FASTAPI APP
# =====================================

app = FastAPI()

# =====================================
# STATIC FILE
# =====================================

STATIC_FOLDER = resource_path("static")

if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_FOLDER),
    name="static"
)
# =====================================
# DATABASE SQLITE
# =====================================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

print(os.path.abspath("database.db"))

cursor = conn.cursor()

# =====================================
# TABLE ADMIN
# =====================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS admin (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT

)

""")

# =====================================
# TABLE GURU
# =====================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS guru (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    nip TEXT UNIQUE NOT NULL,
    mapel TEXT NOT NULL

)

""")

# =====================================
# TABLE ABSENSI
# =====================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS absensi (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_guru TEXT,
    tanggal TEXT,
    jam TEXT,
    status TEXT

)

""")

conn.commit()

# =====================================
# INSERT ADMIN DEFAULT
# =====================================

cursor.execute("SELECT * FROM admin")

cek_admin = cursor.fetchall()

if len(cek_admin) == 0:

    cursor.execute("""

    INSERT INTO admin (username, password)

    VALUES
    ('admin1', 'admin12345'),
    ('admin2', 'admin12345')

    """)

    conn.commit()

# =====================================
# FUNCTION LOAD HTML
# =====================================

def load_html(file_name):

    path = resource_path(file_name)

    with open(path, "r", encoding="utf-8") as file:
        return file.read()

# =====================================
# HALAMAN UTAMA
# =====================================

@app.get("/", response_class=HTMLResponse)
async def home():

    html = load_html("index.html")

    return HTMLResponse(content=html)

# =====================================
# HALAMAN LOGIN
# =====================================

@app.get("/login-page", response_class=HTMLResponse)
async def login_page():

    html = load_html("login.html")

    html = html.replace("{{error}}", "")

    return HTMLResponse(content=html)

# =====================================
# PROSES LOGIN
# =====================================

@app.post("/login")
async def login(

    username: str = Form(...),
    password: str = Form(...)

):

    cursor.execute("""

    SELECT * FROM admin
    WHERE username=? AND password=?

    """, (username, password))

    admin = cursor.fetchone()

    # =================================
    # LOGIN BERHASIL
    # =================================

    if admin:

        return await dashboard()

    # =================================
    # LOGIN GAGAL
    # =================================

    else:

        html = load_html("login.html")

        html = html.replace(
            "{{error}}",
            "Username atau Password salah!"
        )

        return HTMLResponse(content=html)

# =====================================
# DASHBOARD
# =====================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():

    cursor.execute("""
    SELECT COUNT(*) FROM guru
    """)
    total_guru = cursor.fetchone()[0]

    # TOTAL HADIR HARI INI
    today = datetime.now().date().isoformat()

    cursor.execute("""
    SELECT COUNT(*)
    FROM absensi
    WHERE status='Hadir'
    """)

    total_hadir = cursor.fetchone()[0]

    # TOTAL IZIN
    cursor.execute("""
    SELECT COUNT(*)
    FROM absensi
    WHERE status='Izin'
    """)
    total_izin = cursor.fetchone()[0]

    # TOTAL SAKIT
    cursor.execute("""
    SELECT COUNT(*)
    FROM absensi
    WHERE status='Sakit'
    """)
    total_sakit = cursor.fetchone()[0]

    html = load_html("dashboard.html")

    html = html.replace(
        "{{total_guru}}",
        str(total_guru)
    )

    html = html.replace(
        "{{total_hadir}}",
        str(total_hadir)
    )

    html = html.replace(
        "{{total_izin}}",
        str(total_izin)
    )

    html = html.replace(
        "{{total_sakit}}",
        str(total_sakit)
    )

    return HTMLResponse(content=html)

# =====================================
# DATA GURU
# =====================================

@app.get("/data-guru", response_class=HTMLResponse)
async def data_guru():

    cursor.execute("""
    SELECT * FROM guru
    """)

    data_guru = cursor.fetchall()

    rows = ""

    # =================================
    # JIKA BELUM ADA DATA
    # =================================

    if len(data_guru) == 0:

        rows = """

        <tr>

            <td colspan="6" class="text-center">
                Belum ada data guru
            </td>

        </tr>

        """

    # =================================
    # JIKA ADA DATA
    # =================================

    else:

        no = 1

        for guru in data_guru:

            qr_path = f"static/qr/{guru[2]}.png"

            if os.path.exists(qr_path):
                status_qr = """
                <span class="badge-status"
                      style="background:#d4edda;color:#155724;">
                    Sudah Generate
                </span>
                """
            else:
                status_qr = """
                <span class="badge-status"
                      style="background:#f8d7da;color:#721c24;">
                    Belum Generate
                </span>
                """

            rows += f"""
            <tr>

                <td>{no}</td>
                <td>{guru[1]}</td>
                <td>{guru[2]}</td>
                <td>{guru[3]}</td>

                <td>
                   {status_qr}
               </td>

                <td>

                    <a href="/hapus-guru/{guru[0]}"
                       class="btn-delete"
                       onclick="return confirm('Yakin ingin menghapus data guru?')">

                       Hapus

                    </a>

                </td>

            </tr>
            """

            no += 1

    html = load_html("data_guru.html")

    html = html.replace(
        "{{data_guru}}",
        rows
        )

    return HTMLResponse(content=html)

# =====================================
# TAMBAH GURU
# =====================================

@app.post("/tambah-guru")
async def tambah_guru(

    nama: str = Form(...),
    nip: str = Form(...),
    mapel: str = Form(...)

):

    # VALIDASI KOSONG

    if nama == "" or nip == "" or mapel == "":

        return HTMLResponse("""

        <script>

            alert('Data tidak boleh kosong!')

            window.location.href='/data-guru'

        </script>

        """)

    # VALIDASI NIP DUPLIKAT

    cursor.execute("""

    SELECT * FROM guru
    WHERE nip=?

    """, (nip,))

    cek_nip = cursor.fetchone()

    if cek_nip:

        return HTMLResponse("""

        <script>

            alert('NIP sudah digunakan!')

            window.location.href='/data-guru'

        </script>

        """)

    # INSERT DATA GURU

    cursor.execute("""

    INSERT INTO guru (nama, nip, mapel)

    VALUES (?, ?, ?)

    """, (nama, nip, mapel))

    conn.commit()

    return HTMLResponse("""

    <script>

        alert('Data guru berhasil ditambahkan!')

        window.location.href='/data-guru'

    </script>

    """)

# =====================================
# HAPUS GURU
# =====================================

@app.get("/hapus-guru/{id}")
async def hapus_guru(id: int):

    cursor.execute("""

    DELETE FROM guru
    WHERE id=?

    """, (id,))

    conn.commit()

    return HTMLResponse("""

    <script>

        alert('Data guru berhasil dihapus!')

        window.location.href='/data-guru'

    </script>

    """)


# =====================================
# GENERATE QR
# =====================================

@app.get("/generate-qr", response_class=HTMLResponse)
async def generate_qr():

    cursor.execute("SELECT * FROM guru")
    data_guru = cursor.fetchall()

    rows = ""

    if len(data_guru) == 0:

        rows = """
        <tr>
            <td colspan="6" class="text-center">
                Belum ada data guru
            </td>
        </tr>
        """

    else:

        QR_FOLDER = os.path.join(STATIC_FOLDER, "qr")

        if not os.path.exists(QR_FOLDER):
            os.makedirs(QR_FOLDER)

        no = 1

        for guru in data_guru:

            qr_path = os.path.join(
                QR_FOLDER,
                f"{guru[2]}.png"
            )

            if not os.path.exists(qr_path):

                qr = qrcode.make(guru[2])
                qr.save(qr_path)

            qr_html = f'''
            <img src="/static/qr/{guru[2]}.png" width="120">
            '''

            rows += f'''
            <tr>
                <td>{no}</td>
                <td>{guru[1]}</td>
                <td>{guru[2]}</td>
                <td>{guru[3]}</td>

                <td>
                    {qr_html}
                </td>

                <td>
                    <a href="/static/qr/{guru[2]}.png"
                       download
                       class="btn btn-success btn-sm">
                       Download
                    </a>

                    <a href="/izin-guru/{guru[0]}"
                       class="btn btn-warning btn-sm">
                       Izin
                    </a>

                    <a href="/sakit-guru/{guru[0]}"
                       class="btn btn-danger btn-sm">
                       Sakit
                    </a>
                </td>
            </tr>
            '''

            no += 1

    html = load_html("generate_qr.html")

    html = html.replace(
        "{{data_qr}}",
        rows
    )

    return HTMLResponse(content=html)
#======================================
# IZIN GURU
#======================================

@app.get("/izin-guru/{id}")
async def izin_guru(id: int):

    cursor.execute(
        """
        SELECT * FROM guru
        WHERE id=?
        """,
        (id,)
    )

    guru = cursor.fetchone()

    if not guru:

        return HTMLResponse("""
        <script>
            alert('Data guru tidak ditemukan!');
            window.location.href='/generate-qr';
        </script>
        """)

    nama_guru = guru[1]

    tanggal = datetime.now().strftime("%Y-%m-%d")
    jam = datetime.now().strftime("%H:%M:%S")

    # Cek apakah sudah ada absensi hari ini
    cursor.execute(
        """
        SELECT *
        FROM absensi
        WHERE nama_guru=? AND tanggal=?
        """,
        (nama_guru, tanggal)
    )

    cek = cursor.fetchone()

    if cek:

        return HTMLResponse(f"""
        <script>
            alert('{nama_guru} sudah memiliki absensi hari ini!');
            window.location.href='/generate-qr';
        </script>
        """)

    cursor.execute(
        """
        INSERT INTO absensi
        (nama_guru, tanggal, jam, status)
        VALUES (?, ?, ?, ?)
        """,
        (nama_guru, tanggal, jam, "Izin")
    )

    conn.commit()

    return HTMLResponse(f"""
    <script>
        alert('{nama_guru} berhasil dicatat sebagai IZIN');
        window.location.href='/generate-qr';
    </script>
    """)

#======================================
# SAKIT GURU 
#======================================

@app.get("/sakit-guru/{id}")
async def sakit_guru(id: int):

    cursor.execute(
        """
        SELECT * FROM guru
        WHERE id=?
        """,
        (id,)
    )

    guru = cursor.fetchone()

    if not guru:

        return HTMLResponse("""
        <script>
            alert('Data guru tidak ditemukan!');
            window.location.href='/generate-qr';
        </script>
        """)

    nama_guru = guru[1]

    tanggal = datetime.now().strftime("%Y-%m-%d")
    jam = datetime.now().strftime("%H:%M:%S")

    # Cek apakah sudah ada absensi hari ini
    cursor.execute(
        """
        SELECT *
        FROM absensi
        WHERE nama_guru=? AND tanggal=?
        """,
        (nama_guru, tanggal)
    )

    cek = cursor.fetchone()

    if cek:

        return HTMLResponse(f"""
        <script>
            alert('{nama_guru} sudah memiliki absensi hari ini!');
            window.location.href='/generate-qr';
        </script>
        """)

    cursor.execute(
        """
        INSERT INTO absensi
        (nama_guru, tanggal, jam, status)
        VALUES (?, ?, ?, ?)
        """,
        (nama_guru, tanggal, jam, "Sakit")
    )

    conn.commit()

    return HTMLResponse(f"""
    <script>
        alert('{nama_guru} berhasil dicatat sebagai SAKIT');
        window.location.href='/generate-qr';
    </script>
    """)


# =====================================
# HAPUS SEMUA QR
# =====================================

@app.get("/hapus-semua-qr")
async def hapus_semua_qr():

    folder_qr = "static/qr"

    if os.path.exists(folder_qr):

        for file in os.listdir(folder_qr):

            if file.endswith(".png"):

                os.remove(
                    os.path.join(folder_qr, file)
                )

    return HTMLResponse("""

    <script>

        alert('Semua QR berhasil dihapus!');

        window.location.href='/generate-qr';

    </script>

    """)


# =====================================
# SCAN ABSENSI
# =====================================

@app.get("/scan-absensi", response_class=HTMLResponse)
async def scan_absensi():

    html = load_html("scan_absensi.html")

    return HTMLResponse(content=html)


# =====================================
# REKAP ABSENSI
# =====================================

@app.get("/rekap-absensi", response_class=HTMLResponse)
async def rekap_absensi():

    cursor.execute("""
    SELECT *
    FROM absensi
    ORDER BY id DESC
    """)

    data_absensi = cursor.fetchall()

    rows = ""

    if len(data_absensi) == 0:

        rows = """

        <tr>
            <td colspan="6" class="text-center">
                Belum ada data absensi
            </td>
        </tr>

        """

    else:

        no = 1

        for absen in data_absensi:

            rows += f"""

     <tr>

            <td>{no}</td>
            <td>{absen[1]}</td>
            <td>{absen[2]}</td>
            <td>{absen[3]}</td>
            <td>{absen[4]}</td>

            <td>

                <a href="/hapus-absensi/{absen[0]}"
                   class="btn btn-danger btn-sm"
                   onclick="return confirm('Yakin ingin menghapus data absensi ini?')">

                   Hapus

                </a>

           </td>

        </tr>

        """

            no += 1

    html = load_html("rekap_absensi.html")

    html = html.replace(
        "{{data_absensi}}",
        rows
    )

    return HTMLResponse(content=html)

#=========================
# HAPUS ABSENSI
#=========================

@app.get("/hapus-absensi/{id}")
async def hapus_absensi(id: int):

    cursor.execute("""
    DELETE FROM absensi
    WHERE id=?
    """, (id,))

    conn.commit()

    return HTMLResponse("""

    <script>

        alert('Data absensi berhasil dihapus!');

        window.location.href='/rekap-absensi';

    </script>

    """)


# =====================================
# PROSES ABSENSI
# =====================================

@app.post("/proses-absensi")
async def proses_absensi(

    guru_id: str = Form(...)

):

    # CARI GURU BERDASARKAN NIP

    cursor.execute(
        """
        SELECT * FROM guru
        WHERE nip=?
        """,
        (guru_id,)
    )

    guru = cursor.fetchone()

    # JIKA GURU TIDAK DITEMUKAN

    if not guru:

        return HTMLResponse("""

        <script>

        alert('QR Guru tidak ditemukan!');

        window.location.href='/scan-absensi';

        </script>

        """)

    nama_guru = guru[1]

    tanggal = datetime.now().strftime("%Y-%m-%d")

    jam = datetime.now().strftime("%H:%M:%S")

    # CEK ABSEN HARI INI

    cursor.execute(
        """
        SELECT * FROM absensi
        WHERE nama_guru=? AND tanggal=?
        """,
        (nama_guru, tanggal)
    )

    cek_absen = cursor.fetchone()

    if cek_absen:

        return HTMLResponse(f"""

        <script>

        alert('{nama_guru} sudah absen hari ini!');

        window.location.href='/scan-absensi';

        </script>

        """)

    # SIMPAN ABSENSI

    cursor.execute(
        """
        INSERT INTO absensi
        (
            nama_guru,
            tanggal,
            jam,
            status
        )
        VALUES
        (?, ?, ?, ?)
        """,
        (
            nama_guru,
            tanggal,
            jam,
            "Hadir"
        )
    )

    conn.commit()

    return HTMLResponse(f"""

    <script>

    alert('Absensi berhasil untuk {nama_guru}');

    window.location.href='/dashboard';

    </script>

    """)



