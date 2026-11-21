#!/usr/bin/env python3
"""Script kiểm tra hợp đồng game.contract.json và tính tất định của headless sim."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def verify_contract():
    contract_path = os.path.join(ROOT, "game.contract.json")
    if not os.path.exists(contract_path):
        print("FAIL: game.contract.json không tồn tại", file=sys.stderr)
        return False
    with open(contract_path, encoding="utf-8") as f:
        data = json.load(f)
    if "tuning" not in data or "team_size" not in data:
        print("FAIL: game.contract.json thiếu 'tuning' hoặc 'team_size'", file=sys.stderr)
        return False
    print(f"PASS: game.contract.json hợp lệ (team_size={data['team_size']})")
    return True


def verify_determinism():
    print("Kiểm tra tính tất định (gather)...")
    with tempfile.TemporaryDirectory() as tmp:
        sc_file = os.path.join(tmp, "sc.json")
        with open(sc_file, "w", encoding="utf-8") as f:
            json.dump({"gather": {"time_left_ticks": 60}}, f)
        out1 = os.path.join(tmp, "run1.jsonl")
        out2 = os.path.join(tmp, "run2.jsonl")
        inv1 = os.path.join(tmp, "inv1.json")
        inv2 = os.path.join(tmp, "inv2.json")

        cmd1 = [sys.executable, "-m", "chonoi.headless", "--mode", "gather", "--seed", "42",
                "--ticks", "70", "--scenario", sc_file, "--out", out1, "--inventory-out", inv1]
        cmd2 = [sys.executable, "-m", "chonoi.headless", "--mode", "gather", "--seed", "42",
                "--ticks", "70", "--scenario", sc_file, "--out", out2, "--inventory-out", inv2]

        r1 = subprocess.run(cmd1, cwd=ROOT, capture_output=True, text=True)
        r2 = subprocess.run(cmd2, cwd=ROOT, capture_output=True, text=True)

        if r1.returncode != 0 or r2.returncode != 0:
            print(f"FAIL: headless gather kết thúc khác 0 ({r1.returncode}, {r2.returncode})", file=sys.stderr)
            print(r1.stderr or r2.stderr, file=sys.stderr)
            return False

        hash1, hash2 = sha256_file(out1), sha256_file(out2)
        if hash1 != hash2:
            print(f"FAIL: JSONL gather không tất định ({hash1} != {hash2})", file=sys.stderr)
            return False

        with open(inv1, "rb") as f1, open(inv2, "rb") as f2:
            if f1.read() != f2.read():
                print("FAIL: Inventory gather không khớp byte", file=sys.stderr)
                return False

    print("PASS: Tính tất định từng byte (gather) ĐẠT.")
    return True


def main():
    ok = verify_contract() and verify_determinism()
    if ok:
        print("\n===> TẤT CẢ KIỂM TRA HỢP ĐỒNG ĐẠT CHUẨN <===")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
