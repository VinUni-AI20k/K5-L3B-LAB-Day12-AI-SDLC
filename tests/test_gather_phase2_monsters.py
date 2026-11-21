import copy
import json
import unittest

from chonoi.sim.gather import GatherSim
from chonoi.rng import Streams
from chonoi.ids import IdAllocator

with open('game.contract.json', encoding='utf-8') as f:
    TUNING = json.load(f)['tuning']

M1 = next(m for m in TUNING['gather']['monsters']['spawns'] if m['id'] == 'M1')


class Idle:
    move = (0.0, 0.0)
    def pressed(self, button):
        return False


def make_sim(player=None, hold=None, monsters=None, day=1):
    return GatherSim(
        copy.deepcopy(TUNING),
        {'day': day, 'player': player or {}, 'hold': hold or [],
         'fish': [], 'monsters': [copy.deepcopy(M1)] if monsters is None else monsters},
        Streams(5), IdAllocator(),
    )


class Phase2MonsterTests(unittest.TestCase):
    def test_day_unlock(self):
        a = make_sim(monsters=copy.deepcopy(TUNING['gather']['monsters']['spawns']), day=1)
        b = make_sim(monsters=copy.deepcopy(TUNING['gather']['monsters']['spawns']), day=3)
        self.assertNotIn('M2', [x['id'] for x in a.monsters])
        self.assertIn('M2', [x['id'] for x in b.monsters])

    def test_patrol_speed(self):
        s = make_sim()
        before = s.monsters[0]['pos'][0]
        s.step(Idle())
        self.assertAlmostEqual(s.monsters[0]['pos'][0] - before, 1/60, places=6)

    def test_detect_chase_speed(self):
        s = make_sim(player={'pos': [67,24]})
        s.step(Idle())
        self.assertEqual(s.monsters[0]['state'], 'chase')
        self.assertAlmostEqual(s.monsters[0]['pos'][0], 60+3/60, places=6)

    def test_no_chase_if_shallow(self):
        s = make_sim(player={'pos': [62,9]})
        s.step(Idle())
        self.assertEqual(s.monsters[0]['state'], 'patrol')

    def test_hit_lifo_and_invulnerability(self):
        items = ['a', 'b', 'c', 'd', 'e', 'f']
        s = make_sim(player={'pos':[60,24], 'hp':3}, hold=items)
        ev = s.step(Idle())
        hits = [payload for name, payload in ev if name == 'monster_hit']
        self.assertEqual(len(hits), 1)
        self.assertEqual(
            [i["kind"] for i in hits[0]["lost"]],
            ["f", "e", "d"]
        )
        self.assertEqual([item["kind"] for item in s.hold], ["a", "b", "c"])
        self.assertEqual(s.hp,2)
        self.assertEqual(s.invuln_ticks,90)
        s.step(Idle())
        self.assertEqual(s.hp, 2)
        self.assertEqual(s.invuln_ticks,89)

    def test_recoil(self):
        s = make_sim(player={'pos':[59,24]})
        s.step(Idle())
        self.assertEqual(s.monsters[0]['recoil_ticks'],60)
        before = s.monsters[0]['pos'][0]
        s.step(Idle())
        self.assertAlmostEqual(s.monsters[0]['pos'][0] - before, 2/60, places=6)
        self.assertEqual(s.monsters[0]['recoil_ticks'], 59)

    def test_faint_monster(self):
        s = make_sim(player={'pos':[60,24], 'hp':1}, hold=['a','b'])
        ev = s.step(Idle())
        self.assertTrue(s.done)
        self.assertEqual(s.reason, 'fainted')
        self.assertEqual(s.hold, [])
        self.assertEqual(s.hp,0)
        self.assertIn('monster', [v['cause'] for k,v in ev if k == 'faint'])


if __name__ == '__main__':
    unittest.main()
