# Kiểm chứng Gather — Phase 1

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`: 32 kiểm thử đạt.
- Kiểm tra trực tiếp `GatherSim`: oxy vừa cạn và ngạt ở cùng tick dẫn đến ngất, rơi giỏ LIFO và kho rỗng; nút vừa mọc lại được hái ở bước cuối; giỏ không đủ chỗ giữ nguyên đàn và cooldown, chọn ID nhỏ khi hòa; cập bến đúng mép ở bước cuối. Cả bốn ca đạt.
- Smoke tích hợp kho Gather → Quán nằm trong suite trên và đạt.
