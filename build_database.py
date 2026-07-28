import pandas as pd
import sqlite3
import os

# اسم الملف المضغوط اللي فيه الـ CSV
ZIP_FILE = 'data.zip'
DB_FILE = 'natiga.db'

def build_database():
    print("جاري قراءة الملف المضغوط...")
    # قراءة الملف من الـ zip مباشرة لتوفير الرامات
    df = pd.read_csv(ZIP_FILE, compression='zip', encoding='utf-8-sig')

    print("جاري تهيئة البيانات وتسمية الأعمدة لتطابق المنصة...")
    df.rename(columns={
        'seating_no': 'رقم الجلوس',
        'arabic_name': 'اسم الطالب',
        'total_degree': 'مجموع كلى',
        'student_case_desc': 'الحالة'
    }, inplace=True)

    # إضافة أعمدة وهمية للإدارة والمدرسة لمنع أخطاء السيرفر
    df['اسم المدرسة'] = 'غير متوفر'
    df['اسم الادارة'] = 'غير متوفر'

    # تحويل المجموع لرقم
    df['مجموع كلى'] = pd.to_numeric(df['مجموع كلى'], errors='coerce')
    
    # حساب الترتيب على الجمهورية
    df['gov_rank'] = df['مجموع كلى'].rank(method='min', ascending=False).fillna(9999).astype(int)
    
    # تعطيل ترتيب المدرسة والإدارة
    df['admin_rank'] = 'N/A'
    df['school_rank'] = 'N/A'

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("جاري حفظ بيانات الطلاب في قاعدة البيانات...")
    df.to_sql('students', conn, if_exists='replace', index=False)
    
    # إنشاء الفهارس لتسريع البحث
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_seating ON students("رقم الجلوس")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON students("اسم الطالب")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_total ON students("مجموع كلى")')

    print("جاري تجهيز إحصائيات وأوائل الجمهورية...")
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

    # تفريغ جداول الإدارات والمدارس
    cursor.execute('DROP TABLE IF EXISTS admins_stats')
    cursor.execute('CREATE TABLE admins_stats (admin_name TEXT, student_count INTEGER, success_rate REAL, avg_score REAL)')
    cursor.execute('DROP TABLE IF EXISTS schools_stats')
    cursor.execute('CREATE TABLE schools_stats (school_name TEXT, admin_name TEXT, student_count INTEGER, success_rate REAL, avg_score REAL)')

    conn.commit()
    conn.close()
    print("✅ تم بناء قاعدة البيانات والإحصائيات بنجاح!")

if __name__ == '__main__':
    build_database()