from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import math
from collections import Counter

# 1. تعريف التطبيق (ده السطر اللي كان ناقص وعامل الخطأ!)
app = FastAPI(title="Natiga Pro API")

# 2. إعدادات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = 'natiga.db'

def get_db_connection():
    # تفعيل WAL mode لتسريع قاعدة البيانات لو عليها ضغط
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.row_factory = sqlite3.Row
    return conn

# 3. عرض صفحة الموقع الرئيسية (index.html) مباشرة من السيرفر
@app.get("/")
def read_root():
    return FileResponse("index.html")

# 4. مسار البحث الذكي
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
    
    order_clause = ' ORDER BY CAST("مجموع كلى" AS REAL) DESC'
    if sort_by == "lowest_total":
        order_clause = ' ORDER BY CAST("مجموع كلى" AS REAL) ASC'
    elif sort_by == "name_az":
        order_clause = ' ORDER BY "اسم الطالب" ASC'
    elif sort_by == "name_za":
        order_clause = ' ORDER BY "اسم الطالب" DESC'
    elif sort_by == "seating_asc":
        order_clause = ' ORDER BY CAST("رقم الجلوس" AS REAL) ASC'

    # بحث أوائل مدرسة أو إدارة
    if search_type in ["school", "admin"]:
        column_name = '"اسم المدرسة"' if search_type == "school" else '"اسم الادارة"'
        words = q.split()
        conditions = []
        params = []
        
        for word in words:
            conditions.append(f'{column_name} LIKE ?')
            params.append(f"%{word}%")
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        count_query = f'SELECT COUNT(*) FROM students {where_clause}'
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]
        
        if total_results == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No results found")
            
        offset = (page - 1) * limit
        data_query = f'SELECT * FROM students {where_clause} {order_clause} LIMIT ? OFFSET ?'
        data_params = params + [limit, offset]
        cursor.execute(data_query, data_params)
        students = cursor.fetchall()
        conn.close()
        
        return {
            "search_type": search_type,
            "total_results": total_results,
            "total_pages": math.ceil(total_results / limit),
            "current_page": page,
            "results": [dict(student) for student in students]
        }

    # بحث عن طالب (بالاسم أو برقم الجلوس)
    else:
        if q.isdigit() and search_type == "student" and sort_by == "highest_total":
            cursor.execute('SELECT * FROM students WHERE "رقم الجلوس" = ? OR "رقم الجلوس" = ?', (q, int(q)))
            student = cursor.fetchone()
            if student:
                conn.close()
                return {"search_type": "seating", "total_results": 1, "total_pages": 1, "current_page": 1, "results": [dict(student)]}

        words = q.split()
        word_counts = Counter(words)
        conditions = []
        params = []
        for word, count in word_counts.items():
            conditions.append('"اسم الطالب" LIKE ?')
            like_pattern = "%" + "%".join([word] * count) + "%"
            params.append(like_pattern)
                
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        count_query = f'SELECT COUNT(*) FROM students {where_clause}'
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]
        
        if total_results == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No students found")
            
        offset = (page - 1) * limit
        data_query = f'SELECT * FROM students {where_clause} {order_clause} LIMIT ? OFFSET ?'
        data_params = params + [limit, offset]
        cursor.execute(data_query, data_params)
        students = cursor.fetchall()
        conn.close()
        
        return {
            "search_type": "name", 
            "total_results": total_results, 
            "total_pages": math.ceil(total_results / limit), 
            "current_page": page, 
            "results": [dict(student) for student in students]
        }

# 5. مسار جلب الترتيب (سريع جداً من الفهارس)
@app.get("/ranks/{seating_no}")
def get_ranks(seating_no: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT gov_rank, admin_rank, school_rank 
        FROM students 
        WHERE "رقم الجلوس" = ? OR "رقم الجلوس" = ?
    ''', (seating_no, str(seating_no)))
    
    ranks = cursor.fetchone()
    conn.close()
    
    if not ranks:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return {
        "gov_rank": ranks["gov_rank"], 
        "admin_rank": ranks["admin_rank"], 
        "school_rank": ranks["school_rank"]
    }