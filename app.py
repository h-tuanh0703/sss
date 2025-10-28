import os
import pandas as pd
import numpy as np
import re
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import shutil

load_dotenv()

app = FastAPI(title="Niche Competitor Finder")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_product_number(title):
    """Trích xuất product_number từ Product Title"""
    if pd.isna(title):
        return None
    title = str(title)
    pattern = r'\b([A-Z0-9-]{3,})\b'
    matches = re.findall(pattern, title)
    return matches[0] if matches else None

async def process_files() -> dict:
    """Xử lý logic chính từ Colab"""
    try:
        checklist_url = os.getenv('CHECKLIST_URL')
        checklist = pd.read_csv(checklist_url)
        
        upload_path = os.path.join(UPLOAD_FOLDER, 'niche_file.xlsx')
        dryer_niche = pd.read_excel(upload_path)
        
        product_ids = checklist['product_id'].dropna().astype(str).unique()
        
        mask = dryer_niche['Product Title'].astype(str).apply(
            lambda title: any(pid in title for pid in product_ids)
        )
        
        matched = dryer_niche[mask].copy()
        unmatched = dryer_niche[~mask].copy()
        
        unmatched['product_number'] = unmatched['Product Title'].apply(extract_product_number)
        
        has_number = unmatched[unmatched['product_number'].notna()].copy()
        no_number = unmatched[unmatched['product_number'].isna()].copy()
        
        has_number_unique = has_number.drop_duplicates(subset='product_number', keep='first')
        unmatched_final = pd.concat([has_number_unique, no_number], ignore_index=True)
        
        output_path = os.path.join(UPLOAD_FOLDER, 'compare_product_id_vs_title.xlsx')
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            matched.to_excel(writer, index=False, sheet_name='Matched')
            unmatched_final.to_excel(writer, index=False, sheet_name='Unmatched')
        
        return {
            'success': True,
            'matched_count': len(matched),
            'unmatched_original': len(unmatched),
            'unmatched_final': len(unmatched_final),
            'output_file': output_path,
            'matched_data': matched.to_dict('records'),
            'unmatched_data': unmatched_final.to_dict('records'),
            'brands': sorted(list(set([str(b) for b in matched.get('Brand', []) if pd.notna(b)] + [str(b) for b in unmatched_final.get('Brand', []) if pd.notna(b)])))
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        return templates.TemplateResponse("index.html", {"request": request, "toast_message": "File không hợp lệ. Chỉ chấp nhận .xlsx, .xls", "toast_type": "error"})
    
    filepath = os.path.join(UPLOAD_FOLDER, 'niche_file.xlsx')
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = await process_files()
    
    if result['success']:
        toast_message = f"Xử lý thành công! Matched: {result['matched_count']}, Unmatched: {result['unmatched_original']} → {result['unmatched_final']}"
        return templates.TemplateResponse("result.html", {"request": request, "result": result, "toast_message": toast_message, "toast_type": "success"})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "toast_message": f"Lỗi: {result['error']}", "toast_type": "error"})

@app.get("/download")
async def download_file():
    output_path = os.path.join(UPLOAD_FOLDER, 'compare_product_id_vs_title.xlsx')
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="File không tồn tại")
    return FileResponse(output_path, filename='compare_product_id_vs_title.xlsx')

@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request):
    try:
        upload_path = os.path.join(UPLOAD_FOLDER, 'compare_product_id_vs_title.xlsx')
        if not os.path.exists(upload_path):
            return templates.TemplateResponse("index.html", {"request": request, "toast_message": "Chưa có dữ liệu. Vui lòng upload file trước.", "toast_type": "warning"})
        
        matched_df = pd.read_excel(upload_path, sheet_name='Matched')
        unmatched_df = pd.read_excel(upload_path, sheet_name='Unmatched')
        
        # Tính toán unmatched_original từ dữ liệu gốc
        original_path = os.path.join(UPLOAD_FOLDER, 'niche_file.xlsx')
        if os.path.exists(original_path):
            original_df = pd.read_excel(original_path)
            unmatched_original = len(original_df) - len(matched_df)
        else:
            # Nếu không có file gốc, ước tính từ số lượng hiện tại
            unmatched_original = len(unmatched_df)
        
        result = {
            'matched_count': len(matched_df),
            'unmatched_original': unmatched_original,
            'unmatched_final': len(unmatched_df),
            'matched_data': matched_df.to_dict('records'),
            'unmatched_data': unmatched_df.to_dict('records'),
            'brands': sorted(list(set([str(b) for b in matched_df.get('Brand', []) if pd.notna(b)] + [str(b) for b in unmatched_df.get('Brand', []) if pd.notna(b)])))
        }
        
        return templates.TemplateResponse("result.html", {"request": request, "result": result})
        
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "toast_message": f"Lỗi: {str(e)}", "toast_type": "error"})

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    try:
        upload_path = os.path.join(UPLOAD_FOLDER, 'compare_product_id_vs_title.xlsx')
        if not os.path.exists(upload_path):
            return templates.TemplateResponse("index.html", {"request": request, "toast_message": "Chưa có dữ liệu. Vui lòng upload file trước.", "toast_type": "warning"})
        
        unmatched_df = pd.read_excel(upload_path, sheet_name='Unmatched')
        
        brand_stats = unmatched_df.groupby('Brand').size().reset_index(name='count')
        brand_stats = brand_stats.sort_values('count', ascending=False)
        
        total_unmatched = len(unmatched_df)
        brand_stats['percentage'] = (brand_stats['count'] / total_unmatched * 100).round(2)
        
        stats_data = {
            'total_unmatched': total_unmatched,
            'brand_stats': brand_stats.to_dict('records'),
            'top_brands': brand_stats.head(10).to_dict('records')
        }
        
        return templates.TemplateResponse("stats.html", {"request": request, "stats": stats_data})
        
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "toast_message": f"Lỗi: {str(e)}", "toast_type": "error"})

# Tạo thư mục uploads khi khởi động
os.makedirs(UPLOAD_FOLDER, exist_ok=True)