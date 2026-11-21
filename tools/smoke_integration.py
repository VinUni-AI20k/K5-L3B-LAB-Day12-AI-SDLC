"""Smoke test hai tiến trình Gather -> Quán qua file kho (Bắt buộc theo DoD PRD-0).

Cách dùng:
    python tools/smoke_integration.py
"""

import json
import os
import subprocess
import sys
import tempfile


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = f".{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["PYTHONIOENCODING"] = "utf-8"

    with tempfile.TemporaryDirectory() as tmpdir:
        sc_path = os.path.join(tmpdir, "sc.json")
        in_path = os.path.join(tmpdir, "in.json")
        inv_path = os.path.join(tmpdir, "kho.json")
        g_out = os.path.join(tmpdir, "gather.jsonl")
        q_out = os.path.join(tmpdir, "quan.jsonl")

        # 1. Tạo scenario có sẵn đồ trong giỏ và input bấm interact tại dock (tick 0)
        sample_items = {"bong_sung": 2, "ca_loc": 1}
        with open(sc_path, "w", encoding="utf-8") as f:
            json.dump({"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}}, f)

        with open(in_path, "w", encoding="utf-8") as f:
            json.dump({"frames": [{"tick": 0, "interact": True}]}, f)

        # 2. Tiến trình 1: Gather kết thúc xuất kho
        cmd_g = [
            sys.executable,
            "-m",
            "chonoi.headless",
            "--mode",
            "gather",
            "--seed",
            "42",
            "--ticks",
            "1",
            "--scenario",
            sc_path,
            "--inputs",
            in_path,
            "--inventory-out",
            inv_path,
            "--out",
            g_out,
        ]
        res_g = subprocess.run(cmd_g, capture_output=True, text=True, cwd=root, env=env)
        if res_g.returncode != 0:
            print(f"[FAIL] Tiến trình Gather thất bại (mã {res_g.returncode}):\n{res_g.stderr}", file=sys.stderr)
            return res_g.returncode

        if not os.path.exists(inv_path):
            print(f"[FAIL] Gather không xuất file kho tại {inv_path}!", file=sys.stderr)
            return 1

        with open(inv_path, "r", encoding="utf-8") as f:
            inv_data = json.load(f)

        if inv_data.get("items") != sample_items:
            print(f"[FAIL] Nội dung kho sai lệch: nhận {inv_data.get('items')}, kỳ vọng {sample_items}", file=sys.stderr)
            return 1

        # 3. Tiến trình 2: Quán nạp file kho vừa xuất
        cmd_q = [
            sys.executable,
            "-m",
            "chonoi.headless",
            "--mode",
            "quan",
            "--seed",
            "42",
            "--ticks",
            "1",
            "--inventory",
            inv_path,
            "--out",
            q_out,
        ]
        res_q = subprocess.run(cmd_q, capture_output=True, text=True, cwd=root, env=env)
        if res_q.returncode != 0:
            print(f"[FAIL] Tiến trình Quán thất bại (mã {res_q.returncode}):\n{res_q.stderr}", file=sys.stderr)
            return res_q.returncode

        print("[PASS] Smoke test 2 tiến trình thành công (DoD PRD-0):")
        print(f"       1. Gather cập bến xuất file kho: {sample_items}")
        print("       2. Quán đọc thành công kho và khởi tạo phiên chơi tick 0 hợp lệ.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
