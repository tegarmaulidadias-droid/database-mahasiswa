
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
from database import get_connection
from html import escape
from http.cookies import SimpleCookie
import secrets
import hmac

BASE_URL = "/database_mahasiswa"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
SESSIONS = {}
SESSION_COOKIE = "admin_session"

def get_session_id(handler):
    cookie = SimpleCookie()
    cookie.load(handler.headers.get("Cookie", ""))

    if SESSION_COOKIE in cookie:
        return cookie[SESSION_COOKIE].value

    return None


def is_logged_in(handler):
    session_id = get_session_id(handler)
    return session_id is not None and session_id in SESSIONS


def halaman_login(error=""):
    error_html = (
        f'<div class="login-error">{escape(error)}</div>'
        if error else ""
    )

    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login Admin</title>
        <link rel="stylesheet" href="{BASE_URL}/static/style.css">
    </head>
    <body class="login-body">

        <div class="login-container">
            <div class="login-card">

                <div class="login-header">
                    <h1>ADMIN PANEL</h1>
                    <p>Sistem Informasi Akademik</p>
                </div>

                {error_html}

                <form method="POST" action="{BASE_URL}/login">

                    <div class="login-group">
                        <label>Username</label>
                        <input
                            type="text"
                            name="username"
                            placeholder="admin"
                            autocomplete="username"
                            required
                        >
                    </div>

                    <div class="login-group">
                        <label>Password</label>
                        <div class="password-wrapper">
                            <input
                                type="password"
                                id="password"
                                name="password"
                                placeholder="admin123"
                                autocomplete="current-password"
                                required
                            >
                            <button
                                type="button"
                                class="toggle-password"
                                onclick="togglePassword()"
                            >Lihat</button>
                        </div>
                    </div>

                    <button type="submit" class="login-button">
                        LOGIN
                    </button>

                </form>

                <div class="login-footer">
                    Sistem Informasi Akademik
                </div>

            </div>
        </div>

        
<script>
    function togglePassword() {{
        const password = document.getElementById("password");
        const button = document.querySelector(".toggle-password");

        if (password.type === "password") {{
            password.type = "text";
            button.textContent = "Sembunyikan";
        }} else {{
            password.type = "password";
            button.textContent = "Lihat";
        }}
    }}
</script>


    </body>
    </html>
    """


def get_total(table):
    allowed_tables = [
        "mahasiswa", "program_studi", "dosen",
        "mata_kuliah", "krs"
    ]

    if table not in allowed_tables:
        return 0

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total


def get_program_studi():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_prodi, nama_prodi
        FROM program_studi
        ORDER BY nama_prodi
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def get_mahasiswa(nim):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mahasiswa WHERE nim = %s", (nim,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def get_prodi(id_prodi):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM program_studi WHERE id_prodi = %s",
        (id_prodi,)
    )
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def get_dosen(nidn):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dosen WHERE nidn = %s", (nidn,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def get_mata_kuliah(id_mk):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM mata_kuliah WHERE id_mk = %s",
        (id_mk,)
    )
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def get_krs(id_krs):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM krs WHERE id_krs = %s", (id_krs,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def sidebar(active=""):
    menus = [
        ("Dashboard", "/", "dashboard"),
        ("Data Mahasiswa", "/mahasiswa", "mahasiswa"),
        ("Program Studi", "/prodi", "prodi"),
        ("Data Dosen", "/dosen", "dosen"),
        ("Mata Kuliah", "/matakuliah", "matakuliah"),
        ("Data KRS", "/krs", "krs"),
        ("Laporan", "/laporan", "laporan")
    ]

    menu_html = ""

    for title, url, key in menus:
        active_class = "active" if active == key else ""
        menu_html += f"""
            <a class="{active_class}" href="{BASE_URL}{url}">
                {title}
            </a>
        """

    return f"""
        <aside class="sidebar">
            <div class="brand">
                <h2>ADMIN PANEL</h2>
                <p>Sistem Informasi Akademik</p>
            </div>
            <nav>{menu_html}</nav>
        </aside>
    """


def layout(title, active, content):
    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{escape(title)}</title>
        <link rel="stylesheet" href="{BASE_URL}/static/style.css">
    </head>
    <body>
        {sidebar(active)}

        <main class="main-content">
            <header class="topbar">
                <div>
                    <h1>{escape(title)}</h1>
                    <p>Sistem Informasi Akademik</p>
                </div>

                <div class="admin-info">
                    <div class="admin-label">Administrator</div>
                    <a href="{BASE_URL}/logout" class="logout-button">Logout</a>
                </div>
            </header>

            {content}
        </main>
    </body>
    </html>
    """


def dashboard():
    data = [
        ("Data Mahasiswa", "mahasiswa", "👨‍🎓"),
        ("Program Studi", "program_studi", "📚"),
        ("Data Dosen", "dosen", "👨‍🏫"),
        ("Mata Kuliah", "mata_kuliah", "📖"),
        ("Data KRS", "krs", "📝")
    ]

    cards = ""

    for title, table, icon in data:
        try:
            total = get_total(table)
        except Exception:
            total = "Error"

        cards += f"""
            <div class="card">
                <div class="card-icon">{icon}</div>
                <h3>{title}</h3>
                <p>{total}</p>
                <span>Total Data</span>
            </div>
        """

    content = f"""
        <section class="welcome">
            <h2>Selamat Datang, Admin!</h2>
            <p>
                Kelola seluruh data akademik melalui menu
                yang tersedia pada halaman ini.
            </p>
        </section>

        <section>
            <h2 class="section-title">Ringkasan Data</h2>
            <div class="card-container">{cards}</div>
        </section>

        <section class="quick-access">
            <h2>Menu Pengelolaan</h2>
            <p>
                Pilih menu di sebelah kiri untuk mengelola
                data akademik.
            </p>
        </section>
    """

    return layout("Dashboard Admin", "dashboard", content)


