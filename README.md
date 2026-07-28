<div align="center">

# 🎓 Natiga Pro

### Fast, searchable student-results platform built with FastAPI, SQLite FTS5, and a responsive web interface.

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas&logoColor=white)

</div>

---

## 📌 Overview

**Natiga Pro** is a full-stack student-results search platform designed to make large result datasets fast and easy to explore.

Instead of scanning spreadsheets manually, the application imports a compressed dataset into an optimized SQLite database, calculates student rankings, creates a full-text search index, and exposes the data through a FastAPI backend and web interface.

The project focuses on **performance, efficient data processing, fast Arabic-name search, ranking, pagination, sorting, and statistics**.

---

## ✨ Main Features

### 🔎 Smart Student Search
- Search directly by **seating number**.
- Search students by **Arabic name**.
- Partial-word matching using SQLite **FTS5** full-text search.
- Multi-word search support.
- Fast lookup even with large datasets.

### 🏆 Student Ranking
- Automatically calculates a student's overall rank from total score.
- Dedicated API endpoint for rank retrieval.
- Ranking is generated during database preparation using SQL window functions.

### ↕️ Sorting & Pagination
Search results can be sorted by:

- Highest total score.
- Lowest total score.
- Name A → Z.
- Name Z → A.
- Seating number.

Results are paginated to keep responses lightweight and the interface responsive.

### 📊 General Statistics
The API provides a statistics endpoint containing:

- Total number of students.
- Number of successful students.
- Overall success rate.
- Top-performing students.

### ⚡ High-Performance Database
The project uses several optimizations for efficient access:

- SQLite **WAL mode**.
- Memory cache tuning.
- Memory-mapped database access.
- Indexes for seating number and total score.
- SQLite **FTS5** virtual table for student names.

### 📦 Memory-Efficient Data Import
Large datasets are processed with Pandas in **chunks of 10,000 rows**, reducing memory usage during database creation.

---

## 🧠 How It Works

```text
Compressed CSV Dataset (data.zip)
             │
             ▼
      build_database.py
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
 Student Table     FTS5 Index
     │                │
     └───────┬────────┘
             ▼
        SQLite Database
             │
             ▼
         FastAPI API
             │
             ▼
       Web Interface
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python** | Backend and data-processing logic |
| **FastAPI** | REST API and application server |
| **SQLite** | Main database |
| **SQLite FTS5** | High-speed full-text Arabic-name search |
| **Pandas** | Chunked dataset processing and transformation |
| **HTML / CSS / JavaScript** | Frontend interface |
| **Uvicorn** | ASGI server |

---

## 📁 Project Structure

```text
Natiga/
│
├── main.py              # FastAPI application and API endpoints
├── build_database.py    # Dataset import, ranking, indexing, and statistics
├── index.html           # Main web interface
├── data.zip             # Compressed source dataset
├── requirements.txt     # Python dependencies
├── static/              # Frontend assets
└── README.md
```

After running the database builder, the project also generates:

```text
natiga.db                 # Optimized SQLite database
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/R3Dzf/Natiga.git
cd Natiga
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the database

```bash
python build_database.py
```

This step:

1. Reads the compressed dataset in chunks.
2. Normalizes the student data.
3. Calculates rankings.
4. Creates database indexes.
5. Builds the FTS5 search index.
6. Generates summary statistics and top-student data.

### 4. Start the application

```bash
uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## 🔌 API Endpoints

### Search Students

```http
GET /search?q={query}&search_type=student&sort_by=highest_total&page=1&limit=6
```

Search by student name or seating number.

### Student Rank

```http
GET /ranks/{seating_no}
```

Returns the stored ranking information for a student.

### General Statistics

```http
GET /stats/general
```

Returns general result statistics and top-performing students.

---

## 💡 Engineering Highlights

This project demonstrates practical experience with:

- REST API development.
- Full-text search engines.
- SQL indexing and query optimization.
- SQL window functions.
- Large-dataset processing.
- Memory-efficient chunked imports.
- Database performance tuning.
- Pagination and server-side sorting.
- Arabic text search.
- Backend/frontend integration.

---

## 🔮 Possible Future Improvements

- School and educational-administration search.
- School and administration rankings.
- Advanced statistical dashboards.
- Result comparison tools.
- Filtering by score range and student status.
- Exportable result reports.
- Caching for high-traffic deployments.
- PostgreSQL support for larger-scale production deployments.

---

## 👨‍💻 Author

**Ahmed Youssef**  
Computer & Control Engineering Student

GitHub: [@R3Dzf](https://github.com/R3Dzf)

---

<div align="center">

### ⭐ If you find Natiga Pro useful, consider starring the repository.

</div>
