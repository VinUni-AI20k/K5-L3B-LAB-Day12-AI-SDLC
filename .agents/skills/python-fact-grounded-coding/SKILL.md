---
name: python-fact-grounded-coding
description: Dùng TRƯỚC khi sửa luật/logic Python của Chợ Nổi (chonoi/sim/gather.py, chonoi/sim/quan.py, scenario, kho). Buộc agent lấy bằng chứng từ test và headless trước rồi mới sửa, viết test tái hiện, giữ đúng quy ước (số liệu từ contract, Streams, sort_by_id) và ghi kết quả chạy vào commit.
---

# Sửa logic Python dựa trên bằng chứng

Mục tiêu: không đoán luật, không "sửa cho test xanh". Mỗi thay đổi phải có (1) yêu cầu gốc,
(2) bằng chứng hành vi hiện tại, (3) test tái hiện, (4) kết quả chạy sau khi sửa.

Lệnh dưới đây chạy từ gốc repo. Trên Windows `python3` thường là lối tắt Microsoft Store,
nên gọi bằng `python`. Script kiểm chứng tự tạo shim `python3` cho test hộp đen.

## Bước 1. Đọc nguồn sự thật (chưa sửa gì)
1. PRD/ticket **đúng phase** đang làm (đề bài của giảng viên; phân lát trong `docs/plan/`).
2. `docs/contracts/README.md` (hợp đồng sự kiện, schema kho), `game.contract.json` (số liệu).
3. Hàm mình sở hữu theo `docs/plan/phan-chia-cong-viec.md`. Không sửa hàm của lát khác.
4. Chỗ PRD mơ hồ: ghi vào `docs/clarify.md` rồi hỏi PO, **không tự bịa luật**.

Ghi lại cho chính mình: "Yêu cầu nói X (trích nguồn), số liệu Y lấy từ khóa `Z` của contract."

## Bước 2. Lấy bằng chứng hành vi hiện tại
Chạy baseline trước khi động vào code:

```
python .agents/skills/phase-1-verification/scripts/verify_phase1.py --no-proof
```

Rồi tái hiện đúng tình huống cần sửa bằng headless (seed cố định) và đọc JSONL:

```
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl
```

- Tìm sự kiện/snapshot liên quan trong `out.jsonl` (trường `type`, `tick`, `data`).
- Cần tình huống đặc biệt: dựng `--scenario` / `--inputs` nhỏ (xem `tests/helpers.py`:
  `write_json`, `frames`) thay vì chạy dài chờ may mắn.
- Ghi **sự thật quan sát được** (tick nào, giá trị nào), không ghi suy đoán.

Nếu baseline đã đỏ: xem lỗi là do môi trường (ví dụ mã 9009 / "Python was not found" là
python3 lối tắt Store) hay do luật. Không sửa luật khi lỗi là do môi trường.

## Bước 3. Viết test tái hiện trước
- File riêng của lát: `tests/test_p<phase>_<lát>.py` (tránh đụng file người khác).
- Test phải **đỏ** với code hiện tại vì đúng lý do mong đợi. Chạy riêng:

```
python .agents/skills/phase-1-verification/scripts/verify_phase1.py --only-tests -k <tên_test>
```

## Bước 4. Sửa luật theo quy ước nhóm
- Số liệu đọc từ `game.contract.json` / dữ liệu, **không hard-code**.
- Mọi ngẫu nhiên qua `Streams` (`chonoi/rng.py`); không `random` toàn cục, không đồng hồ hệ thống.
- Danh sách thực thể sắp bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.
- Không sửa `docs/contracts/`, `game.contract.json`, schema kho khi chưa báo cả nhóm.
- Hạn chế sửa khung giảng viên (`chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py`); nếu buộc phải sửa thì báo nhóm và ghi lý do.
- Phần sáng tạo thêm phải tắt ở headless.

Soát quy ước tự động:

```
python .agents/skills/python-fact-grounded-coding/scripts/check_rules.py
```

`LỖI` (ngẫu nhiên/đồng hồ) phải sửa. `CẦN XEM` là số literal: kiểm từng số xem có phải số
liệu contract không (ví dụ `60` tick/giây là hằng đơn vị thì được; số oxy, giá món thì không).

## Bước 5. Chứng minh sau khi sửa
1. Test vừa viết chuyển xanh; toàn bộ suite vẫn xanh:
   `python .agents/skills/phase-1-verification/scripts/verify_phase1.py --no-proof`
2. Headless vẫn tất định (script so sha256 hai lần chạy cùng seed).
3. **Không sửa test cũ cho xanh** khi luật sai. Nếu test cũ thật sự sai so với PRD, ghi lý do
   và nguồn trong commit.

## Bước 6. Ghi bằng chứng vào commit
Mô tả commit có:
- Yêu cầu (nguồn PRD/ticket/clarify).
- Bằng chứng trước khi sửa (test/headless cho thấy gì).
- Lệnh đã chạy + kết quả sau khi sửa (số test, tất định đạt).
- AI sai chỗ nào (nếu có) → thêm một dòng vào `docs/ai-usage-log.md`.

## Dấu hiệu dừng lại, hỏi người
- Hai nguồn (PRD và contract) mâu thuẫn.
- Cần đổi contract/schema kho để làm được.
- Test cũ và PRD nói khác nhau.
