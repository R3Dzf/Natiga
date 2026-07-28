from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import math

app = FastAPI(title="Natiga Pro API")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = 'natiga.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA cache_size=-64000;') 
    conn.execute('PRAGMA temp_store=MEMORY;') 
    conn.execute('PRAGMA mmap_size=268435456;') 
    conn.row_factory = sqlite3.Row
    return conn

@app.head("/")
@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/search")
def smart_search(
    q: str = Query(..., min_length=1), 
    search_type: str = Query("student"), 
    sort_by: str = Query("highest_total"), 
    page: int = Query(1, ge=1), 
    limit: int = Query(6, ge=1)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    q = q.strip()
    
    order_clause = ' ORDER BY CAST(s."مجموع كلى" AS REAL) DESC'
    if sort_by == "lowest_total":
        order_clause = ' ORDER BY CAST(s."مجموع كلى" AS REAL) ASC'
    elif sort_by == "name_az":
        order_clause = ' ORDER BY s."اسم الطالب" ASC'
    elif sort_by == "name_za":
        order_clause = ' ORDER BY s."اسم الطالب" DESC'
    elif sort_by == "seating_asc":
        order_clause = ' ORDER BY CAST(s."رقم الجلوس" AS REAL) ASC'

    if search_type in ["school", "admin"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Not supported right now")
    else:
        # البحث برقم الجلوس (مباشر وسريع)
        if q.isdigit() and search_type == "student":
            cursor.execute('SELECT * FROM students WHERE "رقم الجلوس" = ?', (int(q),))
            student = cursor.fetchone()
            if student:
                conn.close()
                return {"search_type": "seating", "total_results": 1, "total_pages": 1, "current_page": 1, "results": [dict(student)]}
            else:
                conn.close()
                raise HTTPException(status_code=404, detail="No students found")

        # البحث بالاسم باستخدام محرك البحث الصاروخي FTS5
        words = q.split()
        # تنسيق الكلمات لمحرك البحث (علامة * تعني بحث بجزء من الكلمة)
        match_pattern = ' '.join([f'"{word}"*' for word in words])
        
        # عد النتائج من محرك البحث (طلقة)
        count_query = 'SELECT COUNT(*) FROM students_fts WHERE name MATCH ?'
        cursor.execute(count_query, (match_pattern,))
        total_results = cursor.fetchone()[0]
        
        if total_results == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No students found")
            
        offset = (page - 1) * limit
        # جلب البيانات عن طريق دمج جدول البحث مع جدول البيانات الرئيسي
        data_query = f'''
            SELECT s.* 
            FROM students_fts f
            JOIN students s ON s.rowid = f.rowid
            WHERE f.name MATCH ?
            {order_clause}
            LIMIT ? OFFSET ?
        '''
        cursor.execute(data_query, (match_pattern, limit, offset))
        students = cursor.fetchall()
        conn.close()
        
        return {
            "search_type": "name", 
            "total_results": total_results, 
            "total_pages": math.ceil(total_results / limit), 
            "current_page": page, 
            "results": [dict(student) for student in students]
        }

@app.get("/ranks/{seating_no}")
def get_ranks(seating_no: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT gov_rank, admin_rank, school_rank 
        FROM students 
        WHERE "رقم الجلوس" = ?
    ''', (seating_no,))
    ranks = cursor.fetchone()
    conn.close()
    if not ranks:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"gov_rank": ranks["gov_rank"], "admin_rank": ranks["admin_rank"], "school_rank": ranks["school_rank"]}

@app.get("/stats/general")
def get_general_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM general_stats')
        gen_row = cursor.fetchone()
        if not gen_row:
            raise HTTPException(status_code=404, detail="Stats not generated yet.")
        cursor.execute('SELECT * FROM top_students')
        top_students = [dict(row) for row in cursor.fetchall()]
        return {
            "total_students": gen_row["total_students"],
            "passed_students": gen_row["passed_students"],
            "success_rate": gen_row["success_rate"],
            "top_students": top_students,
            "top_admins": [],
            "top_schools": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
