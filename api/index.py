from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = "library_secret_key"

if os.environ.get('VERCEL'):
    DATABASE = "/tmp/library.db"
else:
   
    DATABASE = "library.db"

# ----------------------------
# Database Connection
# ----------------------------

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------
# Create Tables
# ----------------------------

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'Available'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS issued_books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        book_title TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


# ----------------------------
# Insert Default Books
# ----------------------------

def insert_default_books():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM books")

    count = cur.fetchone()[0]

    if count == 0:

        books = [

            ("Vistas",),
            ("Invention",),
            ("Rich & Poor",),
            ("Indian Economy",),
            ("Macroeconomics",),
            ("Microeconomics",),
            ("Python Programming",),
            ("Data Structures",),
            ("Operating System",),
            ("DBMS",),
            ("Computer Networks",),
            ("Machine Learning",)

        ]

        cur.executemany(
            "INSERT INTO books(title) VALUES(?)",
            books
        )

    conn.commit()
    conn.close()


create_tables()
insert_default_books()


# ---------------------------------
# Home Page
# ---------------------------------

@app.route("/")

def home():

    conn = get_connection()

    books = conn.execute(

        "SELECT * FROM books ORDER BY id"

    ).fetchall()

    issued = conn.execute(

        "SELECT * FROM issued_books ORDER BY id DESC"

    ).fetchall()

    total_books = conn.execute(

        "SELECT COUNT(*) FROM books"

    ).fetchone()[0]

    available_books = conn.execute(

        "SELECT COUNT(*) FROM books WHERE status='Available'"

    ).fetchone()[0]

    issued_books = conn.execute(

        "SELECT COUNT(*) FROM books WHERE status='Issued'"

    ).fetchone()[0]

    conn.close()

    return render_template(

        "index.html",

        books=books,

        issued=issued,

        total_books=total_books,

        available_books=available_books,

        issued_books=issued_books

    )
    # ---------------------------------
# Borrow Book
# ---------------------------------

@app.route("/borrow", methods=["POST"])
def borrow_book():

    student = request.form["student"].strip()
    book_id = request.form["book_id"]

    conn = get_connection()
    cur = conn.cursor()

    book = cur.execute(
        "SELECT * FROM books WHERE id=?",
        (book_id,)
    ).fetchone()

    if book:

        if book["status"] == "Available":

            cur.execute(
                "UPDATE books SET status='Issued' WHERE id=?",
                (book_id,)
            )

            cur.execute(
                """
                INSERT INTO issued_books(student_name, book_title)
                VALUES(?,?)
                """,
                (student, book["title"])
            )

            conn.commit()

            flash("Book Borrowed Successfully!", "success")

        else:

            flash("Book is already issued.", "danger")

    conn.close()

    return redirect(url_for("home"))


# ---------------------------------
# Return Book
# ---------------------------------

@app.route("/return/<int:id>")
def return_book(id):

    conn = get_connection()
    cur = conn.cursor()

    issued = cur.execute(
        "SELECT * FROM issued_books WHERE id=?",
        (id,)
    ).fetchone()

    if issued:

        cur.execute(
            """
            UPDATE books
            SET status='Available'
            WHERE title=?
            """,
            (issued["book_title"],)
        )

        cur.execute(
            "DELETE FROM issued_books WHERE id=?",
            (id,)
        )

        conn.commit()

        flash("Book Returned Successfully!", "success")

    conn.close()

    return redirect(url_for("home"))


# ---------------------------------
# Donate Book
# ---------------------------------

@app.route("/donate", methods=["POST"])
def donate_book():

    title = request.form["title"].strip()

    if title == "":

        flash("Book title cannot be empty.", "danger")

        return redirect(url_for("home"))

    conn = get_connection()

    conn.execute(

        """
        INSERT INTO books(title,status)
        VALUES(?,?)
        """,

        (title, "Available")

    )

    conn.commit()

    conn.close()

    flash("Book Donated Successfully!", "success")

    return redirect(url_for("home"))


# ---------------------------------
# Delete Book
# ---------------------------------

@app.route("/delete/<int:id>")
def delete_book(id):

    conn = get_connection()

    conn.execute(

        "DELETE FROM books WHERE id=?",

        (id,)

    )

    conn.commit()

    conn.close()

    flash("Book Deleted Successfully!", "warning")

    return redirect(url_for("home"))


# ---------------------------------
# Search Books
# ---------------------------------

@app.route("/search", methods=["GET"])
def search():

    keyword = request.args.get("keyword", "").strip()

    conn = get_connection()

    books = conn.execute(

        """
        SELECT *
        FROM books
        WHERE title LIKE ?
        ORDER BY id
        """,

        ('%' + keyword + '%',)

    ).fetchall()

    issued = conn.execute(

        "SELECT * FROM issued_books"

    ).fetchall()

    total_books = conn.execute(

        "SELECT COUNT(*) FROM books"

    ).fetchone()[0]

    available_books = conn.execute(

        "SELECT COUNT(*) FROM books WHERE status='Available'"

    ).fetchone()[0]

    issued_books = conn.execute(

        "SELECT COUNT(*) FROM books WHERE status='Issued'"

    ).fetchone()[0]

    conn.close()

    return render_template(

        "index.html",

        books=books,

        issued=issued,

        total_books=total_books,

        available_books=available_books,

        issued_books=issued_books

    )


# ---------------------------------
# Run App
# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)