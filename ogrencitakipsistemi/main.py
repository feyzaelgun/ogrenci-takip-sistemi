import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from reportlab.pdfgen import canvas

# =========================
# GENEL AYARLAR
# =========================
DB_NAME = "ogrenci_ders_sistemi.db"

FONT_FAMILY = "Nunito"  # Sisteme yüklüyse direkt çalışır, değilse default fonta düşer

APP_BG = "#f3f4ff"       # genel arka plan
SIDEBAR_BG = "#e0ecff"   # sol menü
TOPBAR_BG = "#e5edff"    # üst bar
CARD_BG = "#ffffff"      # içerik kartları
PRIMARY = "#2563eb"      # buton rengi
PRIMARY_DARK = "#1d4ed8"
TEXT_MAIN = "#111827"
TEXT_MUTED = "#6b7280"

# CTk global
ctk.set_appearance_mode("light")       # başlangıç: light
ctk.set_default_color_theme("blue")    # mavi tonlar


def f(size, weight="normal"):
    """Kısa font helper (Nunito)."""
    return (FONT_FAMILY, size, weight)


# =========================
# VERİTABANI OLUŞTURMA
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            full_name TEXT,
            weak_subject TEXT,
            absence INTEGER,
            avg_grade REAL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 🔥 YENİ
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            plan_text TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_name TEXT NOT NULL,
            teacher_name TEXT,
            grade REAL DEFAULT 0,
            absence INTEGER DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            teacher_id INTEGER,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'Beklemede',
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()



# =========================
# OTOMATİK ÇALIŞMA PLANI
# =========================
def generate_study_plan(weak, avg, absn):
    avg = avg or 0
    absn = absn or 0

    if avg < 2:
        base = "Başarı düşük. Haftada 6 gün, günde 3 saat yoğun çalışma önerilir."
    elif avg < 2.5:
        base = "Başarı orta. Haftada 5 gün, günde 2 saat düzenli çalışma önerilir."
    elif avg < 3:
        base = "Başarı iyi. Haftada 4 gün, günde 1.5 saat çalışma yeterlidir."
    else:
        base = "Başarı çok iyi. Haftada 3 gün tekrar programı uygundur."

    if weak:
        weak_text = f"\nZayıf ders: {weak}. Bu derse her gün en az 30 dk ek çalışma ayrılmalıdır."
    else:
        weak_text = "\nBelirtilmiş zayıf ders yok. Tüm derslerde dengeli tekrar önerilir."

    if absn >= 30:
        abs_text = "\nDevamsızlık çok yüksek! Kaçırılan konular için ekstra telafi yapılmalıdır."
    elif absn >= 10:
        abs_text = "\nDevamsızlık orta düzeyde. Eksik konular tespit edilip tamamlanmalıdır."
    else:
        abs_text = "\nDevamsızlık düşük. Mevcut durum başarıyı olumsuz etkilemiyor."

    return base + weak_text + abs_text


# =========================
# ANA UYGULAMA
# =========================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Öğrenci Ders Takip Sistemi")

        window_width = 950
        window_height = 580

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 🔥 TEK geometry çağrısı
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(False, False)
        self.configure(bg=APP_BG)

        self.current_user = None
        self.current_frame = None

        # ttk stil
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            font=f(11),
            rowheight=26,
            background="#eef2ff",
            fieldbackground="#eef2ff",
            foreground="#111827"
        )
        style.configure(
            "Treeview.Heading",
            font=f(11, "bold"),
            background="#e0e7ff",
            foreground="#111827"
        )
        style.map("Treeview",
                  background=[("selected", "#c7d2fe")])

        init_db()
        self.switch_frame(LoginPage)


    def switch_frame(self, frame_class, *args):
        new_frame = frame_class(self, *args)
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)





