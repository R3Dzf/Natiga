import pandas as pd
import sqlite3

# اسم الملف المضغوط اللي رفعناه
ZIP_FILE = 'data.zip'
DB_FILE = 'natiga.db'

def build_database():
    print("⏳ جاري قراءة الملف وتكوين قاعدة البيانات بدون استهلاك للرامات...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. قراءة الملف على دفعات (Chunks) كل دفعة 10 آلاف سطر
    chunk_size = 10000
    for i, chunk in enumerate(pd.read_csv(ZIP_FILE, compression='zip', encoding='utf-8-sig', chunksize=chunk_size)):
        chunk.rename(columns={
            'seating_no': 'رقم الجلوس',
            'arabic_name': 'اسم الطالب',
            'total_degree': 'مجموع كلى',
            'student_case_desc': 'الحالة'
        }, inplace=True)

        chunk['اسم المدرسة'] = 'غير متوفر'
        chunk['اسم الادارة'] = 'غير متوفر'
        chunk['admin_rank'] = 'N/A'
        chunk['school_rank'] = 'N/A'
        
        # تحويل المجموع لرقم
        chunk['مجموع كلى'] = pd.to_numeric(chunk['مجموع كلى'], errors='coerce')

        # حفظ الدفعة في الداتابيز (أول دفعة تنشئ الجدول، والباقي يضيف عليه)
        if i == 0:
            chunk.to_sql('students_raw', conn, if_exists='replace', index=False)
        else:
            chunk.to_sql('students_raw', conn, if_exists='append', index=False)
        
    print("✅ تم نقل جميع البيانات بنجاح! جاري حساب ترتيب الجمهورية...")
    
    # 2. حساب ترتيب الجمهورية جوه الداتابيز نفسها (عشان نوفر رامات البايثون)
    cursor.execute('DROP TABLE IF EXISTS students')
    cursor.execute('''
        CREATE TABLE students AS 
        SELECT *, RANK() OVER (ORDER BY "مجموع كلى" DESC) as gov_rank 
        FROM students_raw
    ''')
    cursor.execute('DROP TABLE students_raw')

    # 3. إنشاء الفهارس لتسريع محرك البحث
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_seating ON students("رقم الجلوس")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON students("اسم الطالب")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_total ON students("مجموع كلى")')

    print("✅ جاري تجهيز إحصائيات وأوائل الجمهورية...")
    cursor.execute('DROP TABLE IF EXISTS general_stats')
    cursor.execute('CREATE TABLE general_stats (total_students INTEGER, passed_students INTEGER, success_rate REAL)')
    
    cursor.execute('DROP TABLE IF EXISTS top_students')
    cursor.execute('CREATE TABLE top_students (seat_no TEXT, name TEXT, admin_name TEXT, school_name TEXT, score REAL)')

    # الإحصائيات العامة
    cursor.execute('SELECT COUNT(*) FROM students')
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM students WHERE الحالة LIKE '%ناجح%'")
    passed = cursor.fetchone()[0]
    rate = round((passed / total) * 100, 1) if total > 0 else 0
    cursor.execute('INSERT INTO general_stats VALUES (?, ?, ?)', (total, passed, rate))

    # أوائل الجمهورية (أعلى 15 طالب)
    cursor.execute('''
        INSERT INTO top_students (seat_no, name, admin_name, school_name, score)
        SELECT "رقم الجلوس", "اسم الطالب", "اسم الادارة", "اسم المدرسة", CAST("مجموع كلى" AS REAL) AS score
        FROM students
        WHERE "مجموع كلى" IS NOT NULL
        ORDER BY score DESC
        LIMIT 15
    ''')

    # جداول فارغة للمدارس والإدارات لمنع انهيار السيرفر
    cursor.execute('DROP TABLE IF EXISTS admins_stats')
    cursor.execute('CREATE TABLE admins_stats (admin_name TEXT, student_count INTEGER, success_rate REAL, avg_score REAL)')
    cursor.execute('DROP TABLE IF EXISTS schools_stats')
    cursor.execute('CREATE TABLE schools_stats (school_name TEXT, admin_name TEXT, student_count INTEGER, success_rate REAL, avg_score REAL)')

    conn.commit()
    conn.close()
    print("🚀 تم بناء قاعدة البيانات بالكامل وبنجاح تام!")

if __name__ == '__main__':
    build_database()