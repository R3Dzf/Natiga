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
    # تفعيل أنظمة الكاش المتقدمة لتسريع القراءة أضعاف مضاعفة
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA cache_size=-64000;') # كاش 64 ميجا
    conn.execute('PRAGMA temp_store=MEMORY;') # تخزين العمليات في الرامات
    conn.execute('PRAGMA mmap_size=268435456;') # تسريع الوصول للبيانات
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
    
    order_clause = ' ORDER BY CAST("مجموع كلى" AS REAL) DESC'
    if sort_by == "lowest_total":
        order_clause = ' ORDER BY CAST("مجموع كلى" AS REAL) ASC'
    elif sort_by == "name_az":
        order_clause = ' ORDER BY "اسم الطالب" ASC'
    elif sort_by == "name_za":
        order_clause = ' ORDER BY "اسم الطالب" DESC'
    elif sort_by == "seating_asc":
        order_clause = ' ORDER BY CAST("رقم الجلوس" AS REAL) ASC'

    # البحث للمدارس والإدارات (معطل حالياً من الواجهة بس متأمن هنا)
    if search_type in ["school", "admin"]:
        column_name = '"اسم المدرسة"' if search_type == "school" else '"اسم الادارة"'
        # بحث مباشر وسريع بدون تعقيد
        like_pattern = f"%{q.replace(' ', '%')}%"
        where_clause = f" WHERE {column_name} LIKE ?"
        params = [like_pattern]
        
        count_query = f'SELECT COUNT(*) FROM students {where_clause}'
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]
        
        if total_results == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No results found")
            
        offset = (page - 1) * limit
        data_query = f'SELECT * FROM students {where_clause} {order_clause} LIMIT ? OFFSET ?'
        cursor.execute(data_query, params + [limit, offset])
        students = cursor.fetchall()
        conn.close()
        
        return {
            "search_type": search_type,
            "total_results": total_results,
            "total_pages": math.ceil(total_results / limit),
            "current_page": page,
            "results": [dict(student) for student in students]
        }
    else:
        # 1. لو البحث برقم الجلوس (سريع جداً لأنه بيستخدم Index)
        if q.isdigit() and search_type == "student":
            cursor.execute('SELECT * FROM students WHERE "رقم الجلوس" = ?', (int(q),))
            student = cursor.fetchone()
            if student:
                conn.close()
                return {"search_type": "seating", "total_results": 1, "total_pages": 1, "current_page": 1, "results": [dict(student)]}
            else:
                conn.close()
                raise HTTPException(status_code=404, detail="No students found")

        # 2. لو البحث بالاسم (الخوارزمية الجديدة السريعة)
        # لو كتب "محمد احمد" هتبحث عن أي اسم فيه محمد وبعده احمد في استعلام واحد
        like_pattern = f"%{q.replace(' ', '%')}%"
        where_clause = ' WHERE "اسم الطالب" LIKE ?'
        params = [like_pattern]
        
        count_query = f'SELECT COUNT(*) FROM students {where_clause}'
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]
        
        if total_results == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No students found")
            
        offset = (page - 1) * limit
        data_query = f'SELECT * FROM students {where_clause} {order_clause} LIMIT ? OFFSET ?'
        cursor.execute(data_query, params + [limit, offset])
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
        
    return {
        "gov_rank": ranks["gov_rank"], 
        "admin_rank": ranks["admin_rank"], 
        "school_rank": ranks["school_rank"]
    }

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

        cursor.execute('SELECT * FROM admins_stats')
        admins = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM schools_stats')
        schools = [dict(row) for row in cursor.fetchall()]

        return {
            "total_students": gen_row["total_students"],
            "passed_students": gen_row["passed_students"],
            "success_rate": gen_row["success_rate"],
            "top_students": top_students,
            "top_admins": admins,
            "top_schools": schools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/stats/specific")
def get_specific_stats(entity_type: str, name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if entity_type == "admin":
            cursor.execute('SELECT * FROM admins_stats WHERE admin_name = ?', (name,))
        elif entity_type == "school":
            cursor.execute('SELECT * FROM schools_stats WHERE school_name = ?', (name,))
        else:
            raise HTTPException(status_code=400, detail="Invalid type")
            
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Stats not found")
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