# =========================
# GİRİŞ SAYFASI
# =========================
class LoginPage(ctk.CTkFrame):
    def __init__(self, app: MainApp):
        super().__init__(app, fg_color="#F5F7FF")
        self.app = app

        ctk.CTkLabel(
            self,
            text="Öğrenci Ders Takip Sistemi",
            font=f(32, "bold"),
            text_color=TEXT_MAIN
        ).pack(pady=(40, 5))

        ctk.CTkLabel(
            self,
            text="Lütfen giriş yapın veya yeni hesap oluşturun",
            font=f(14),
            text_color=TEXT_MUTED
        ).pack()

        card = ctk.CTkFrame(self, width=480, height=360,
                            fg_color=CARD_BG, corner_radius=30)
        card.pack(pady=30)
        card.pack_propagate(False)

        form = ctk.CTkFrame(card, fg_color=CARD_BG)
        form.pack(pady=20)

        ctk.CTkLabel(
            form,
            text="Kullanıcı Adı",
            font=f(12, "bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w")

        self.username = ctk.CTkEntry(
            form,
            width=330,
            height=45,
            placeholder_text="Kullanıcı adınız",
            corner_radius=12,
            font=f(12)
        )
        self.username.pack(pady=(0, 20))

        ctk.CTkLabel(
            form,
            text="Şifre",
            font=f(12, "bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w")

        self.password = ctk.CTkEntry(
            form,
            width=330,
            height=45,
            show="*",
            placeholder_text="Şifre",
            corner_radius=12,
            font=f(12)
        )
        self.password.pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(card, fg_color=CARD_BG)
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Giriş Yap",
            width=150,
            height=45,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            font=f(13, "bold"),
            corner_radius=14,
            command=self.login
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Kayıt Ol",
            width=150,
            height=45,
            fg_color="#E5E7EB",
            text_color="#000",
            hover_color="#d4d4d8",
            font=f(13, "bold"),
            corner_radius=14,
            command=lambda: self.app.switch_frame(RegisterPage)
        ).pack(side="left", padx=10)

    def login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            messagebox.showerror("Hata", "Kullanıcı adı ve şifre boş olamaz.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, role FROM users WHERE username=? AND password=?", (u, p))
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Hata", "Böyle kullanıcı yok 😢")
            return

        uid, role = row
        self.app.current_user = {"id": uid, "username": u, "role": role}

        if role == "teacher":
            self.app.switch_frame(TeacherPage)
        else:
            # Öğrenci profilini kontrol et
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id FROM students WHERE user_id=?", (uid,))
            s_row = cur.fetchone()
            conn.close()

            if not s_row:
                messagebox.showerror(
                    "Hata",
                    "Böyle kullanıcı yok 😢"
                )
                return  # ❗ StudentPage'e geçişi durdur

            self.app.switch_frame(StudentPage)


# =========================
# KAYIT SAYFASI
# =========================
class RegisterPage(ctk.CTkFrame):
    def __init__(self, app: MainApp):
        super().__init__(app, fg_color=APP_BG)
        self.app = app

        ctk.CTkLabel(
            self,
            text="Yeni Hesap Oluştur",
            font=f(32, "bold"),
            text_color="#222"
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            self,
            text="",
            font=f(16),
            text_color="#555"
        ).pack(pady=(0, 20))

        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=30)
        card.pack(pady=10, padx=60, fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(card, fg_color=CARD_BG, corner_radius=30)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="Rol", font=f(12, "bold")).pack(anchor="w", pady=(5, 3))
        self.role_var = ctk.StringVar(value="Öğrenci")

        self.role_box = ctk.CTkOptionMenu(
            scroll,
            values=["Öğrenci", "Öğretmen"],
            variable=self.role_var,
            width=300,
            height=40,
            corner_radius=10,
            fg_color="#4A90E2",
            button_color="#3A78C4",
            font=f(12, "bold")
        )
        self.role_box.pack(anchor="w")

        ctk.CTkLabel(scroll, text="Kullanıcı Adı", font=f(12, "bold")).pack(anchor="w", pady=(20, 3))
        self.username_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="Kullanıcı adı",
            width=500,
            height=40,
            corner_radius=12,
            font=f(12)
        )
        self.username_entry.pack(anchor="w")

        ctk.CTkLabel(scroll, text="Şifre", font=f(12, "bold")).pack(anchor="w", pady=(20, 3))
        self.password_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="Şifre",
            show="*",
            width=500,
            height=40,
            corner_radius=12,
            font=f(12)
        )
        self.password_entry.pack(anchor="w")

        btn_area = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_area.pack(pady=20)

        ctk.CTkButton(
            btn_area,
            text="Kaydı Tamamla",
            fg_color="#4A6CF7",
            hover_color="#3454D1",
            width=200,
            height=46,
            corner_radius=14,
            font=f(13, "bold"),
            command=self.register_user
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_area,
            text="Geri Dön",
            fg_color="#E5E7EB",
            text_color="#000",
            hover_color="#d5d7db",
            width=200,
            height=46,
            corner_radius=14,
            font=f(13, "bold"),
            command=lambda: self.app.switch_frame(LoginPage)
        ).pack(side="left", padx=10)

    def update_form(self, choice):
        # Şu an ekstra alan yok, gerekirse genişletirsin
        pass

    def register_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role_text = self.role_var.get()

        if not username or not password:
            messagebox.showerror("Hata", "Kullanıcı adı ve şifre boş olamaz.")
            return

        role = "teacher" if role_text == "Öğretmen" else "student"

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            user_id = cur.lastrowid
        except sqlite3.IntegrityError:
            # 🧹 Temizlik: Students tablosunda kaydı olmayan student rolündeki userları sil
            try:
                cur.execute("""
                    DELETE FROM users
                    WHERE role='student'
                    AND id NOT IN (SELECT user_id FROM students)
                """)
                conn.commit()

                # 🌀 Temizlik sonrası tekrar kayıt etmeyi dene!
                cur.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, password, role)
                )
                user_id = cur.lastrowid

            except sqlite3.IntegrityError:
                conn.close()
                messagebox.showerror("Hata", "Bu kullanıcı adı zaten kayıtlı.")
                return


        if role == "student":
            cur.execute("""
                INSERT INTO students (user_id, full_name, weak_subject, absence, avg_grade)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, "", "", 0, 0.0))

            student_id = cur.lastrowid

            cur.execute("""
                INSERT INTO study_plans (student_id, plan_text)
                VALUES (?, ?)
            """, (student_id, ""))
        if role == "teacher":
            cur.execute(
                "INSERT INTO teachers (user_id) VALUES (?)",
                (user_id,)
            )

        conn.commit()
        conn.close()

        messagebox.showinfo("Başarılı", "Kayıt tamamlandı. Artık giriş yapabilirsiniz.")
        self.app.switch_frame(LoginPage)


# =========================
# ÖĞRETMEN PANELİ
# =========================
class TeacherPage(ctk.CTkFrame):
    def __init__(self, app: MainApp):
        super().__init__(app, fg_color="#F5F7FF")
        self.app = app
        self.current_student_id = None
        self.students = []
        self.student_row_map = {}

        # TOP BAR
        top_bar = ctk.CTkFrame(self, fg_color="white", height=60)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        ctk.CTkLabel(
            top_bar,
            text=f"Öğretmen Paneli - {self.app.current_user['username']}",
            font=f(20, "bold"),
            text_color=TEXT_MAIN
        ).pack(side="left", padx=20)



        ctk.CTkButton(
            top_bar,
            text="Çıkış Yap",
            width=100,
            height=36,
            corner_radius=10,
            fg_color="#E5E7EB",
            text_color="#111",
            hover_color="#d4d4d8",
            font=f(12, "bold"),
            command=lambda: self.app.switch_frame(LoginPage)
        ).pack(side="right", padx=10)

        # MAIN LAYOUT
        self.main_frame = ctk.CTkFrame(self, fg_color="#F5F7FF")
        self.main_frame.pack(fill="both", expand=True)

        # SIDEBAR
        sidebar = ctk.CTkFrame(self.main_frame, fg_color=SIDEBAR_BG, width=200)
        sidebar.pack(side="left", fill="y", padx=(0, 10), pady=15)
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="MENÜ",
            font=f(14, "bold"),
            text_color=TEXT_MAIN
        ).pack(pady=(20, 10))

        self._add_menu_button(sidebar, "📚 Öğrenciler", self.show_students_view)
        self._add_menu_button(sidebar, "🕒 Randevularım", self.show_appointments_view)
        self._add_menu_button(sidebar, "👩‍🏫 Öğretmenler", self.show_teachers_view)
        self._add_menu_button(sidebar, "📊 Raporlar", self.show_reports_view)

        # CONTENT
        self.content = ctk.CTkFrame(self.main_frame, fg_color="#F5F7FF")
        self.content.pack(side="right", fill="both", expand=True, padx=10, pady=15)

        self.show_students_view()

    def _add_menu_button(self, parent, text, command):
        ctk.CTkButton(
            parent,
            text=text,
            width=170,
            height=40,
            corner_radius=12,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            text_color="white",
            font=f(13, "bold"),
            command=command
        ).pack(pady=6)

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # --------- ÖĞRENCİLER ----------
    def show_students_view(self):
        self.clear_content()
        self.current_student_id = None

        container = ctk.CTkFrame(self.content, fg_color="#F5F7FF")
        container.pack(fill="both", expand=True)

        left = ctk.CTkFrame(container, fg_color=SIDEBAR_BG, width=320, corner_radius=15)
        left.pack(side="left", fill="y", padx=(0, 10), pady=5)
        left.pack_propagate(False)

        ctk.CTkLabel(
            left,
            text="📚 Öğrenciler",
            font=f(16, "bold"),
            text_color=TEXT_MAIN
        ).pack(pady=(10, 5))

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            left,
            textvariable=self.search_var,
            placeholder_text="İsim ile ara...",
            width=260,
            height=32,
            corner_radius=10,
            font=f(12)
        )
        search_entry.pack(pady=(0, 10))
        search_entry.bind("<KeyRelease>", self._on_search)

        tree_frame = ctk.CTkFrame(left, fg_color="#DCE4FF", corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.student_tree = ttk.Treeview(
            tree_frame,
            columns=("username", "name"),
            show="headings",
            height=12
        )
        self.student_tree.heading("username", text="Kullanıcı Adı")
        self.student_tree.heading("name", text="Ad Soyad")

        self.student_tree.column("username", width=120, anchor="center")
        self.student_tree.column("name", width=180, anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.student_tree.pack(side="left", fill="both", expand=True)

        self.student_tree.bind("<<TreeviewSelect>>", self._on_student_select)

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(pady=5)

        self.delete_btn = ctk.CTkButton(
            btn_frame,
            text="Sil 🗑️",
            width=120,
            height=35,
            corner_radius=8,
            fg_color="#EF4444",
            hover_color="#B91C1C",
            state="disabled",
            font=f(12, "bold"),
            command=self.delete_student
        )
        self.delete_btn.pack(padx=5)

        self.detail_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=15)
        self.detail_card.pack(side="right", fill="both", expand=True, padx=(0, 5), pady=5)

        self.detail_info = tk.Text(
            self.detail_card,
            height=6,
            wrap="word",
            bg="#F9FAFF",
            fg=TEXT_MAIN,
            font=f(12),
            bd=0,
            relief="flat"
        )
        self.detail_info.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            self.detail_card,
            text="📝 Çalışma Programı",
            font=f(16, "bold"),
            text_color="#222"
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.plan_text = tk.Text(
            self.detail_card,
            wrap="word",
            bg="#F9FAFF",
            fg=TEXT_MAIN,
            font=f(12),
            bd=0,
            relief="flat",
            height=12
        )
        self.plan_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        row = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        row.pack(pady=5)

        ctk.CTkButton(
            row,
            text="Kaydet",
            width=120,
            fg_color="#3A66FF",
            hover_color="#2750cc",
            font=f(12, "bold"),
            command=self.save_plan
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            row,
            text="Otomatik Oluştur",
            width=150,
            fg_color="#22C55E",
            hover_color="#16A34A",
            font=f(12, "bold"),
            command=self.auto_plan
        ).pack(side="left", padx=5)

        self._load_students_to_tree()

    def _on_search(self, event=None):
        self._load_students_to_tree(self.search_var.get())

    def _load_students_to_tree(self, filter_text=""):
        self.student_tree.delete(*self.student_tree.get_children())
        self.student_row_map.clear()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id, u.username, s.full_name
            FROM students s
            JOIN users u ON u.id = s.user_id
        """)
        rows = cur.fetchall()
        conn.close()

        for sid, username, name in rows:
            if filter_text.lower() not in (name or "").lower():
                continue
            iid = self.student_tree.insert(
                "",
                "end",
                values=(username, name or "(İsim yok)")
            )
            self.student_row_map[iid] = sid

    def _on_student_select(self, event=None):
        sel = self.student_tree.selection()
        if not sel:
            self.current_student_id = None
            self.delete_btn.configure(state="disabled")
            self.detail_info.delete("1.0", tk.END)
            self.plan_text.delete("1.0", tk.END)
            return

        iid = sel[0]
        sid = self.student_row_map[iid]
        self.current_student_id = sid
        self.delete_btn.configure(state="normal")
        self._show_student_detail(sid)

    def _show_student_detail(self, sid):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT full_name, weak_subject, absence, avg_grade FROM students WHERE id=?", (sid,))
        info = cur.fetchone()

        cur.execute("SELECT plan_text FROM study_plans WHERE student_id=?", (sid,))
        plan_row = cur.fetchone()
        conn.close()

        self.detail_info.delete("1.0", tk.END)
        self.plan_text.delete("1.0", tk.END)

        if info:
            full, weak, absn, avg = info
            self.detail_info.insert(
                tk.END,
                f"Ad Soyad: {full}\n"
                f"Zayıf Ders: {weak}\n"
                f"Devamsızlık: {absn} saat\n"
                f"Not Ort.: {avg}\n"
            )

        if plan_row and plan_row[0]:
            self.plan_text.insert("1.0", plan_row[0])

    def save_plan(self):
        if not self.current_student_id:
            messagebox.showerror("Hata", "Öğrenci seçilmedi!")
            return

        plan = self.plan_text.get("1.0", tk.END).strip()
        if not plan:
            messagebox.showerror("Hata", "Çalışma planı boş olamaz!")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT id FROM study_plans WHERE student_id=?", (self.current_student_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE study_plans
                SET plan_text=?
                WHERE student_id=?
            """, (plan, self.current_student_id))
        else:
            cur.execute("""
                INSERT INTO study_plans (student_id, plan_text)
                VALUES (?, ?)
            """, (self.current_student_id, plan))

        conn.commit()
        conn.close()

        messagebox.showinfo("Başarılı", "Çalışma programı kaydedildi ✨")

    def auto_plan(self):
        if not self.current_student_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT weak_subject, avg_grade, absence FROM students WHERE id=?", (self.current_student_id,))
        row = cur.fetchone()
        conn.close()

        plan = generate_study_plan(row[0], row[1], row[2])
        self.plan_text.delete("1.0", tk.END)
        self.plan_text.insert("1.0", plan)

    def delete_student(self):
        if not self.current_student_id:
            return

        if not messagebox.askyesno("Onay", "Bu öğrenciyi silmek istiyor musun?"):
            return

        sid = self.current_student_id

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT user_id FROM students WHERE id=?", (sid,))
        row = cur.fetchone()

        if not row:
            conn.close()
            messagebox.showerror("Hata", "Öğrenci bulunamadı!")
            return

        user_id = row[0]

        cur.execute("DELETE FROM appointments WHERE student_id=?", (sid,))
        cur.execute("DELETE FROM courses WHERE student_id=?", (sid,))
        cur.execute("DELETE FROM study_plans WHERE student_id=?", (sid,))
        cur.execute("DELETE FROM students WHERE id=?", (sid,))
        cur.execute("DELETE FROM users WHERE id=?", (user_id,))

        conn.commit()
        conn.close()

        self.current_student_id = None
        self._load_students_to_tree()
        self.detail_info.delete("1.0", tk.END)
        self.plan_text.delete("1.0", tk.END)
        self.delete_btn.configure(state="disabled")

        messagebox.showinfo("Bilgi", "Öğrenci silindi ✓")

    # --------- RANDEVULAR ----------
    def show_appointments_view(self):
        self.clear_content()

        ctk.CTkLabel(
            self.content,
            text="Randevularım",
            font=f(22, "bold"),
            text_color="#222"
        ).pack(anchor="w", padx=20, pady=10)

        wrapper = ctk.CTkScrollableFrame(self.content, fg_color=CARD_BG, corner_radius=20)
        wrapper.pack(fill="both", expand=True, padx=20, pady=10)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.date, a.time, a.status,
                   COALESCE(s.full_name, '(İsim yok)')
            FROM appointments a
            JOIN students s ON s.id = a.student_id
            WHERE a.teacher_id=?
            ORDER BY a.date, a.time
        """, (self.app.current_user["id"],))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                wrapper,
                text="Henüz randevu yok.",
                text_color=TEXT_MUTED,
                font=f(13)
            ).pack(pady=20)
            return

        pending = [r for r in rows if r[3] == "Beklemede" or r[3] is None]
        approved = [r for r in rows if r[3] == "Onaylandı"]
        rejected = [r for r in rows if r[3] == "Reddedildi"]

        if pending:
            ctk.CTkLabel(
                wrapper,
                text="⏳ Bekleyen Randevular",
                font=f(18, "bold"),
                text_color="#6366F1"
            ).pack(anchor="w", padx=10, pady=(5, 5))

            for app_id, date, time, status, st_name in pending:
                card = ctk.CTkFrame(wrapper, fg_color="#F5F7FF", corner_radius=12)
                card.pack(fill="x", padx=10, pady=6)

                ctk.CTkLabel(
                    card,
                    text=f"{date} • {time}\nÖğrenci: {st_name}",
                    font=f(12),
                    text_color=TEXT_MAIN,
                    justify="left"
                ).pack(side="left", padx=12, pady=10)

                box = ctk.CTkFrame(card, fg_color="transparent")
                box.pack(side="right", padx=10, pady=5)

                ctk.CTkButton(
                    box,
                    text="Onayla ✓",
                    width=90,
                    height=28,
                    fg_color="#22C55E",
                    hover_color="#16A34A",
                    font=f(11, "bold"),
                    command=lambda i=app_id: self.update_appointment(i, "Onaylandı")
                ).pack(pady=2)

                ctk.CTkButton(
                    box,
                    text="Reddet ✗",
                    width=90,
                    height=28,
                    fg_color="#EF4444",
                    hover_color="#B91C1C",
                    font=f(11, "bold"),
                    command=lambda i=app_id: self.update_appointment(i, "Reddedildi")
                ).pack(pady=2)

        if approved:
            ctk.CTkLabel(
                wrapper,
                text="✔ Onaylanan Randevular",
                font=f(18, "bold"),
                text_color="#16A34A"
            ).pack(anchor="w", padx=10, pady=(20, 5))

            for app_id, date, time, status, st_name in approved:
                ctk.CTkLabel(
                    wrapper,
                    text=f"{date} • {time}\nÖğrenci: {st_name}",
                    font=f(12),
                    text_color=TEXT_MAIN,
                    justify="left"
                ).pack(anchor="w", padx=20, pady=4)

        if rejected:
            ctk.CTkLabel(
                wrapper,
                text="❌ Reddedilen Randevular",
                font=f(18, "bold"),
                text_color="#B91C1C"
            ).pack(anchor="w", padx=10, pady=(20, 5))

            for app_id, date, time, status, st_name in rejected:
                ctk.CTkLabel(
                    wrapper,
                    text=f"{date} • {time}\nÖğrenci: {st_name}",
                    font=f(12),
                    text_color=TEXT_MAIN,
                    justify="left"
                ).pack(anchor="w", padx=20, pady=4)

    def update_appointment(self, app_id, status):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE appointments SET status=? WHERE id=?", (status, app_id))
        conn.commit()
        conn.close()
        self.show_appointments_view()

    # --------- ÖĞRETMENLER ----------
    def show_teachers_view(self):
        self.clear_content()
        ctk.CTkLabel(
            self.content,
            text="Öğretmenler",
            font=f(22, "bold")
        ).pack(anchor="w", padx=20, pady=10)

        wrap = ctk.CTkScrollableFrame(self.content, fg_color=CARD_BG, corner_radius=20)
        wrap.pack(fill="both", expand=True, padx=20, pady=10)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username
            FROM users u
            JOIN teachers t ON t.user_id = u.id
        """)
        rows = cur.fetchall()
        conn.close()

        for tid, name in rows:
            card = ctk.CTkFrame(wrap, fg_color="#F0F2FF", corner_radius=12)
            card.pack(fill="x", padx=10, pady=6)

            ctk.CTkLabel(
                card,
                text=name,
                font=f(13, "bold"),
                text_color=TEXT_MAIN
            ).pack(side="left", padx=10, pady=10)

            if tid != self.app.current_user["id"]:
                ctk.CTkButton(
                    card,
                    text="Sil 🗑️",
                    width=80,
                    height=30,
                    fg_color="#EF4444",
                    hover_color="#B91C1C",
                    font=f(11, "bold"),
                    command=lambda i=tid: self.delete_teacher(i)
                ).pack(side="right", padx=10, pady=10)

    def delete_teacher(self, tid):
        if not messagebox.askyesno("Onay", "Bu öğretmeni silmek istiyor musunuz?"):
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # 🔥 önce teachers
        cur.execute("DELETE FROM teachers WHERE user_id=?", (tid,))
        # 🔥 sonra users
        cur.execute("DELETE FROM users WHERE id=?", (tid,))

        conn.commit()
        conn.close()
        self.show_teachers_view()

    # --------- RAPORLAR ----------
    def show_reports_view(self):
        self.clear_content()
        ctk.CTkLabel(
            self.content,
            text="Genel Raporlar",
            font=f(22, "bold")
        ).pack(anchor="w", padx=20, pady=10)

        card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=10)

        txt = tk.Text(
            card,
            bg="#F9FAFF",
            fg=TEXT_MAIN,
            font=f(12),
            bd=0,
            relief="flat"
        )
        txt.pack(fill="both", expand=True, padx=15, pady=15)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), AVG(avg_grade), AVG(absence) FROM students")
        total, avg_gr, avg_ab = cur.fetchone()
        conn.close()

        txt.insert(tk.END, f"Toplam öğrenci sayısı: {total}\n")
        txt.insert(tk.END, f"Ortalama not ortalaması: {round(avg_gr or 0, 2)}\n")
        txt.insert(tk.END, f"Ortalama devamsızlık: {round(avg_ab or 0, 1)} saat\n")


# =========================
# ÖĞRENCİ PANELİ
# =========================
class StudentPage(ctk.CTkFrame):
    def __init__(self, app: MainApp):
        super().__init__(app, fg_color="#F6F7FB")
        self.app = app

        top_bar = ctk.CTkFrame(self, fg_color="white", height=60)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        ctk.CTkLabel(
            top_bar,
            text=f"Öğrenci Paneli - {app.current_user['username']}",
            font=f(20, "bold"),
            text_color=TEXT_MAIN
        ).pack(side="left", padx=20)



        ctk.CTkButton(
            top_bar,
            text="Çıkış Yap",
            width=100,
            height=35,
            fg_color="#E5E7EB",
            text_color="#111",
            hover_color="#d4d6d9",
            font=f(12, "bold"),
            command=lambda: self.app.switch_frame(LoginPage)
        ).pack(side="right", padx=10)

        menu = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, width=200)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        ctk.CTkLabel(
            menu,
            text="MENÜ",
            font=f(14, "bold"),
            text_color=TEXT_MAIN
        ).pack(pady=(20, 10))

        self._add_menu_button(menu, "🧾 Bilgilerimi Düzenle", self.show_edit_profile)
        self._add_menu_button(menu, "📅 Randevu Al", self.show_appointment)
        self._add_menu_button(menu, "📂 Randevularım", self.show_my_appointments)
        self._add_menu_button(menu, "📘 Çalışma Programım", self.show_study_plan)

        self.content = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=25)
        self.content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.show_edit_profile()

    def _add_menu_button(self, parent, text, command):
        ctk.CTkButton(
            parent,
            text=text,
            width=170,
            height=45,
            corner_radius=12,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            text_color="white",
            font=f(13, "bold"),
            command=command
        ).pack(pady=7)

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # Ders ekleme (şu an menüde yok ama fonksiyon duruyor)
    def add_course(self):
        course = self.new_course.get().strip()
        grade_text = self.new_grade.get().strip()

        if not course or not grade_text:
            messagebox.showerror("Hata", "Ders adı ve not boş olamaz!")
            return

        try:
            grade = float(grade_text)
        except ValueError:
            messagebox.showerror("Hata", "Not sayısal olmalıdır!")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT id FROM students WHERE user_id=?", (self.app.current_user["id"],))
        row = cur.fetchone()

        if row is None:
            messagebox.showerror(
                "Hata",
                "Öğrenci profiliniz bulunamadı! Lütfen tekrar giriş yapın."
            )
            return

        student_id = row[0]

        cur.execute("""
            INSERT INTO courses (student_id, course_name, grade)
            VALUES (?, ?, ?)
        """, (student_id, course, grade))

        conn.commit()
        conn.close()

        messagebox.showinfo("Başarılı", "Ders eklendi 🎉")
        self.show_courses()

    # -------- Bilgilerimi Düzenle --------
    def show_edit_profile(self):
        self.clear_content()

        ctk.CTkLabel(
            self.content,
            text="Bilgilerimi Düzenle",
            font=f(22, "bold"),
            text_color="#222"
        ).pack(anchor="w", padx=20, pady=(10, 15))

        frame = ctk.CTkFrame(self.content, fg_color="#F0F2FF", corner_radius=20)
        frame.pack(fill="x", padx=20, pady=10)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT full_name, weak_subject, absence, avg_grade
            FROM students WHERE user_id=?
        """, (self.app.current_user["id"],))
        row = cur.fetchone()
        conn.close()

        full_name, weak_subject, absence, avg_grade = row

        ctk.CTkLabel(frame, text="Ad Soyad:", font=f(12, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.edit_name = ctk.CTkEntry(frame, width=300, height=35, font=f(12))
        self.edit_name.insert(0, full_name or "")
        self.edit_name.pack(anchor="w", padx=15, pady=5)

        ctk.CTkLabel(frame, text="Zayıf Ders:", font=f(12, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.edit_weak = ctk.CTkEntry(frame, width=300, height=35, font=f(12))
        self.edit_weak.insert(0, weak_subject or "")
        self.edit_weak.pack(anchor="w", padx=15, pady=5)

        ctk.CTkLabel(frame, text="Devamsızlık (saat):", font=f(12, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.edit_abs = ctk.CTkEntry(frame, width=300, height=35, font=f(12))
        self.edit_abs.insert(0, str(absence or 0))
        self.edit_abs.pack(anchor="w", padx=15, pady=5)

        ctk.CTkLabel(frame, text="Not Ortalaması:", font=f(12, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.edit_avg = ctk.CTkEntry(frame, width=300, height=35, font=f(12))
        self.edit_avg.insert(0, str(avg_grade or 0.0))
        self.edit_avg.pack(anchor="w", padx=15, pady=5)

        ctk.CTkButton(
            frame,
            text="Kaydet",
            width=140,
            fg_color="#4A6CF7",
            hover_color="#3454D1",
            font=f(12, "bold"),
            command=self.save_profile
        ).pack(anchor="center", pady=15)

    def save_profile(self):
        new_name = self.edit_name.get().strip()
        new_weak = self.edit_weak.get().strip()

        try:
            new_abs = int(self.edit_abs.get().strip())
            new_avg = float(self.edit_avg.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Devamsızlık tam sayı, not ortalaması sayı olmalıdır!")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            UPDATE students
            SET full_name=?, weak_subject=?, absence=?, avg_grade=?
            WHERE user_id=?
        """, (new_name, new_weak, new_abs, new_avg, self.app.current_user["id"]))
        conn.commit()
        conn.close()

        messagebox.showinfo("Başarılı", "Bilgileriniz güncellendi!")
        self.show_edit_profile()

    # -------- Randevu Al --------
    def show_appointment(self):
        self.clear_content()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE role='teacher'")
        teachers = [t[0] for t in cur.fetchall()]
        conn.close()

        ctk.CTkLabel(
            self.content,
            text="Randevu Al",
            font=f(22, "bold")
        ).pack(anchor="w", padx=20, pady=(10, 15))

        frame = ctk.CTkFrame(self.content, fg_color="#F0F2FF", corner_radius=25)
        frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkLabel(frame, text="Öğretmen", font=f(12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.teacher_var = ctk.StringVar(value="Seçiniz")
        ctk.CTkOptionMenu(
            frame,
            values=teachers,
            variable=self.teacher_var,
            font=f(12)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(frame, text="Tarih (GG-AA-YYYY)", font=f(12, "bold")).pack(anchor="w", padx=10, pady=(15, 3))
        self.date_entry = ctk.CTkEntry(frame, placeholder_text="01-01-2025", font=f(12))
        self.date_entry.pack(anchor="w", padx=10)

        ctk.CTkLabel(frame, text="Saat (SS:DD)", font=f(12, "bold")).pack(anchor="w", padx=10, pady=(15, 3))
        self.time_entry = ctk.CTkEntry(frame, placeholder_text="14:30", font=f(12))
        self.time_entry.pack(anchor="w", padx=10, pady=(0, 15))

        ctk.CTkButton(
            frame,
            text="Randevu Oluştur",
            fg_color="#4A6CF7",
            hover_color="#3454D1",
            font=f(13, "bold"),
            command=self.request_appointment
        ).pack(pady=15)

    def request_appointment(self):
        t = self.teacher_var.get()
        d = self.date_entry.get().strip()
        h = self.time_entry.get().strip()

        if t == "Seçiniz" or not d or not h:
            messagebox.showerror("Hata", "Tüm alanları doldur!")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username=?", (t,))
        teacher_row = cur.fetchone()
        if not teacher_row:
            conn.close()
            messagebox.showerror("Hata", "Öğretmen bulunamadı!")
            return
        teacher_id = teacher_row[0]

        cur.execute("SELECT id FROM students WHERE user_id=?", (self.app.current_user["id"],))
        student_row = cur.fetchone()

        if not student_row:
            cur.execute("""
                INSERT INTO students (user_id, full_name, weak_subject, absence, avg_grade)
                VALUES (?, ?, ?, ?, ?)
            """, (self.app.current_user["id"], "", "", 0, 0.0))
            conn.commit()
            student_id = cur.lastrowid
        else:
            student_id = student_row[0]

        cur.execute("""
            SELECT id FROM appointments
            WHERE student_id=? AND teacher_id=? AND date=? AND time=?
        """, (student_id, teacher_id, d, h))

        if cur.fetchone():
            conn.close()
            messagebox.showwarning("Uyarı", "Bu randevuyu zaten oluşturdun! 📌")
            return

        cur.execute("""
            INSERT INTO appointments (student_id, teacher_id, date, time)
            VALUES (?, ?, ?, ?)
        """, (student_id, teacher_id, d, h))

        conn.commit()
        conn.close()

        messagebox.showinfo("Tamam", "Randevu isteği gönderildi ✨")
        self.show_my_appointments()

    # -------- Randevularım --------
    def show_my_appointments(self):
        self.clear_content()

        ctk.CTkLabel(
            self.content,
            text="Randevularım",
            font=f(22, "bold"),
            text_color="#222"
        ).pack(anchor="w", padx=20, pady=10)

        wrapper = ctk.CTkScrollableFrame(self.content, fg_color="white", corner_radius=20)
        wrapper.pack(fill="both", expand=True, padx=20, pady=10)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT date, time, status,
                   (SELECT username FROM users WHERE id=a.teacher_id)
            FROM appointments a
            WHERE student_id = (SELECT id FROM students WHERE user_id=?)
            ORDER BY a.date, a.time
        """, (self.app.current_user["id"],))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                wrapper,
                text="Henüz randevu yok 🤷‍♂️",
                font=f(14),
                text_color="#555"
            ).pack(pady=20)
            return

        approved = [r for r in rows if r[2] == "Onaylandı"]
        rejected = [r for r in rows if r[2] == "Reddedildi"]
        pending = [r for r in rows if r[2] == "Beklemede" or r[2] is None]

        if pending:
            ctk.CTkLabel(
                wrapper,
                text="⏳ Bekleyen Randevular",
                font=f(18, "bold"),
                text_color="#6366F1"
            ).pack(anchor="w", padx=10, pady=(10, 5))

            for d, h, s, t in pending:
                ctk.CTkLabel(
                    wrapper,
                    text=f"{d} | {h} | Öğretmen: {t}",
                    font=f(13),
                    text_color="#111"
                ).pack(anchor="w", padx=20, pady=3)

        if approved:
            ctk.CTkLabel(
                wrapper,
                text="✔ Onaylanan Randevular",
                font=f(18, "bold"),
                text_color="#16A34A"
            ).pack(anchor="w", padx=10, pady=(15, 5))

            for d, h, s, t in approved:
                ctk.CTkLabel(
                    wrapper,
                    text=f"{d} | {h} | Öğretmen: {t}",
                    font=f(13),
                    text_color="#111"
                ).pack(anchor="w", padx=20, pady=3)

        if rejected:
            ctk.CTkLabel(
                wrapper,
                text="❌ Reddedilen Randevular",
                font=f(18, "bold"),
                text_color="#B91C1C"
            ).pack(anchor="w", padx=10, pady=(15, 5))

            for d, h, s, t in rejected:
                ctk.CTkLabel(
                    wrapper,
                    text=f"{d} | {h} | Öğretmen: {t}",
                    font=f(13),
                    text_color="#111"
                ).pack(anchor="w", padx=20, pady=3)

    # -------- Çalışma Planım --------
    def show_study_plan(self):
        self.clear_content()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT plan_text FROM study_plans
            WHERE student_id = (SELECT id FROM students WHERE user_id=?)
        """, (self.app.current_user["id"],))
        row = cur.fetchone()
        conn.close()

        ctk.CTkLabel(
            self.content,
            text="Kişisel Çalışma Programım",
            font=f(22, "bold")
        ).pack(anchor="w", padx=20, pady=10)

        plan = row[0] if row and row[0] else "Henüz oluşturulmadı."

        ctk.CTkLabel(
            self.content,
            text=plan,
            font=f(14),
            wraplength=750,
            justify="left"
        ).pack(anchor="w", padx=20, pady=20)

        ctk.CTkButton(
            self.content,
            text="PDF Olarak Kaydet",
            fg_color="#3A66FF",
            hover_color="#2750cc",
            font=f(13, "bold"),
            command=self.export_pdf
        ).pack(pady=10)

    def export_pdf(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT plan_text FROM study_plans
            WHERE student_id = (SELECT id FROM students WHERE user_id=?)
        """, (self.app.current_user["id"],))
        row = cur.fetchone()
        conn.close()

        if not row or not row[0].strip():
            messagebox.showerror("Hata", "Plan bulunamadı!")
            return

        # Masaüstü/ÇalışmaPlanları klasörü
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = os.path.join(desktop, "ÇalışmaPlanları")
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, f"calisma_plani_{self.app.current_user['username']}.pdf")

        c = canvas.Canvas(file_path)
        y = 800
        for line in wrap_text(row[0], 95):
            c.drawString(40, y, line)
            y -= 18
        c.save()

        messagebox.showinfo("Başarılı", f"PDF oluşturuldu!\n{file_path}")


# =========================
# PDF Yardımcı
# =========================
def wrap_text(text, max_len):
    words = text.split()
    lines = []
    current = []
    length = 0
    for w in words:
        extra = 1 if current else 0
        if length + len(w) + extra > max_len:
            lines.append(" ".join(current))
            current = [w]
            length = len(w)
        else:
            current.append(w)
            length += len(w) + extra
    if current:
        lines.append(" ".join(current))
    return lines


# =========================
# ÇALIŞTIR
# =========================
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
