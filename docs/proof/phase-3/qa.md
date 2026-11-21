# Bằng chứng QA Phase 3

- Bản kiểm thử: `main` tại `355ce0b`.
- Môi trường: Windows PowerShell, Python 3.11.9.
- Manifest tại bản kiểm thử khai Test Contract v1.1.

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest tests.test_gather_freshness -v
python3 -m unittest discover -s tests -v
```

- Suite gather freshness: **3/3 đạt**.
- Suite trên main: **54/57 đạt** trong 11,450 giây. Ba lỗi còn lại từ Phase 2: kiểm tra `hold` chặn ca Cá Sấu không gây ngất, CLI từ chối `--days 2`, parser từ chối `pause`.
- Bốn ca hộp đen trong PR #13 chờ chạy trên CLI v1.2: ngưỡng ươn, bàn giao kho cá thể, từ chối kho đếm, giữ lại nguyên liệu và chốt giá.