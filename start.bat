@echo off
echo Starting Product Comparison Tool (FastAPI)...
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python không được cài đặt hoặc không có trong PATH
    pause
    exit /b 1
)

REM Kiểm tra virtual environment
if not exist "venv\" (
    echo Tạo virtual environment...
    python -m venv venv
)

REM Kích hoạt virtual environment
call venv\Scripts\activate

REM Cài đặt dependencies
echo Cài đặt dependencies...
pip install -r requirements.txt

REM Tạo thư mục uploads nếu chưa có
if not exist "uploads\" mkdir uploads

REM Khởi chạy ứng dụng
echo.
echo Khởi chạy FastAPI...
echo Truy cập: http://localhost:5000
echo API Docs: http://localhost:5000/docs
echo Nhấn Ctrl+C để dừng
echo.
python run.py

pause