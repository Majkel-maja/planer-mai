import sqlite3
from config import APP_DIR  # używamy tego samego folderu co JSON

# Baza będzie w pliku "todo_plan.db" w katalogu MajaPlanner
DB_PATH = APP_DIR / "todo_plan.db"
DB_NAME = str(DB_PATH)


def _get_connection():
    """Łączy się z bazą SQLite i ustawia row_factory, żeby zwracać słowniki."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Tworzy bazę danych i tabelę tasks, jeśli jeszcze ich nie ma.
    Kolumny:
      - id          – techniczne ID
      - text        – treść zadania
      - done        – 0/1 czy zrobione
      - cat         – kategoria
      - meta        – np. data "dd.mm"
      - star        – 0/1 czy przypięte
      - created_seq – kolejność tworzenia
      - rep         – 0/1 czy to zadanie z auto-powtarzania
    """
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            cat TEXT,
            meta TEXT,
            star INTEGER NOT NULL DEFAULT 0,
            created_seq INTEGER,
            rep INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def save_all(tasks_data):
    """
    Zapisuje CAŁĄ listę zadań do bazy.
    Najpierw czyści tabelę, potem wstawia wszystko od nowa.
    tasks_data to lista słowników jak w app.save():
      {
        "text": ...,
        "done": True/False,
        "cat": ...,
        "meta": ...,
        "star": True/False,
        "created_seq": int,
        "rep": True/False,
      }
    """
    conn = _get_connection()
    cur = conn.cursor()

    # Czyścimy tabelę
    cur.execute("DELETE FROM tasks")

    # Wstawiamy od nowa
    for item in tasks_data:
        cur.execute(
            """
            INSERT INTO tasks (text, done, cat, meta, star, created_seq, rep)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("text", ""),
                1 if item.get("done") else 0,
                item.get("cat"),
                item.get("meta"),
                1 if item.get("star") else 0,
                item.get("created_seq"),
                1 if item.get("rep") else 0,
            ),
        )

    conn.commit()
    conn.close()


def load_all():
    """
    Wczytuje wszystkie zadania z bazy i zwraca listę słowników
    w TAKIM SAMYM formacie jak wcześniej z JSON-a.
    Jeśli tabela jeszcze nie istnieje lub jest pusta -> zwraca [].
    """
    conn = _get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT text, done, cat, meta, star, created_seq, rep
            FROM tasks
            ORDER BY created_seq ASC, id ASC
            """
        )
    except sqlite3.OperationalError:
        # tabela jeszcze nie istnieje
        conn.close()
        return []

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append(
            {
                "text": r["text"],
                "done": bool(r["done"]),
                "cat": r["cat"] or "Inne",
                "meta": r["meta"],
                "star": bool(r["star"]),
                "created_seq": r["created_seq"],
                "rep": bool(r["rep"]),
            }
        )
    return result
