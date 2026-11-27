
from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import date

app = Flask(__name__)
DB = "expense_tracker.db"

# สร้างฐานข้อมูล
def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            category TEXT,
            note TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()


# หน้าเว็บไซต์
HTML = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Expense Tracker</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            padding: 20px;
            color: #1e293b;
        }
        .container {
            max-width: 900px;
            margin: auto;
        }
        h1 { text-align: center; color: #2563eb; }
        .cards {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            flex: 1;
            min-width: 180px;
            box-shadow: 0 2px 8px #ddd;
        }
        .income { color: green; }
        .expense { color: red; }
        form, .table-box, .chart-box {
            background: white;
            padding: 20px;
            margin-top: 20px;
            border-radius: 12px;
        }
        input, select, button {
            padding: 10px;
            margin: 5px 0;
            width: 100%;
            box-sizing: border-box;
        }
        button {
            background: #2563eb;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: center;
        }
        th { background: #e2e8f0; }
    </style>
</head>

<body>
<div class="container">

    <h1>ระบบบันทึกรายรับ-รายจ่าย</h1>
    <p style="text-align:center">Personal Expense Tracker</p>

    <form method="GET">
        <label>เลือกเดือนที่ต้องการดู</label>
        <input type="month" name="month" value="{{ month }}">
        <button type="submit">ดูสรุปรายเดือน</button>
    </form>

    <div class="cards">
        <div class="card">
            <h3>รายรับ</h3>
            <h2 class="income">{{ income }} บาท</h2>
        </div>

        <div class="card">
            <h3>รายจ่าย</h3>
            <h2 class="expense">{{ expense }} บาท</h2>
        </div>

        <div class="card">
            <h3>เงินคงเหลือ</h3>
            <h2>{{ balance }} บาท</h2>
        </div>
    </div>

    <form method="POST" action="/add">
        <h2>บันทึกรายการใหม่</h2>

        <label>ประเภทรายการ</label>
        <select name="type" required>
            <option value="income">รายรับ</option>
            <option value="expense">รายจ่าย</option>
        </select>

        <label>จำนวนเงิน</label>
        <input type="number" name="amount"
               min="0.01" step="0.01" required>

        <label>หมวดหมู่</label>
        <select name="category" required>
            <option>อาหาร</option>
            <option>เดินทาง</option>
            <option>ค่าหอ</option>
            <option>การศึกษา</option>
            <option>เงินเดือน</option>
            <option>อื่น ๆ</option>
        </select>

        <label>รายละเอียด</label>
        <input type="text" name="note"
               placeholder="รายละเอียดรายการ">

        <label>วันที่</label>
        <input type="date" name="date"
               value="{{ today }}" required>

        <button type="submit">บันทึกรายการ</button>
    </form>

    <div class="chart-box">
        <h2>กราฟสรุปรายรับ-รายจ่าย</h2>
        <canvas id="myChart"></canvas>
    </div>

    <div class="chart-box">
        <h2>กราฟรายจ่ายตามหมวดหมู่</h2>
        <canvas id="categoryChart"></canvas>
    </div>

    <div class="table-box">
        <h2>รายการย้อนหลังประจำเดือน</h2>

        <table>
            <tr>
                <th>วันที่</th>
                <th>ประเภท</th>
                <th>หมวดหมู่</th>
                <th>รายละเอียด</th>
                <th>จำนวนเงิน</th>
            </tr>

            {% for item in records %}
            <tr>
                <td>{{ item[5] }}</td>
                <td>{{ 'รายรับ' if item[1]=='income' else 'รายจ่าย' }}</td>
                <td>{{ item[3] }}</td>
                <td>{{ item[4] }}</td>
                <td>{{ item[2] }} บาท</td>
            </tr>
            {% endfor %}
        </table>
    </div>

</div>

<script>
    new Chart(document.getElementById('myChart'), {
        type: 'bar',
        data: {
            labels: ['รายรับ', 'รายจ่าย'],
            datasets: [{
                label: 'จำนวนเงิน (บาท)',
                data: [{{ income }}, {{ expense }}],
                backgroundColor: ['#22c55e', '#ef4444']
            }]
        }
    });

    new Chart(document.getElementById('categoryChart'), {
        type: 'pie',
        data: {
            labels: {{ categories | tojson }},
            datasets: [{
                data: {{ category_amounts | tojson }},
                backgroundColor: [
                    '#3b82f6', '#22c55e', '#f59e0b',
                    '#ef4444', '#a855f7', '#64748b'
                ]
            }]
        }
    });
</script>

</body>
</html>
"""


# บันทึกรายการ
@app.route("/add", methods=["POST"])
def add():
    conn = sqlite3.connect(DB)

    conn.execute("""
        INSERT INTO transactions
        (type, amount, category, note, date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form["type"],
        float(request.form["amount"]),
        request.form["category"],
        request.form["note"],
        request.form["date"]
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# หน้าหลักและระบบสรุปยอด
@app.route("/")
def home():
    month = request.args.get("month", date.today().strftime("%Y-%m"))

    conn = sqlite3.connect(DB)

    records = conn.execute("""
        SELECT * FROM transactions
        WHERE date LIKE ?
        ORDER BY date DESC, id DESC
    """, (month + "%",)).fetchall()

    income = sum(
        r[2] for r in records if r[1] == "income"
    )

    expense = sum(
        r[2] for r in records if r[1] == "expense"
    )

    balance = income - expense

    categories = {}
    for r in records:
        if r[1] == "expense":
            categories[r[3]] = categories.get(r[3], 0) + r[2]

    conn.close()

    return render_template_string(
        HTML,
        records=records,
        income=round(income, 2),
        expense=round(expense, 2),
        balance=round(balance, 2),
        categories=list(categories.keys()),
        category_amounts=list(categories.values()),
        month=month,
        today=date.today().isoformat()
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
