from flask import Flask, render_template, request, send_file
import pandas as pd
import mysql.connector
import os
from io import BytesIO
from collections import defaultdict

app = Flask(__name__)
UPLOAD_PATH = "uploaded.csv"

def get_feature_map():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="feature_db"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT column_name, chinese_name, layer, category_type FROM features")
    rows = cursor.fetchall()
    conn.close()
    return {row["column_name"]: row for row in rows}

@app.route("/", methods=["GET", "POST"])
def index():
    df = pd.DataFrame()
    selected = []
    feature_map = get_feature_map()
    features_by_layer = defaultdict(list)

    if request.method == "POST":
        action = request.form.get("action")

        # 處理 CSV 上傳
        if action == "upload" and "csv_file" in request.files:
            csv_file = request.files["csv_file"]
            if csv_file.filename.endswith(".csv"):
                csv_file.save(UPLOAD_PATH)

        # 讀取上傳檔案
        if os.path.exists(UPLOAD_PATH):
            df = pd.read_csv(UPLOAD_PATH)

        # 整理所有特徵並依層級分類
        for col, info in feature_map.items():
            exists = col in df.columns
            features_by_layer[info["layer"]].append({
                "name": col,
                "chinese": info["chinese_name"] + (" ❌ 無資料" if not exists else ""),
                "type": info["category_type"],
                "exists": exists
            })

        if action == "select":
            selected = request.form.getlist("selected_features")

        elif action == "export":
            selected = request.form.getlist("selected_features")
            if not df.empty and selected:  # 確保有資料和選項
                export_df = pd.DataFrame()
                for col in selected:
                    if col in df.columns:
                        export_df[col] = df[col]
                    else:
                        export_df[col] = ""  # 空白欄位補上
                output = BytesIO()
                export_df.to_csv(output, index=False, encoding="utf-8-sig")
                output.seek(0)
                return send_file(
                    output,
                    mimetype="text/csv",
                    download_name="selected_features.csv",
                    as_attachment=True,
                )
            else:
                return "無效的選取或檔案未正確載入，請重新上傳 CSV 並選取欄位。", 400

    return render_template("index.html", features_by_layer=features_by_layer, selected=selected)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)