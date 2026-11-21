"""Cá Sấu — ca biên theo tick (TICKET-02 mục 1.2, thứ tự mục 4.5). Test hộp đen qua headless.

Tách file riêng khỏi tests/test_gather_monsters.py (lát của 22520160) để không đè nhau khi tích hợp.
"""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, write_json


def run_gather(w, block, ticks=3):
    base = {"random_fish": False, "fish": [], "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [90, 0]}]}
    sc = write_json(w.path("sc.json"), {"gather": dict(base, **block)})
    code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--snapshot-every", "1", "--out", w.path("o.jsonl"))
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def croc(**kw):
    return dict({"id": "M1", "kind": "ca_sau", "pos": [50, 20], "waypoints": [[50, 20], [54, 20]]}, **kw)


class MonsterEdges(unittest.TestCase):
    def test_end_of_recoil_does_not_hit_in_same_step(self):
        """'Hết recoil về patrol, xét phát hiện/chạm từ bước kế': còn 1 bước recoil -> không hit ở tick 1, hit ở tick 2."""
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 20]},
                                  "monsters": [croc(state="recoil", state_ticks_left=1, recoil_dir=[1.0, 0.0])]})
            self.assertEqual([e["tick"] for e in events(rows, "monster_hit")], [2])

    def test_invulnerability_is_decremented_before_hit_check(self):
        """Mục 4.5: 'giảm bất tử' ở đầu bước, trước xét chạm (như hồi bắt): invuln 1 -> hết bất tử ngay bước đầu, hit tick 1."""
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 20], "invuln_ticks": 1}, "monsters": [croc()]})
            self.assertEqual([e["tick"] for e in events(rows, "monster_hit")], [1])

    def test_invulnerability_90_ticks_blocks_until_t_plus_90(self):
        """Hit ở tick t đặt bất tử 90 -> không hit trong (t, t+90), có thể hit lại từ t+90 (quái khác, sát người chơi)."""
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 20], "hp": 3},
                                  "monsters": [croc(), croc(id="M2", pos=[50, 20.5], waypoints=[[50, 20.5], [50, 20.5]])]},
                              ticks=100)
            hits = [(e["tick"], e["data"]["monster_id"]) for e in events(rows, "monster_hit")]
            self.assertEqual(hits[0], (1, "M1"))
            self.assertEqual(hits[1][0], 91)


if __name__ == "__main__":
    unittest.main()
