# Product Comparison Tool (FastAPI)

Web application để so khớp Product ID từ checklist với Product Title trong file niche.

## Tính năng

- Upload file Excel (.xlsx, .xls)
- So khớp Product ID với Product Title
- Trích xuất Product Number từ unmatched records
- Lọc trùng theo Product Number
- Xuất file Excel với 2 sheets: Matched và Unmatched
- Giao diện web thân thiện
- API tự động tạo docs

## Cài đặt

1. **Clone repository:**
```bash
git clone <repository-url>
cd find-competitor-demo
```

2. **Tạo virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

4. **Cấu hình environment:**
- Sao chép `.env` và cập nhật các giá trị cần thiết
- Đặc biệt là `CHECKLIST_URL` với link Google Sheets của bạn

## Chạy ứng dụng

```bash
python run.py
```

Truy cập: 
- Web UI: http://localhost:5000
- API Docs: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## Cấu trúc dự án

```
find-competitor-demo/
├── app.py              # FastAPI application chính
├── run.py              # Script khởi chạy
├── requirements.txt    # Dependencies
├── .env               # Environment variables
├── .gitignore         # Git ignore rules
├── uploads/           # Thư mục upload files
├── static/            # CSS, JS, images
└── templates/         # HTML templates
    ├── base.html      # Template cơ sở
    ├── index.html     # Trang chủ
    └── result.html    # Trang kết quả
```

## API Endpoints

- `GET /` - Trang chủ upload file
- `POST /upload` - Xử lý file upload
- `GET /download` - Tải file kết quả
- `GET /docs` - API Documentation (Swagger)
- `GET /redoc` - API Documentation (ReDoc)

## Environment Variables

- `UPLOAD_FOLDER` - Thư mục upload
- `CHECKLIST_URL` - URL Google Sheets checklist