def halaman_mahasiswa(message=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.nim, m.nama_mahasiswa, m.jenis_kelamin,
               m.tanggal_lahir, m.alamat, p.nama_prodi
        FROM mahasiswa m
        LEFT JOIN program_studi p ON m.id_prodi = p.id_prodi
        ORDER BY m.nim
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    rows = ""
    for mhs in data:
        nim = escape(str(mhs["nim"]), quote=True)
        tanggal = mhs["tanggal_lahir"]
        tanggal = tanggal.strftime("%d-%m-%Y") if tanggal else "-"

        rows += f"""
            <tr>
                <td>{nim}</td>
                <td>{escape(str(mhs["nama_mahasiswa"]))}</td>
                <td>{escape(str(mhs["jenis_kelamin"]))}</td>
                <td>{escape(str(tanggal))}</td>
                <td>{escape(str(mhs["nama_prodi"] or "-"))}</td>
                <td>
                    <div class="action-buttons">
                        <a class="btn-edit" href="{BASE_URL}/mahasiswa/edit?nim={nim}">✏️ Edit</a>
                        <form method="POST" action="{BASE_URL}/mahasiswa/hapus"
                              onsubmit="return confirm('Yakin ingin menghapus data mahasiswa ini?')">
                            <input type="hidden" name="nim" value="{nim}">
                            <button type="submit" class="btn-delete">🗑️ Hapus</button>
                        </form>
                    </div>
                </td>
            </tr>
        """

    if not rows:
        rows = '<tr><td colspan="6" class="empty">Belum ada data mahasiswa.</td></tr>'

    message_html = f'<div class="notice">{escape(message)}</div>' if message else ""
    content = f"""
        <section class="table-section">
            {message_html}
            <div class="table-heading">
                <div>
                    <h2>Daftar Mahasiswa</h2>
                    <p>Jumlah data: <strong>{len(data)}</strong> mahasiswa</p>
                </div>
                <a href="{BASE_URL}/mahasiswa/tambah" class="btn-add">+ Tambah Mahasiswa</a>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>NIM</th><th>Nama Mahasiswa</th>
                            <th>Jenis Kelamin</th><th>Tanggal Lahir</th>
                            <th>Program Studi</th><th>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </section>
    """
    return layout("Data Mahasiswa", "mahasiswa", content)


def form_mahasiswa(mode="tambah", mhs=None, error=""):
    mhs = mhs or {}
    nim = escape(str(mhs.get("nim") or ""), quote=True)
    nama = escape(str(mhs.get("nama_mahasiswa") or ""), quote=True)
    jk = str(mhs.get("jenis_kelamin") or "")
    tanggal = mhs.get("tanggal_lahir")
    tanggal = tanggal.strftime("%Y-%m-%d") if tanggal else ""
    alamat = escape(str(mhs.get("alamat") or ""))
    id_prodi = str(mhs.get("id_prodi") or "")

    options = ""
    for prodi in get_program_studi():
        pid = str(prodi["id_prodi"])
        selected = "selected" if pid == id_prodi else ""
        options += f'<option value="{escape(pid, quote=True)}" {selected}>{escape(str(prodi["nama_prodi"]))}</option>'

    if mode == "edit":
        title = "Edit Data Mahasiswa"
        action = f"{BASE_URL}/mahasiswa/edit"
        nim_field = f'<input type="text" name="nim" value="{nim}" readonly><small>NIM tidak dapat diubah.</small>'
    else:
        title = "Tambah Data Mahasiswa"
        action = f"{BASE_URL}/mahasiswa/tambah"
        nim_field = '<input type="text" name="nim" placeholder="Masukkan NIM" required>'

    jk_options = f"""
        <option value="">Pilih jenis kelamin</option>
        <option value="Laki-laki" {"selected" if jk == "Laki-laki" else ""}>Laki-laki</option>
        <option value="Perempuan" {"selected" if jk == "Perempuan" else ""}>Perempuan</option>
    """
    error_html = f'<div class="notice error">{escape(error)}</div>' if error else ""

    content = f"""
        <section class="form-section">
            <div class="form-page-heading">
                <div><h2>{title}</h2><p>Lengkapi informasi mahasiswa pada formulir berikut.</p></div>
            </div>
            {error_html}
            <form method="POST" action="{action}" class="data-form">
                <div class="form-grid">
                    <div class="form-group"><label>NIM</label>{nim_field}</div>
                    <div class="form-group">
                        <label>Nama Mahasiswa</label>
                        <input type="text" name="nama_mahasiswa" value="{nama}" placeholder="Masukkan nama mahasiswa" required>
                    </div>
                    <div class="form-group">
                        <label>Jenis Kelamin</label>
                        <select name="jenis_kelamin" required>{jk_options}</select>
                    </div>
                    <div class="form-group">
                        <label>Tanggal Lahir</label>
                        <input type="date" name="tanggal_lahir" value="{escape(tanggal, quote=True)}">
                    </div>
                    <div class="form-group full">
                        <label>Alamat</label>
                        <textarea name="alamat" rows="4" placeholder="Masukkan alamat lengkap">{alamat}</textarea>
                    </div>
                    <div class="form-group full">
                        <label>Program Studi</label>
                        <select name="id_prodi" required>
                            <option value="">Pilih program studi</option>{options}
                        </select>
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn-submit">Simpan Data</button>
                        <a href="{BASE_URL}/mahasiswa" class="btn-cancel">Batal</a>
                    </div>
                </div>
            </form>
        </section>
    """
    return layout(title, "mahasiswa", content)


def halaman_prodi(message=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_prodi, nama_prodi, jenjang, akreditasi
        FROM program_studi ORDER BY id_prodi
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    rows = ""
    for prodi in data:
        pid = escape(str(prodi["id_prodi"]), quote=True)
        rows += f"""
            <tr>
                <td>{pid}</td>
                <td>{escape(str(prodi["nama_prodi"]))}</td>
                <td>{escape(str(prodi["jenjang"]))}</td>
                <td>{escape(str(prodi["akreditasi"]))}</td>
                <td>
                    <div class="action-buttons">
                        <a class="btn-edit" href="{BASE_URL}/prodi/edit?id={pid}">✏️ Edit</a>
                        <form method="POST" action="{BASE_URL}/prodi/hapus"
                              onsubmit="return confirm('Yakin ingin menghapus program studi ini?')">
                            <input type="hidden" name="id_prodi" value="{pid}">
                            <button type="submit" class="btn-delete">🗑️ Hapus</button>
                        </form>
                    </div>
                </td>
            </tr>
        """

    if not rows:
        rows = '<tr><td colspan="5" class="empty">Belum ada data program studi.</td></tr>'

    message_html = f'<div class="notice">{escape(message)}</div>' if message else ""
    content = f"""
        <section class="table-section">
            {message_html}
            <div class="table-heading">
                <div><h2>Daftar Program Studi</h2><p>Jumlah data: <strong>{len(data)}</strong> program studi</p></div>
                <a href="{BASE_URL}/prodi/tambah" class="btn-add">+ Tambah Program Studi</a>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>ID Prodi</th><th>Nama Program Studi</th><th>Jenjang</th><th>Akreditasi</th><th>Aksi</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </section>
    """
    return layout("Program Studi", "prodi", content)


def form_prodi(mode="tambah", prodi=None, error=""):
    prodi = prodi or {}
    pid = escape(str(prodi.get("id_prodi") or ""), quote=True)
    nama = escape(str(prodi.get("nama_prodi") or ""), quote=True)
    jenjang = str(prodi.get("jenjang") or "")
    akreditasi = str(prodi.get("akreditasi") or "")

    if mode == "edit":
        title, action = "Edit Program Studi", f"{BASE_URL}/prodi/edit"
        id_field = f'<input type="number" name="id_prodi" value="{pid}" readonly><small>ID Program Studi tidak dapat diubah.</small>'
    else:
        title, action = "Tambah Program Studi", f"{BASE_URL}/prodi/tambah"
        id_field = '<input type="number" name="id_prodi" placeholder="Masukkan ID Program Studi" required>'

    jenjang_options = '<option value="">Pilih jenjang</option>'
    for value in ["D3", "D4", "S1", "S2", "S3"]:
        selected = "selected" if jenjang == value else ""
        jenjang_options += f'<option value="{value}" {selected}>{value}</option>'

    akreditasi_options = '<option value="">Pilih akreditasi</option>'
    for value in ["Unggul", "A", "Baik Sekali", "B", "Baik", "C"]:
        selected = "selected" if akreditasi == value else ""
        akreditasi_options += f'<option value="{escape(value, quote=True)}" {selected}>{escape(value)}</option>'

    error_html = f'<div class="notice error">{escape(error)}</div>' if error else ""
    content = f"""
        <section class="form-section">
            <div class="form-page-heading"><div><h2>{title}</h2><p>Lengkapi informasi program studi berikut.</p></div></div>
            {error_html}
            <form method="POST" action="{action}" class="data-form">
                <div class="form-grid">
                    <div class="form-group"><label>ID Program Studi</label>{id_field}</div>
                    <div class="form-group"><label>Nama Program Studi</label><input type="text" name="nama_prodi" value="{nama}" placeholder="Masukkan nama program studi" required></div>
                    <div class="form-group"><label>Jenjang</label><select name="jenjang" required>{jenjang_options}</select></div>
                    <div class="form-group"><label>Akreditasi</label><select name="akreditasi" required>{akreditasi_options}</select></div>
                    <div class="form-actions">
                        <button type="submit" class="btn-submit">Simpan Data</button>
                        <a href="{BASE_URL}/prodi" class="btn-cancel">Batal</a>
                    </div>
                </div>
            </form>
        </section>
    """
    return layout(title, "prodi", content)


def halaman_dosen(message=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.nidn, d.nama_dosen, d.no_telepon, p.nama_prodi
        FROM dosen d
        LEFT JOIN program_studi p ON d.id_prodi = p.id_prodi
        ORDER BY d.nidn
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    rows = ""
    for dosen in data:
        nidn = escape(str(dosen["nidn"]), quote=True)
        rows += f"""
            <tr>
                <td>{nidn}</td>
                <td>{escape(str(dosen["nama_dosen"]))}</td>
                <td>{escape(str(dosen["no_telepon"] or "-"))}</td>
                <td>{escape(str(dosen["nama_prodi"] or "-"))}</td>
                <td>
                    <div class="action-buttons">
                        <a class="btn-edit" href="{BASE_URL}/dosen/edit?nidn={nidn}">✏️ Edit</a>
                        <form method="POST" action="{BASE_URL}/dosen/hapus"
                              onsubmit="return confirm('Yakin ingin menghapus dosen ini?')">
                            <input type="hidden" name="nidn" value="{nidn}">
                            <button type="submit" class="btn-delete">🗑️ Hapus</button>
                        </form>
                    </div>
                </td>
            </tr>
        """

    if not rows:
        rows = '<tr><td colspan="5" class="empty">Belum ada data dosen.</td></tr>'

    message_html = f'<div class="notice">{escape(message)}</div>' if message else ""
    content = f"""
        <section class="table-section">
            {message_html}
            <div class="table-heading">
                <div><h2>Daftar Dosen</h2><p>Jumlah data: <strong>{len(data)}</strong> dosen</p></div>
                <a href="{BASE_URL}/dosen/tambah" class="btn-add">+ Tambah Dosen</a>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>NIDN</th><th>Nama Dosen</th><th>Nomor Telepon</th><th>Program Studi</th><th>Aksi</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </section>
    """
    return layout("Data Dosen", "dosen", content)


def form_dosen(mode="tambah", dosen=None, error=""):
    dosen = dosen or {}
    nidn = escape(str(dosen.get("nidn") or ""), quote=True)
    nama = escape(str(dosen.get("nama_dosen") or ""), quote=True)
    telepon = escape(str(dosen.get("no_telepon") or ""), quote=True)
    id_prodi = str(dosen.get("id_prodi") or "")

    options = ""
    for prodi in get_program_studi():
        pid = str(prodi["id_prodi"])
        selected = "selected" if pid == id_prodi else ""
        options += f'<option value="{escape(pid, quote=True)}" {selected}>{escape(str(prodi["nama_prodi"]))}</option>'

    if mode == "edit":
        title, action = "Edit Data Dosen", f"{BASE_URL}/dosen/edit"
        nidn_field = f'<input type="text" name="nidn" value="{nidn}" readonly><small>NIDN tidak dapat diubah.</small>'
    else:
        title, action = "Tambah Data Dosen", f"{BASE_URL}/dosen/tambah"
        nidn_field = '<input type="text" name="nidn" placeholder="Masukkan NIDN" required>'

    error_html = f'<div class="notice error">{escape(error)}</div>' if error else ""
    content = f"""
        <section class="form-section">
            <div class="form-page-heading"><div><h2>{title}</h2><p>Lengkapi informasi dosen berikut.</p></div></div>
            {error_html}
            <form method="POST" action="{action}" class="data-form">
                <div class="form-grid">
                    <div class="form-group"><label>NIDN</label>{nidn_field}</div>
                    <div class="form-group"><label>Nama Dosen</label><input type="text" name="nama_dosen" value="{nama}" placeholder="Masukkan nama dosen" required></div>
                    <div class="form-group"><label>Nomor Telepon</label><input type="text" name="no_telepon" value="{telepon}" placeholder="Masukkan nomor telepon"></div>
                    <div class="form-group"><label>Program Studi</label><select name="id_prodi" required><option value="">Pilih program studi</option>{options}</select></div>
                    <div class="form-actions">
                        <button type="submit" class="btn-submit">Simpan Data</button>
                        <a href="{BASE_URL}/dosen" class="btn-cancel">Batal</a>
                    </div>
                </div>
            </form>
        </section>
    """
    return layout(title, "dosen", content)


def halaman_matakuliah(message=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT mk.id_mk, mk.nama_mk, mk.semester, mk.sks, d.nama_dosen
        FROM mata_kuliah mk
        LEFT JOIN dosen d ON mk.nidn = d.nidn
        ORDER BY mk.id_mk
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    rows = ""
    for mk in data:
        id_mk = escape(str(mk["id_mk"]), quote=True)
        rows += f"""
            <tr>
                <td>{id_mk}</td>
                <td>{escape(str(mk["nama_mk"]))}</td>
                <td>{escape(str(mk["semester"]))}</td>
                <td>{escape(str(mk["sks"]))}</td>
                <td>{escape(str(mk["nama_dosen"] or "-"))}</td>
                <td>
                    <div class="action-buttons">
                        <a class="btn-edit" href="{BASE_URL}/matakuliah/edit?id_mk={id_mk}">✏️ Edit</a>
                        <form method="POST" action="{BASE_URL}/matakuliah/hapus"
                              onsubmit="return confirm('Yakin ingin menghapus mata kuliah ini?')">
                            <input type="hidden" name="id_mk" value="{id_mk}">
                            <button type="submit" class="btn-delete">🗑️ Hapus</button>
                        </form>
                    </div>
                </td>
            </tr>
        """

    if not rows:
        rows = '<tr><td colspan="6" class="empty">Belum ada data mata kuliah.</td></tr>'

    message_html = f'<div class="notice">{escape(message)}</div>' if message else ""
    content = f"""
        <section class="table-section">
            {message_html}
            <div class="table-heading">
                <div><h2>Daftar Mata Kuliah</h2><p>Jumlah data: <strong>{len(data)}</strong> mata kuliah</p></div>
                <a href="{BASE_URL}/matakuliah/tambah" class="btn-add">+ Tambah Mata Kuliah</a>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>ID Mata Kuliah</th><th>Nama Mata Kuliah</th><th>Semester</th><th>SKS</th><th>Dosen Pengampu</th><th>Aksi</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </section>
    """
    return layout("Mata Kuliah", "matakuliah", content)


def form_matakuliah(mode="tambah", mk=None, error=""):
    mk = mk or {}
    id_mk = escape(str(mk.get("id_mk") or ""), quote=True)
    nama = escape(str(mk.get("nama_mk") or ""), quote=True)
    semester = str(mk.get("semester") or "")
    sks = str(mk.get("sks") or "")
    nidn = str(mk.get("nidn") or "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nidn, nama_dosen FROM dosen ORDER BY nama_dosen")
    dosen_list = cursor.fetchall()
    cursor.close()
    conn.close()

    options = ""
    for dosen in dosen_list:
        did = str(dosen["nidn"])
        selected = "selected" if did == nidn else ""
        options += f'<option value="{escape(did, quote=True)}" {selected}>{escape(str(dosen["nama_dosen"]))}</option>'

    if not dosen_list:
        options = '<option value="">Belum ada data dosen</option>'

    if mode == "edit":
        title, action = "Edit Mata Kuliah", f"{BASE_URL}/matakuliah/edit"
        id_field = f'<input type="text" name="id_mk" value="{id_mk}" readonly><small>ID mata kuliah tidak dapat diubah.</small>'
    else:
        title, action = "Tambah Mata Kuliah", f"{BASE_URL}/matakuliah/tambah"
        id_field = '<input type="text" name="id_mk" placeholder="Masukkan ID mata kuliah" required>'

    semester_options = '<option value="">Pilih semester</option>'
    for nomor in range(1, 9):
        selected = "selected" if str(nomor) == semester else ""
        semester_options += f'<option value="{nomor}" {selected}>Semester {nomor}</option>'

    sks_options = '<option value="">Pilih jumlah SKS</option>'
    for jumlah in range(1, 7):
        selected = "selected" if str(jumlah) == sks else ""
        sks_options += f'<option value="{jumlah}" {selected}>{jumlah} SKS</option>'

    error_html = f'<div class="notice error">{escape(error)}</div>' if error else ""
    content = f"""
        <section class="form-section">
            <div class="form-page-heading"><div><h2>{title}</h2><p>Lengkapi informasi mata kuliah berikut.</p></div></div>
            {error_html}
            <form method="POST" action="{action}" class="data-form">
                <div class="form-grid">
                    <div class="form-group"><label>ID Mata Kuliah</label>{id_field}</div>
                    <div class="form-group"><label>Nama Mata Kuliah</label><input type="text" name="nama_mk" value="{nama}" placeholder="Masukkan nama mata kuliah" required></div>
                    <div class="form-group"><label>Semester</label><select name="semester" required>{semester_options}</select></div>
                    <div class="form-group"><label>Jumlah SKS</label><select name="sks" required>{sks_options}</select></div>
                    <div class="form-group full"><label>Dosen Pengampu</label><select name="nidn" required><option value="">Pilih dosen pengampu</option>{options}</select></div>
                    <div class="form-actions">
                        <button type="submit" class="btn-submit">Simpan Data</button>
                        <a href="{BASE_URL}/matakuliah" class="btn-cancel">Batal</a>
                    </div>
                </div>
            </form>
        </section>
    """
    return layout(title, "matakuliah", content)


def halaman_krs(message=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT k.id_krs, k.nim, m.nama_mahasiswa, k.id_mk,
               mk.nama_mk, k.semester, k.nilai_angka
        FROM krs k
        JOIN mahasiswa m ON k.nim = m.nim
        JOIN mata_kuliah mk ON k.id_mk = mk.id_mk
        ORDER BY k.id_krs
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    rows = ""
    for item in data:
        id_krs = escape(str(item["id_krs"]), quote=True)
        rows += f"""
            <tr>
                <td>{id_krs}</td>
                <td>{escape(str(item["nim"]))}</td>
                <td>{escape(str(item["nama_mahasiswa"]))}</td>
                <td>{escape(str(item["nama_mk"]))}</td>
                <td>{escape(str(item["semester"]))}</td>
                <td>{escape(str(item["nilai_angka"] if item["nilai_angka"] is not None else "-"))}</td>
                <td>
                    <div class="action-buttons">
                        <a class="btn-edit" href="{BASE_URL}/krs/edit?id_krs={id_krs}">✏️ Edit</a>
                        <form method="POST" action="{BASE_URL}/krs/hapus"
                              onsubmit="return confirm('Yakin ingin menghapus data KRS ini?')">
                            <input type="hidden" name="id_krs" value="{id_krs}">
                            <button class="btn-delete" type="submit">🗑️ Hapus</button>
                        </form>
                    </div>
                </td>
            </tr>
        """

    if not rows:
        rows = '<tr><td colspan="7" class="empty">Belum ada data KRS.</td></tr>'

    message_html = f'<div class="notice">{escape(message)}</div>' if message else ""
    content = f"""
        <section class="table-section">
            {message_html}
            <div class="table-heading">
                <div><h2>Daftar KRS</h2><p>Jumlah data: <strong>{len(data)}</strong> KRS</p></div>
                <a href="{BASE_URL}/krs/tambah" class="btn-add">+ Tambah KRS</a>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>ID KRS</th><th>NIM</th><th>Nama Mahasiswa</th><th>Mata Kuliah</th><th>Semester</th><th>Nilai</th><th>Aksi</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </section>
    """
    return layout("Data KRS", "krs", content)


def form_krs(mode="tambah", data=None, error=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nim, nama_mahasiswa FROM mahasiswa ORDER BY nama_mahasiswa")
    mahasiswa_list = cursor.fetchall()
    cursor.execute("SELECT id_mk, nama_mk FROM mata_kuliah ORDER BY nama_mk")
    matakuliah_list = cursor.fetchall()
    cursor.close()
    conn.close()

    data = data or {}
    nim_options = '<option value="">Pilih Mahasiswa</option>'
    for mhs in mahasiswa_list:
        selected = "selected" if str(data.get("nim", "")) == str(mhs["nim"]) else ""
        nim_options += f'<option value="{escape(str(mhs["nim"]), quote=True)}" {selected}>{escape(str(mhs["nim"]))} - {escape(str(mhs["nama_mahasiswa"]))}</option>'

    mk_options = '<option value="">Pilih Mata Kuliah</option>'
    for mk in matakuliah_list:
        selected = "selected" if str(data.get("id_mk", "")) == str(mk["id_mk"]) else ""
        mk_options += f'<option value="{escape(str(mk["id_mk"]), quote=True)}" {selected}>{escape(str(mk["id_mk"]))} - {escape(str(mk["nama_mk"]))}</option>'

    is_edit = mode == "edit"
    action = f"{BASE_URL}/krs/edit" if is_edit else f"{BASE_URL}/krs/tambah"
    heading = "Edit Data KRS" if is_edit else "Tambah Data KRS"
    button_text = "Simpan Perubahan" if is_edit else "Simpan Data"
    id_value = escape(str(data.get("id_krs", "")), quote=True)
    readonly = "readonly" if is_edit else ""
    semester_value = escape(str(data.get("semester", "")), quote=True)
    nilai_value = escape(str(data.get("nilai_angka") if data.get("nilai_angka") is not None else ""), quote=True)
    error_html = f'<div class="notice error">{escape(error)}</div>' if error else ""

    content = f"""
        <section class="form-section">
            <div class="form-page-heading"><div><h2>{heading}</h2><p>Isi formulir berikut untuk mengelola data KRS.</p></div></div>
            {error_html}
            <form method="POST" action="{action}" class="data-form">
                <div class="form-grid">
                    <div class="form-group"><label>ID KRS</label><input type="text" name="id_krs" value="{id_value}" {readonly} required></div>
                    <div class="form-group"><label>Semester</label><input type="number" name="semester" min="1" max="8" value="{semester_value}" required></div>
                    <div class="form-group full"><label>Mahasiswa</label><select name="nim" required>{nim_options}</select></div>
                    <div class="form-group full"><label>Mata Kuliah</label><select name="id_mk" required>{mk_options}</select></div>
                    <div class="form-group full"><label>Nilai Angka</label><input type="number" name="nilai_angka" step="0.01" value="{nilai_value}"></div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn-submit">{button_text}</button>
                    <a href="{BASE_URL}/krs" class="btn-cancel">Batal</a>
                </div>
            </form>
        </section>
    """
    return layout(heading, "krs", content)


def halaman_laporan():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM mahasiswa")
    total_mahasiswa = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM dosen")
    total_dosen = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM program_studi")
    total_prodi = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM mata_kuliah")
    total_mk = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM krs")
    total_krs = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT
            m.nim,
            m.nama_mahasiswa,
            m.jenis_kelamin,
            m.tanggal_lahir,
            p.nama_prodi
        FROM mahasiswa m
        LEFT JOIN program_studi p
            ON m.id_prodi = p.id_prodi
        ORDER BY m.nim
    """)
    data_mahasiswa = cursor.fetchall()

    cursor.execute("""
        SELECT
            p.nama_prodi,
            COUNT(m.nim) AS jumlah_mahasiswa
        FROM program_studi p
        LEFT JOIN mahasiswa m
            ON p.id_prodi = m.id_prodi
        GROUP BY p.id_prodi, p.nama_prodi
        ORDER BY p.id_prodi
    """)
    data_prodi = cursor.fetchall()

    cursor.close()
    conn.close()

    rows_mahasiswa = ""

    for nomor, mhs in enumerate(data_mahasiswa, start=1):
        tanggal = mhs["tanggal_lahir"]
        tanggal = tanggal.strftime("%d-%m-%Y") if tanggal else "-"

        rows_mahasiswa += f"""
            <tr>
                <td>{nomor}</td>
                <td><strong>{escape(str(mhs["nim"]))}</strong></td>
                <td>{escape(str(mhs["nama_mahasiswa"]))}</td>
                <td>{escape(str(mhs["jenis_kelamin"]))}</td>
                <td>{escape(str(tanggal))}</td>
                <td>{escape(str(mhs["nama_prodi"] or "-"))}</td>
            </tr>
        """

    if not rows_mahasiswa:
        rows_mahasiswa = """
            <tr>
                <td colspan="6" class="empty">
                    Belum ada data mahasiswa.
                </td>
            </tr>
        """

    rows_prodi = ""

    for prodi in data_prodi:
        jumlah = prodi["jumlah_mahasiswa"]
        persentase = (
            (jumlah / total_mahasiswa) * 100
            if total_mahasiswa > 0 else 0
        )

        rows_prodi += f"""
            <div class="report-prodi-item">
                <div class="report-prodi-info">
                    <span>{escape(str(prodi["nama_prodi"]))}</span>
                    <strong>{jumlah} mahasiswa</strong>
                </div>
                <div class="report-progress">
                    <div style="width: {persentase:.1f}%"></div>
                </div>
            </div>
        """

    if not rows_prodi:
        rows_prodi = "<p>Belum ada data program studi.</p>"

    content = f"""
        <section class="report-page">

            <div class="report-header">
                <div>
                    <span class="report-eyebrow">RINGKASAN AKADEMIK</span>
                    <h2>Laporan Data Akademik</h2>
                    <p>
                        Ringkasan informasi dan data akademik yang tersimpan
                        dalam sistem.
                    </p>
                </div>
                <div class="report-header-icon">📊</div>
            </div>

            <div class="report-stat-grid">

                <div class="report-stat-card">
                    <div class="report-stat-top">
                        <span>Total Mahasiswa</span>
                        <div class="report-stat-icon">👨‍🎓</div>
                    </div>
                    <h3>{total_mahasiswa}</h3>
                    <p>Data mahasiswa terdaftar</p>
                </div>

                <div class="report-stat-card">
                    <div class="report-stat-top">
                        <span>Total Dosen</span>
                        <div class="report-stat-icon">👨‍🏫</div>
                    </div>
                    <h3>{total_dosen}</h3>
                    <p>Data dosen terdaftar</p>
                </div>

                <div class="report-stat-card">
                    <div class="report-stat-top">
                        <span>Program Studi</span>
                        <div class="report-stat-icon">🏛️</div>
                    </div>
                    <h3>{total_prodi}</h3>
                    <p>Program studi tersedia</p>
                </div>

                <div class="report-stat-card">
                    <div class="report-stat-top">
                        <span>Mata Kuliah</span>
                        <div class="report-stat-icon">📚</div>
                    </div>
                    <h3>{total_mk}</h3>
                    <p>Mata kuliah tersedia</p>
                </div>

                <div class="report-stat-card">
                    <div class="report-stat-top">
                        <span>Total KRS</span>
                        <div class="report-stat-icon">📋</div>
                    </div>
                    <h3>{total_krs}</h3>
                    <p>Data KRS tersimpan</p>
                </div>

            </div>

            <div class="report-content-grid">

                <div class="report-panel">
                    <div class="report-panel-heading">
                        <div>
                            <h3>Mahasiswa per Program Studi</h3>
                            <p>Distribusi jumlah mahasiswa pada setiap prodi.</p>
                        </div>
                    </div>

                    <div class="report-prodi-list">
                        {rows_prodi}
                    </div>
                </div>

                <div class="report-panel report-summary-panel">
                    <div class="report-panel-heading">
                        <div>
                            <h3>Informasi Akademik</h3>
                            <p>Ringkasan keseluruhan data.</p>
                        </div>
                    </div>

                    <div class="report-summary-list">
                        <div><span>Mahasiswa</span><strong>{total_mahasiswa}</strong></div>
                        <div><span>Dosen</span><strong>{total_dosen}</strong></div>
                        <div><span>Program Studi</span><strong>{total_prodi}</strong></div>
                        <div><span>Mata Kuliah</span><strong>{total_mk}</strong></div>
                        <div><span>KRS</span><strong>{total_krs}</strong></div>
                    </div>
                </div>

            </div>

            <div class="report-panel report-table-panel">
                <div class="report-panel-heading">
                    <div>
                        <h3>Laporan Data Mahasiswa</h3>
                        <p>Daftar seluruh mahasiswa yang tersimpan dalam database.</p>
                    </div>
                    <span class="report-total-badge">
                        {total_mahasiswa} Data
                    </span>
                </div>

                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>No.</th>
                                <th>NIM</th>
                                <th>Nama Mahasiswa</th>
                                <th>Jenis Kelamin</th>
                                <th>Tanggal Lahir</th>
                                <th>Program Studi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_mahasiswa}
                        </tbody>
                    </table>
                </div>
            </div>

        </section>
    """

    return layout("Laporan Data", "laporan", content)


class AppHandler(BaseHTTPRequestHandler):

    def redirect(self, path):
        self.send_response(303)
        self.send_header("Location", path)
        self.end_headers()

    def get_form_data(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_data = self.rfile.read(length).decode("utf-8")
        return parse_qs(raw_data)

    def get_value(self, data, key, default=""):
        return data.get(key, [default])[0].strip()

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def get_session_id(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))

        if SESSION_COOKIE in cookie:
            return cookie[SESSION_COOKIE].value

        return None

    def is_logged_in(self):
        session_id = self.get_session_id()
        return session_id is not None and session_id in SESSIONS

    def set_login_cookie(self, session_id):
        self.send_header(
            "Set-Cookie",
            f"{SESSION_COOKIE}={session_id}; Path=/; HttpOnly; SameSite=Lax"
        )

    def clear_login_cookie(self):
        self.send_header(
            "Set-Cookie",
            f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
        )


    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        
        if path == f"{BASE_URL}/static/style.css":
            try:
                with open("static/style.css", "rb") as file:
                    css = file.read()

                self.send_response(200)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.end_headers()
                self.wfile.write(css)
            except FileNotFoundError:
                self.send_error(404, "File CSS tidak ditemukan")
            return

       
        if path == f"{BASE_URL}/login":
            if self.is_logged_in():
                self.redirect(f"{BASE_URL}/")
                return

            self.send_html(halaman_login())
            return

        
        if path == f"{BASE_URL}/logout":
            session_id = self.get_session_id()

            if session_id in SESSIONS:
                del SESSIONS[session_id]

            self.send_response(303)
            self.clear_login_cookie()
            self.send_header("Location", f"{BASE_URL}/login")
            self.end_headers()
            return

        
        if not self.is_logged_in():
            self.redirect(f"{BASE_URL}/login")
            return

       
        if path == f"{BASE_URL}/" or path == f"{BASE_URL}":
            self.send_html(dashboard())

        
        elif path == f"{BASE_URL}/mahasiswa":
            self.send_html(halaman_mahasiswa())

        elif path == f"{BASE_URL}/mahasiswa/tambah":
            self.send_html(form_mahasiswa())

        elif path == f"{BASE_URL}/mahasiswa/edit":
            nim = params.get("nim", [""])[0]

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM mahasiswa WHERE nim = %s", (nim,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            if data:
                self.send_html(form_mahasiswa("edit", data))
            else:
                self.redirect(f"{BASE_URL}/mahasiswa")

        
        elif path == f"{BASE_URL}/prodi":
            self.send_html(halaman_prodi())

        elif path == f"{BASE_URL}/prodi/tambah":
            self.send_html(form_prodi())

        elif path == f"{BASE_URL}/prodi/edit":
            id_prodi = params.get("id", [""])[0]

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM program_studi WHERE id_prodi = %s",
                (id_prodi,)
            )
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            if data:
                self.send_html(form_prodi("edit", data))
            else:
                self.redirect(f"{BASE_URL}/prodi")

       
        elif path == f"{BASE_URL}/dosen":
            self.send_html(halaman_dosen())

        elif path == f"{BASE_URL}/dosen/tambah":
            self.send_html(form_dosen())

        elif path == f"{BASE_URL}/dosen/edit":
            nidn = params.get("nidn", [""])[0]

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM dosen WHERE nidn = %s", (nidn,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            if data:
                self.send_html(form_dosen("edit", data))
            else:
                self.redirect(f"{BASE_URL}/dosen")

       
        elif path == f"{BASE_URL}/matakuliah":
            self.send_html(halaman_matakuliah())

        elif path == f"{BASE_URL}/matakuliah/tambah":
            self.send_html(form_matakuliah())

        elif path == f"{BASE_URL}/matakuliah/edit":
            id_mk = params.get("id_mk", [""])[0]

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM mata_kuliah WHERE id_mk = %s",
                (id_mk,)
            )
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            if data:
                self.send_html(form_matakuliah("edit", data))
            else:
                self.redirect(f"{BASE_URL}/matakuliah")

       
        elif path == f"{BASE_URL}/krs":
            self.send_html(halaman_krs())

        elif path == f"{BASE_URL}/krs/tambah":
            self.send_html(form_krs())

        elif path == f"{BASE_URL}/krs/edit":
            id_krs = params.get("id_krs", [""])[0]

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM krs WHERE id_krs = %s", (id_krs,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()

            if data:
                self.send_html(form_krs("edit", data))
            else:
                self.redirect(f"{BASE_URL}/krs")

        
        elif path == f"{BASE_URL}/laporan":
            self.send_html(halaman_laporan())

        else:
            self.send_error(404, "Halaman tidak ditemukan")

   

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        data = self.get_form_data()

     
        if path == f"{BASE_URL}/login":
            username = self.get_value(data, "username")
            password = self.get_value(data, "password")

            username_valid = hmac.compare_digest(
                username.encode("utf-8"),
                ADMIN_USERNAME.encode("utf-8")
            )

            password_valid = hmac.compare_digest(
                password.encode("utf-8"),
                ADMIN_PASSWORD.encode("utf-8")
            )

            if username_valid and password_valid:
                session_id = secrets.token_urlsafe(32)
                SESSIONS[session_id] = True

                self.send_response(303)
                self.set_login_cookie(session_id)
                self.send_header("Location", f"{BASE_URL}/")
                self.end_headers()
            else:
                self.send_html(
                    halaman_login("Username atau password salah."),
                    401
                )

            return

        
        if not self.is_logged_in():
            self.redirect(f"{BASE_URL}/login")
            return

      

        if path == f"{BASE_URL}/mahasiswa/tambah":
            nim = self.get_value(data, "nim")
            nama = self.get_value(data, "nama_mahasiswa")
            jk = self.get_value(data, "jenis_kelamin")
            tanggal = self.get_value(data, "tanggal_lahir") or None
            alamat = self.get_value(data, "alamat")
            id_prodi = self.get_value(data, "id_prodi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mahasiswa
                (nim, nama_mahasiswa, jenis_kelamin, tanggal_lahir, alamat, id_prodi)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nim, nama, jk, tanggal, alamat, id_prodi))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/mahasiswa")

        elif path == f"{BASE_URL}/mahasiswa/edit":
            nim = self.get_value(data, "nim")
            nama = self.get_value(data, "nama_mahasiswa")
            jk = self.get_value(data, "jenis_kelamin")
            tanggal = self.get_value(data, "tanggal_lahir") or None
            alamat = self.get_value(data, "alamat")
            id_prodi = self.get_value(data, "id_prodi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mahasiswa
                SET nama_mahasiswa=%s, jenis_kelamin=%s,
                    tanggal_lahir=%s, alamat=%s, id_prodi=%s
                WHERE nim=%s
            """, (nama, jk, tanggal, alamat, id_prodi, nim))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/mahasiswa")

        elif path == f"{BASE_URL}/mahasiswa/hapus":
            nim = self.get_value(data, "nim")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mahasiswa WHERE nim=%s", (nim,))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/mahasiswa")

       

        elif path == f"{BASE_URL}/prodi/tambah":
            id_prodi = self.get_value(data, "id_prodi")
            nama = self.get_value(data, "nama_prodi")
            jenjang = self.get_value(data, "jenjang")
            akreditasi = self.get_value(data, "akreditasi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO program_studi
                (id_prodi, nama_prodi, jenjang, akreditasi)
                VALUES (%s, %s, %s, %s)
            """, (id_prodi, nama, jenjang, akreditasi))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/prodi")

        elif path == f"{BASE_URL}/prodi/edit":
            id_prodi = self.get_value(data, "id_prodi")
            nama = self.get_value(data, "nama_prodi")
            jenjang = self.get_value(data, "jenjang")
            akreditasi = self.get_value(data, "akreditasi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE program_studi
                SET nama_prodi=%s, jenjang=%s, akreditasi=%s
                WHERE id_prodi=%s
            """, (nama, jenjang, akreditasi, id_prodi))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/prodi")

        elif path == f"{BASE_URL}/prodi/hapus":
            id_prodi = self.get_value(data, "id_prodi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM program_studi WHERE id_prodi=%s",
                (id_prodi,)
            )
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/prodi")


        elif path == f"{BASE_URL}/dosen/tambah":
            nidn = self.get_value(data, "nidn")
            nama = self.get_value(data, "nama_dosen")
            telepon = self.get_value(data, "no_telepon")
            id_prodi = self.get_value(data, "id_prodi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dosen (nidn, nama_dosen, no_telepon, id_prodi)
                VALUES (%s, %s, %s, %s)
            """, (nidn, nama, telepon, id_prodi))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/dosen")

        elif path == f"{BASE_URL}/dosen/edit":
            nidn = self.get_value(data, "nidn")
            nama = self.get_value(data, "nama_dosen")
            telepon = self.get_value(data, "no_telepon")
            id_prodi = self.get_value(data, "id_prodi")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dosen
                SET nama_dosen=%s, no_telepon=%s, id_prodi=%s
                WHERE nidn=%s
            """, (nama, telepon, id_prodi, nidn))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/dosen")

        elif path == f"{BASE_URL}/dosen/hapus":
            nidn = self.get_value(data, "nidn")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dosen WHERE nidn=%s", (nidn,))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/dosen")

       

        elif path == f"{BASE_URL}/matakuliah/tambah":
            id_mk = self.get_value(data, "id_mk")
            nama = self.get_value(data, "nama_mk")
            semester = self.get_value(data, "semester")
            sks = self.get_value(data, "sks")
            nidn = self.get_value(data, "nidn")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mata_kuliah (id_mk, nama_mk, semester, sks, nidn)
                VALUES (%s, %s, %s, %s, %s)
            """, (id_mk, nama, semester, sks, nidn))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/matakuliah")

        elif path == f"{BASE_URL}/matakuliah/edit":
            id_mk = self.get_value(data, "id_mk")
            nama = self.get_value(data, "nama_mk")
            semester = self.get_value(data, "semester")
            sks = self.get_value(data, "sks")
            nidn = self.get_value(data, "nidn")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mata_kuliah
                SET nama_mk=%s, semester=%s, sks=%s, nidn=%s
                WHERE id_mk=%s
            """, (nama, semester, sks, nidn, id_mk))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/matakuliah")

        elif path == f"{BASE_URL}/matakuliah/hapus":
            id_mk = self.get_value(data, "id_mk")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mata_kuliah WHERE id_mk=%s", (id_mk,))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/matakuliah")

       

        elif path == f"{BASE_URL}/krs/tambah":
            id_krs = self.get_value(data, "id_krs")
            nim = self.get_value(data, "nim")
            id_mk = self.get_value(data, "id_mk")
            semester = self.get_value(data, "semester")
            nilai = self.get_value(data, "nilai_angka") or None

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO krs (id_krs, nim, id_mk, semester, nilai_angka)
                VALUES (%s, %s, %s, %s, %s)
            """, (id_krs, nim, id_mk, semester, nilai))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/krs")

        elif path == f"{BASE_URL}/krs/edit":
            id_krs = self.get_value(data, "id_krs")
            nim = self.get_value(data, "nim")
            id_mk = self.get_value(data, "id_mk")
            semester = self.get_value(data, "semester")
            nilai = self.get_value(data, "nilai_angka") or None

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE krs
                SET nim=%s, id_mk=%s, semester=%s, nilai_angka=%s
                WHERE id_krs=%s
            """, (nim, id_mk, semester, nilai, id_krs))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/krs")

        elif path == f"{BASE_URL}/krs/hapus":
            id_krs = self.get_value(data, "id_krs")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM krs WHERE id_krs=%s", (id_krs,))
            conn.commit()
            cursor.close()
            conn.close()

            self.redirect(f"{BASE_URL}/krs")

        else:
            self.send_error(404, "Proses tidak ditemukan")




if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), AppHandler)

    print("===================================")
    print(" SISTEM INFORMASI DATA MAHASISWA")
    print("===================================")
    print("Server berjalan di http://localhost:8000/")
    print("Username : admin")
    print("Password : admin123")
    print("Tekan CTRL + C untuk menghentikan server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()
