"""Kiem thu Lat 4: gameplay P1 va AC-P2-05/06/08/12 (Ticket-02)."""
import copy
import json
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json
from legacy_v11 import setUpModule, tearDownModule  # noqa: F401  v1.2: fixture kho đếm chạy trên manifest v1.1 tạm, xem tests/legacy_v11.py

with open('game.contract.json', encoding='utf-8') as _f:
    TUNING = json.load(_f)['tuning']
TUNING.pop('freshness', None)  # v1.2: sim dựng trực tiếp với fixture kho đếm -> giữ luật v1.1 (tests/legacy_v11.py)
Q, MENU = TUNING['quan'], TUNING['menu']
STOVE = Q['stoves'][0]
TABLE = Q['tables'][0]
DISH = 'ca_loc_nuong_trui'
PRICE = MENU[DISH]['price']


def customer(**changes):
    c = {'id': 'C1', 'table_id': TABLE['id'], 'dish_id': DISH}
    c.update(changes)
    return c


def make_sim(block):
    return QuanSim(TUNING, block, Streams(1), IdAllocator())


def step(sim, interact=False):
    return sim.step(InputState((0, 0), {}, {'interact'} if interact else set()))


def run_fixture(block, ticks=1, frames=None):
    with Workdir() as w:
        sc = write_json(w.path('scenario.json'), {'quan': block})
        out = w.path('out.jsonl')
        args = ['--mode', 'quan', '--seed', '1', '--ticks', str(ticks), '--scenario', sc,
                '--snapshot-every', '1', '--out', out]
        if frames is not None:
            args.extend(['--inputs', write_json(w.path('inputs.json'), {'frames': frames})])
        rc, err = run_headless(*args)
        return rc, err, read_jsonl(out) if rc == 0 else []


class Cooking(unittest.TestCase):
    def test_cook_started_tru_kho_theo_phan_giu(self):
        sim = make_sim({'stock': {'ca_loc': 1}, 'random_customers': False,
                        'player': {'pos': list(STOVE['pos'])}, 'customers': [customer()]})
        ev = step(sim, True)
        self.assertEqual(ev, [('cook_started', {'stove_id': STOVE['id'], 'order_id': 'C1',
                                                 'dish_id': DISH, 'items': ['ca_loc'], 'base_price': PRICE})])
        self.assertEqual(sim.stock['ca_loc'], 0)
        self.assertEqual(sim.customers[0]['reserved'], {})
        self.assertEqual(sim.customers[0]['order_status'], 'assigned')
        self.assertEqual(sim.stoves[0]['cook_ticks_left'], int(round(MENU[DISH]['cook_s'] * 60)))

    def test_dish_ready_dung_tick_khong_tang_tuoi_ngay_moi_chin(self):
        sim = make_sim({'stock': {'ca_loc': 1}, 'random_customers': False,
                        'player': {'pos': list(STOVE['pos'])}, 'customers': [customer()]})
        step(sim, True)
        cooking_ticks = int(round(MENU[DISH]['cook_s'] * 60))
        for _ in range(cooking_ticks - 1):
            self.assertNotIn('dish_ready', [name for name, _ in step(sim)])
        self.assertEqual(step(sim), [('dish_ready', {'stove_id': STOVE['id'], 'order_id': 'C1',
                                                     'dish_id': DISH})])
        self.assertEqual(sim.stoves[0]['ready_ticks'], 0)
        step(sim)
        self.assertEqual(sim.stoves[0]['ready_ticks'], 1)
        self.assertEqual(step(sim, True)[0][0], 'dish_picked')
        self.assertEqual(sim.hand, {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE})
        self.assertEqual(sim.stoves[0]['state'], 'idle')
        self.assertEqual(sim.stoves[0]['dish'], None)

    def test_bep_khong_tuong_tac_duoc_khong_duoc_chuyen_sang_ban(self):
        sim = make_sim({'random_customers': False, 'player': {'pos': list(STOVE['pos'])},
                        'tables': [{'id': TABLE['id'], 'pos': list(STOVE['pos'])}],
                        'hand': {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE},
                        'customers': [customer(state='waiting', order_status='assigned', reserved={},
                                               base_price=PRICE)]})
        self.assertEqual(step(sim, True), [])
        self.assertEqual(sim.customers[0]['state'], 'waiting')

    def test_oldest_order_then_table_id(self):
        self.assertGreaterEqual(len(Q['tables']), 4, 'AC-P2-05 can 4 ban trong manifest v1.1')
        t1, t2 = Q['tables'][:2]
        sim = make_sim({'stock': {'ca_loc': 2}, 'random_customers': False,
                        'player': {'pos': list(STOVE['pos'])},
                        'customers': [customer(id='C1', table_id=t1['id'], order_tick=4),
                                      customer(id='C2', table_id=t2['id'], order_tick=3)]})
        ev = step(sim, True)
        self.assertEqual(ev[0][1]['order_id'], 'C2')


class ServingPayment(unittest.TestCase):
    def test_served_giu_boa_theo_kien_nhan_sau_buoc_1(self):
        full = int(round(Q['patience_s'] * 60))
        block = {'random_customers': False, 'player': {'pos': list(TABLE['pos'])},
                 'hand': {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE},
                 'customers': [customer(state='waiting', order_status='assigned', reserved={},
                                        base_price=PRICE, patience_ticks_left=full)]}
        sim = make_sim(block)
        ev = step(sim, True)
        self.assertEqual(ev, [('served', {'order_id': 'C1', 'table_id': TABLE['id'],
                                          'dish_id': DISH, 'patience_ticks_left': full-1,
                                          'base_price': PRICE, 'tip': int(PRICE * Q['tip_rate'])})])
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.customers[0]['state'], 'eating')
        self.assertEqual(sim.customers[0]['eat_ticks_left'], int(round(Q['eat_s'] * 60)))

    def test_boa_bang_0_neu_ki_nhan_qua_thap(self):
        sim = make_sim({'random_customers': False, 'player': {'pos': list(TABLE['pos'])},
                        'hand': {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE},
                        'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE,
                                               patience_ticks_left=1)]})
        ev = step(sim, True)
        self.assertEqual([name for name, _ in ev], ['served'])
        self.assertEqual(ev[0][1]['tip'], 0)
        self.assertEqual(sim.customers[0]['state'], 'eating')

    def test_an_xong_pay_va_nang_uy_tin(self):
        tip = int(PRICE * Q['tip_rate'])
        sim = make_sim({'random_customers': False,
                        'customers': [customer(state='eating', order_status='served', reserved={},
                                               eat_ticks_left=1, base_price=PRICE, tip=tip)]})
        ev = step(sim)
        self.assertEqual(ev, [('paid', {'order_id': 'C1', 'table_id': TABLE['id'],
                                        'base_price': PRICE, 'tip': tip, 'amount': PRICE + tip,
                                        'reason': 'finished_eating'})])
        self.assertEqual((sim.money, sim.earned, sim.shift_earned), (PRICE+tip,) * 3)
        self.assertAlmostEqual(sim.reputation, Q['reputation_initial'] + Q['tip_reputation'])
        self.assertEqual(sim.customers, [])

    def test_dong_ca_thanh_toan_khach_dang_an(self):
        sim = make_sim({'random_customers': False, 'time_left_ticks': 1,
                        'customers': [customer(state='eating', order_status='served', reserved={},
                                               eat_ticks_left=20, base_price=PRICE, tip=0)]})
        ev = step(sim)
        self.assertEqual([name for name, _ in ev], ['paid', 'quan_end'])
        self.assertEqual(ev[0][1]['reason'], 'closing')
        self.assertEqual(ev[1][1]['shift_earned'], PRICE)
        self.assertEqual((sim.done, sim.reason), (True, 'time'))

    def test_phuc_vu_dung_tick_het_ca_duoc_tra_ngay(self):
        sim = make_sim({'random_customers': False, 'time_left_ticks': 1,
                        'player': {'pos': list(TABLE['pos'])},
                        'hand': {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE},
                        'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE,
                                               patience_ticks_left=1)]})
        ev = step(sim, True)
        self.assertEqual([name for name, _ in ev], ['served', 'paid', 'quan_end'])
        self.assertEqual(ev[1][1]['reason'], 'closing')


class ScenarioValidation(unittest.TestCase):
    def test_bad_scenario_exit_2(self):
        bad = [
            {'random_customers': 1},
            {'reputation': Q['reputation_max'] + 1},
            {'hand': {'order_id': 'C9', 'dish_id': DISH, 'base_price': PRICE}},
            {'stoves': [{'id': STOVE['id'], 'state': 'ready'}]},
            {'stoves': [{'id': STOVE['id'], 'state': 'cooking', 'dish':
                         {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE},
                         'cook_ticks_left': 0}]},
            {'customers': [customer(state='eating', order_status='reserved')]},
            {'customers': [customer(state='eating', order_status='served', base_price=PRICE,
                                    eat_ticks_left=0, tip=0)]},
            {'customers': [customer(order_status='assigned', base_price=PRICE, reserved={})]},
            {'stock': {'ca_loc': 1}, 'customers': [customer(reserved={'ca_loc': 2})]},
            {'stock': {'ca_loc': 1}, 'hand': {'order_id': 'C1', 'dish_id': DISH,
                                            'base_price': PRICE},
             'stoves': [{'id': STOVE['id'], 'state': 'ready',
                         'dish': {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE}}],
             'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE)]},
        ]
        for fixture in bad:
            with self.subTest(fixture=fixture):
                rc, err, _ = run_fixture(fixture, ticks=0)
                self.assertEqual(rc, 2, err)

    def test_valid_cooking_ready_hand_and_eating_fixtures(self):
        payload = {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE}
        valid = [
            {'stoves': [{'id': STOVE['id'], 'state': 'cooking', 'dish': payload,
                         'cook_ticks_left': 1}],
             'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE)]},
            {'stoves': [{'id': STOVE['id'], 'state': 'ready', 'dish': payload,
                         'ready_ticks': 25}],
             'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE)]},
            {'hand': payload,
             'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE)]},
            {'customers': [customer(state='eating', order_status='served', reserved={},
                                    eat_ticks_left=20, base_price=PRICE, tip=0)]}
        ]
        for fixture in valid:
            with self.subTest(fixture=fixture):
                rc, err, rows = run_fixture(dict({'random_customers': False}, **fixture), ticks=0)
                self.assertEqual(rc, 0, err)
                self.assertEqual(snapshots(rows)[0]['customers'][0]['id'], 'C1')

    def test_headless_chuoi_nau_bung_phuc_vu_thanh_toan_va_tat_dinh(self):
        block = {'random_customers': False, 'stock': {'ca_loc': 1}, 'time_left_ticks': 1200,
                 'player': {'pos': [7, 8]},
                 'stoves': [{'id': STOVE['id'], 'pos': [7, 8]}],
                 'tables': [{'id': TABLE['id'], 'pos': [10, 8]}],
                 'customers': [customer()]}
        frames = [{'tick': 0, 'interact': True}, {'tick': 1, 'interact': False},
                  {'tick': 361, 'interact': True},
                  {'tick': 362, 'interact': False, 'move': [1, 0]},
                  {'tick': 410, 'move': [0, 0]}, {'tick': 419, 'interact': True}]
        with Workdir() as w:
            sc = write_json(w.path('sc.json'), {'quan': block})
            inp = write_json(w.path('in.json'), {'frames': frames})
            results = []
            for idx in (1, 2):
                out = w.path(f'out{idx}.jsonl')
                code, err = run_headless('--mode', 'quan', '--seed', '17', '--ticks', '1100',
                                         '--scenario', sc, '--inputs', inp, '--out', out)
                self.assertEqual(code, 0, err)
                with open(out, 'rb') as f:
                    results.append(f.read())
            self.assertEqual(results[0], results[1])
            rows = [json.loads(line) for line in results[0].decode('utf-8').splitlines()]
            ev = [(r['tick'], r['name']) for r in events(rows)]
            self.assertEqual(ev, [(1, 'cook_started'), (361, 'dish_ready'),
                                  (362, 'dish_picked'), (420, 'served'), (1020, 'paid')])
            self.assertEqual(events(rows, 'paid')[0]['data']['amount'],
                             PRICE + int(PRICE * Q['tip_rate']))

    def test_headless_full_payment_event(self):
        block = {'random_customers': False,
                 'customers': [customer(state='eating', order_status='served', reserved={},
                                        eat_ticks_left=1, base_price=PRICE, tip=0)]}
        rc, err, rows = run_fixture(block)
        self.assertEqual(rc, 0, err)
        self.assertEqual(events(rows, 'paid')[0]['tick'], 1)
        self.assertEqual(events(rows, 'paid')[0]['data']['amount'], PRICE)


class Phase2Compatibility(unittest.TestCase):
    """Kiểm v1.1 theo manifest thực tế; Burn dùng tuning riêng khi extension chưa bật."""
    def test_hai_bep_hai_ban_lay_don_cu_nhat_va_toi_gan_nhat(self):
        t = copy.deepcopy(TUNING)
        self.assertEqual(len(t['quan']['stoves']), 2)
        self.assertEqual(len(t['quan']['tables']), 4)
        sim = QuanSim(t, {'random_customers': False, 'stock': {'ca_loc': 2},
                         'player': {'pos': [5, 8]},
                         'customers': [customer(id='C1', table_id='T1', order_tick=12),
                                       customer(id='C2', table_id='T2', order_tick=10)]},
                      Streams(1), IdAllocator())
        ev = step(sim, True)
        self.assertEqual(ev[0][1]['stove_id'], 'B2')
        self.assertEqual(ev[0][1]['order_id'], 'C2')
        sim.pos = [2, 8]
        ev = step(sim, True)
        self.assertEqual(ev[0][1]['stove_id'], 'B1')
        self.assertEqual(ev[0][1]['order_id'], 'C1')

    def test_dong_thoi_hai_mon_chin_theo_id_bep(self):
        t = copy.deepcopy(TUNING)
        self.assertEqual(len(t['quan']['stoves']), 2)
        self.assertEqual(len(t['quan']['tables']), 4)
        dish = {'dish_id': DISH, 'base_price': PRICE}
        stoves = [{'id': 'B2', 'state': 'cooking', 'dish': dict(dish, order_id='C2'),
                   'cook_ticks_left': 1},
                  {'id': 'B1', 'state': 'cooking', 'dish': dict(dish, order_id='C1'),
                   'cook_ticks_left': 1}]
        customers = [_p3_customer(id='C1', table_id='T1', order_status='assigned', reserved={}, base_price=PRICE),
                     _p3_customer(id='C2', table_id='T2', order_status='assigned', reserved={}, base_price=PRICE)]
        sim = QuanSim(t, {'random_customers': False, 'stoves': stoves,
                          'customers': customers}, Streams(1), IdAllocator())
        ev = step(sim)
        self.assertEqual([(n, data['stove_id']) for n, data in ev],
                         [('dish_ready', 'B1'), ('dish_ready', 'B2')])

    def test_burn_chi_khi_vuot_nguong_va_thu_giu_lai(self):
        t = copy.deepcopy(TUNING)
        t['quan']['burn_s'] = 20
        payload = {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE}
        c = customer(order_status='assigned', reserved={}, base_price=PRICE)
        for stock, want in (({'ca_loc': 1}, 'reserved'), ({}, 'unfulfillable')):
            sim = QuanSim(t, {'random_customers': False, 'stock': stock,
                              'stoves': [{'id': 'B1', 'state': 'ready', 'dish': payload,
                                          'ready_ticks': 1200}],
                              'customers': [c]}, Streams(1), IdAllocator())
            ev = step(sim)
            self.assertEqual(ev[0][0], 'dish_burnt')
            self.assertEqual(ev[0][1]['order_status'], want)
            self.assertEqual(sim.customers[0]['order_status'], want)
            self.assertEqual(sim.stoves[0]['state'], 'idle')
            self.assertEqual(sim.customers[0]['reserved'],
                             {'ca_loc': 1} if want == 'reserved' else {})

    def test_no_burn_in_core_even_after_long_ready(self):
        payload = {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE}
        t = copy.deepcopy(TUNING)
        t['quan']['burn_s'] = None  # Loi khong Burn: khong phu thuoc cau hinh extension trong manifest.
        sim = QuanSim(t, {'random_customers': False,
                          'stoves': [{'id': 'B1', 'state': 'ready', 'dish': payload,
                                      'ready_ticks': 5000}],
                          'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE)]},
                      Streams(1), IdAllocator())
        self.assertEqual(step(sim), [])
        self.assertEqual(sim.stoves[0]['state'], 'ready')



class Phase2Acceptance(unittest.TestCase):
    """Test AC-P2-05, AC-P2-06, AC-P2-08, AC-P2-12 voi manifest P2 that."""

    def test_ac_p2_05_chon_bep_truoc_ban_va_id_khi_hoa(self):
        """AC-P2-05: hoa khoang cach -> bep truoc ban, giua 2 bep -> id nho."""
        self.assertEqual(len(Q['stoves']), 2)
        self.assertEqual(len(Q['tables']), 4)
        pos = [2, 8]
        sim = make_sim({'random_customers': False, 'stock': {'ca_loc': 1},
                        'player': {'pos': pos},
                        'stoves': [{'id': 'B2', 'pos': pos}],
                        'tables': [{'id': 'T1', 'pos': pos}],
                        'customers': [customer()]})
        ev = step(sim, True)
        self.assertEqual([e[0] for e in ev], ['cook_started'])
        self.assertEqual(ev[0][1]['stove_id'], 'B1')

    def test_ac_p2_05_4_ban_khi_hoa_khoang_cach_chon_id(self):
        """AC-P2-05: hai ban cung khoang cach, giao mon cho ban id nho."""
        table_pos = [9, 2]
        payload = {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE}
        sim = make_sim({'random_customers': False,
                        'player': {'pos': table_pos},
                        'tables': [{'id': 'T2', 'pos': table_pos}],
                        'hand': payload,
                        'customers': [_p3_customer(id='C1', table_id='T1', order_status='assigned',
                                               reserved={}, base_price=PRICE),
                                      _p3_customer(id='C2', table_id='T2', order_status='assigned',
                                               reserved={}, base_price=PRICE)]})
        ev = step(sim, True)
        self.assertEqual([x[0] for x in ev], ['served'])
        self.assertEqual(ev[0][1]['table_id'], 'T1')
        self.assertEqual(next(c for c in sim.customers if c['id'] == 'C2')['state'], 'waiting')

    def test_ac_p2_05_sau_mon_tu_cong_thuc_va_gia_trong_menu(self):
        """AC-P2-05: 6 mon, cong thuc + gia + so tick nau lay tu menu, khong hardcode."""
        self.assertEqual(len(MENU), 6)
        for dish, spec in sorted(MENU.items()):
            with self.subTest(dish=dish):
                recipe = dict(spec['recipe'])
                sim = make_sim({'random_customers': False, 'player': {'pos': list(STOVE['pos'])},
                                'stock': recipe,
                                'customers': [customer(dish_id=dish)]})
                ev = step(sim, True)
                self.assertEqual(ev[0][0], 'cook_started')
                self.assertEqual(ev[0][1]['base_price'], spec['price'])
                self.assertEqual(ev[0][1]['items'], sorted(k for k,n in recipe.items() for _ in range(n)))
                self.assertEqual(sim.stoves[0]['cook_ticks_left'], int(round(spec['cook_s'] * 60)))
                self.assertEqual(sim.customers[0]['reserved'], {})
                self.assertTrue(all(sim.stock[k] == 0 for k in recipe))

    def test_ac_p2_06_tien_va_uy_tin_carry_shift_earned_reset(self):
        """AC-P2-06: money/earned/reputation qua ca; shift_earned chi cua ca hien tai."""
        first = QuanSim(TUNING, {'random_customers': False,
                                 'customers': [customer(state='eating', order_status='served',
                                                        reserved={}, eat_ticks_left=1,
                                                        base_price=PRICE, tip=12)]},
                        Streams(1), IdAllocator(), carry={'money': 200, 'earned': 250, 'reputation': 3.0})
        self.assertEqual(first.shift_earned, 0)
        self.assertEqual(step(first)[0][0], 'paid')
        self.assertEqual((first.money, first.earned, first.shift_earned), (272, 322, 72))
        self.assertAlmostEqual(first.reputation, 3.0 + Q['tip_reputation'])
        carry = {'money': first.money, 'earned': first.earned, 'reputation': first.reputation}
        second = QuanSim(TUNING, {'random_customers': False}, Streams(2), IdAllocator(), carry=carry)
        self.assertEqual((second.money, second.earned, second.shift_earned), (272, 322, 0))
        self.assertEqual(second.reputation, first.reputation)

    def test_ac_p2_08_snapshot_hud_quan_du_du_lieu(self):
        """AC-P2-08: Lat 4 ban giao state cho HUD; KHONG chung minh UI ve dat 18px."""
        session = Session('quan', TUNING, {'random_customers': False,
                                          'stock': {'ca_loc': 2},
                                          'customers': [customer()]}, seed=7)
        snap = session.snapshot()
        self.assertEqual(len(snap['stoves']), 2)
        self.assertEqual(len(snap['tables']), 4)
        self.assertTrue(all({'id', 'state', 'dish', 'cook_ticks_left', 'ready_ticks'} <= set(b) for b in snap['stoves']))
        self.assertTrue(all({'id', 'customer_id'} <= set(tb) for tb in snap['tables']))
        self.assertTrue({'dish_id', 'patience_ticks_left', 'order_status', 'reserved'} <= set(snap['customers'][0]))
        self.assertTrue({'hand', 'stock', 'time_left_ticks', 'money', 'reputation'} <= set(snap))

    def test_ac_p2_12_dung_1200_tick_bung_duoc_1201_moi_chay(self):
        """AC-P2-12: ngay 1200 khong chay; vuot 1200 phat dish_burnt."""
        t = copy.deepcopy(TUNING)
        t['quan']['burn_s'] = 20
        limit = int(round(t['quan']['burn_s'] * 60))
        dish = {'order_id': 'C1', 'dish_id': DISH, 'base_price': PRICE}
        block = {'random_customers': False, 'player': {'pos': list(STOVE['pos'])},
                 'stoves': [{'id': 'B1', 'state': 'ready', 'dish': dish, 'ready_ticks': limit-1}],
                 'customers': [customer(order_status='assigned', reserved={}, base_price=PRICE)]}
        sim = QuanSim(t, block, Streams(1), IdAllocator())
        ev = step(sim, True)
        self.assertEqual([name for name, _ in ev], ['dish_picked'])
        self.assertEqual(sim.hand['order_id'], 'C1')
        block['stoves'][0]['ready_ticks'] = limit
        sim = QuanSim(t, block, Streams(1), IdAllocator())
        ev = step(sim)
        self.assertEqual([name for name, _ in ev], ['dish_burnt'])
        self.assertEqual(ev[0][1]['order_status'], 'unfulfillable')
        self.assertEqual(sim.stoves[0]['state'], 'idle')

    def test_ac_p2_12_hai_bep_chay_cung_tick_giu_lai_co_han(self):
        """AC-P2-12: 2 bep chay theo id, chi 1 don du nguyen lieu de re-reserve."""
        t = copy.deepcopy(TUNING)
        t['quan']['burn_s'] = 20
        limit = int(round(t['quan']['burn_s'] * 60))
        payload = {'dish_id': DISH, 'base_price': PRICE}
        sim = QuanSim(t, {'random_customers': False, 'stock': {'ca_loc': 1},
                          'stoves': [
                              {'id': 'B2', 'state': 'ready', 'dish': dict(payload, order_id='C2'), 'ready_ticks': limit},
                              {'id': 'B1', 'state': 'ready', 'dish': dict(payload, order_id='C1'), 'ready_ticks': limit}],
                          'customers': [
                              customer(id='C1', table_id='T1', order_status='assigned', reserved={}, base_price=PRICE),
                              _p3_customer(id='C2', table_id='T2', order_status='assigned', reserved={}, base_price=PRICE)]},
                      Streams(1), IdAllocator())
        ev = step(sim)
        self.assertEqual([(name, data['stove_id'], data['order_status']) for name, data in ev],
                         [('dish_burnt', 'B1', 'reserved'), ('dish_burnt', 'B2', 'unfulfillable')])
        self.assertEqual({c['id']: c['order_status'] for c in sim.customers},
                         {'C1': 'reserved', 'C2': 'unfulfillable'})
        self.assertEqual(sim.stock['ca_loc'], 1)  # phan giu chua tru kho
        self.assertEqual(sim.customers[0]['reserved'], {'ca_loc': 1})


# Phase 3 - kiểm thử logic phần Lát 4 trước khi lát 0 merge items.py.
# Test dùng adapter giả đúng chữ ký đã CHỐT trong docs/plan/phase-3.md;
# khi chonoi.items xuất hiện, tự dùng module thật. KHÔNG thay cho QA_STRICT v1.2.
from contextlib import contextmanager
import importlib
import sys
import types
from unittest.mock import patch
from chonoi.ids import id_key


@contextmanager
def _p3_items_api():
    try:
        importlib.import_module('chonoi.items')
    except ModuleNotFoundError as exc:
        if exc.name != 'chonoi.items':
            raise
        module = types.ModuleType('chonoi.items')

        def spoiled(item, tuning):
            return item['fresh'] < tuning['freshness']['spoiled_below']

        def decay(items, per_tick, tuning):
            changed = []
            for item in items:
                was = spoiled(item, tuning)
                item['fresh'] = max(0.0, item['fresh'] - per_tick)
                if not was and spoiled(item, tuning):
                    changed.append(item)
            return list(reversed(changed))  # code Lát 4 phải sắp lại theo id

        def pick_freshest(items, kind, count, excludes, tuning):
            candidates = sorted((i for i in items if i['kind'] == kind and i['id'] not in excludes
                                 and not spoiled(i, tuning)), key=lambda i: (-i['fresh'], id_key(i['id'])))
            return [i['id'] for i in candidates[:count]] if len(candidates) >= count else None

        module.is_spoiled = spoiled
        module.decay = decay
        module.pick_freshest = pick_freshest
        with patch.dict(sys.modules, {'chonoi.items': module}):
            yield
    else:
        yield


def _p3_customer(**changes):
    c = {'id': 'C1', 'table_id': TABLE['id'], 'dish_id': DISH,
         'state': 'waiting', 'order_status': 'reserved', 'order_tick': 0,
         'patience_ticks_left': int(round(Q['patience_s'] * 60)), 'eat_ticks_left': 0,
         'reserved': [], 'base_price': None, 'tip': None}
    c.update(changes)
    return c


def _p3_fixture():
    t = copy.deepcopy(TUNING)
    t['freshness'] = {'initial': 100, 'gather_decay_per_s': 0.5,
                      'quan_decay_per_s': 0.25, 'spoiled_below': 30}
    sim = QuanSim(TUNING, {'random_customers': False}, Streams(1), IdAllocator())
    # Tránh đi qua _init_customers v1.1 do Lát 3 sở hữu và chưa migrate.
    sim.tuning = t
    sim.t = t['quan']
    sim.freshness = t['freshness']
    sim.stock = []
    return sim


class Phase3Staging(unittest.TestCase):
    """Lát 4 v1.2: thử riêng các hàm sở hữu; chưa chạy smoke tích hợp v1.2."""

    def test_p3_11_constructor_snapshot_and_step_keep_individual_stock(self):
        with _p3_items_api():
            t = copy.deepcopy(TUNING)
            t['freshness'] = {'initial': 100, 'gather_decay_per_s': 0.5,
                              'quan_decay_per_s': 0.25, 'spoiled_below': 30}
            # Lát 3 chưa migrate _init_customers, nên tạm thay đúng hook của lát 3.
            with patch.object(QuanSim, '_init_customers', return_value=[]):
                sim = QuanSim(t, {'random_customers': False, 'stock': [
                    {'id': 'I10', 'kind': 'ca_loc', 'fresh': 30.001},
                    {'id': 'I2', 'kind': 'ca_loc', 'fresh': 30.001}]},
                    Streams(1), IdAllocator())
            ev = step(sim)
            self.assertEqual([data['item_id'] for name, data in ev if name == 'spoiled'],
                             ['I2', 'I10'])
            self.assertIsInstance(sim.snapshot()['stock'], list)
            self.assertEqual([item['id'] for item in sim.snapshot()['stock']], ['I2', 'I10'])

    def test_p3_11_stock_decay_reserved_item_spoiled_once(self):
        with _p3_items_api():
            sim = _p3_fixture()
            sim.stock = [{'id': 'I10', 'kind': 'ca_loc', 'fresh': 30.001},
                         {'id': 'I2', 'kind': 'ca_loc', 'fresh': 30.001}]
            sim.customers = [{'reserved': ['I10'], 'order_status': 'reserved'}]
            ev = []
            sim._tick_freshness(ev)
            self.assertEqual([(name, d['item_id'], d['location']) for name, d in ev],
                             [('spoiled', 'I2', 'stock'), ('spoiled', 'I10', 'stock')])
            self.assertLess(sim.stock[0]['fresh'], 30)
            ev = []
            sim._tick_freshness(ev)
            self.assertEqual(ev, [])

    def test_p3_14_consumes_only_reserved_ids_and_freezes_fresh_price(self):
        with _p3_items_api():
            sim = _p3_fixture()
            sim.pos = list(STOVE['pos'])
            sim.stock = [{'id': 'I2', 'kind': 'bong_sung', 'fresh': 60},
                         {'id': 'I1', 'kind': 'bong_sung', 'fresh': 90},
                         {'id': 'I3', 'kind': 'ca_loc', 'fresh': 99}]
            sim.customers = [_p3_customer(dish_id='goi_bong_sung', order_status='reserved',
                                      reserved=['I1', 'I2'], state='waiting')]
            ev = []
            sim._interact(ev)
            self.assertEqual([i['id'] for i in ev[0][1]['items']], ['I1', 'I2'])
            self.assertEqual(ev[0][1]['base_price'], 30)  # floor(40 * 75 / 100)
            self.assertEqual(sim.customers[0]['base_price'], 30)
            self.assertEqual(sim.customers[0]['reserved'], [])
            self.assertEqual([i['id'] for i in sim.stock], ['I3'])
            self.assertEqual(sim.stoves[0]['dish']['base_price'], 30)

    def test_p3_14_rejects_stale_or_spoiled_reserved_before_cook(self):
        with _p3_items_api():
            sim = _p3_fixture()
            sim.pos = list(STOVE['pos'])
            sim.stock = [{'id': 'I1', 'kind': 'ca_loc', 'fresh': 29.99}]
            sim.customers = [_p3_customer(reserved=['I1'], order_status='reserved')]
            ev = []
            sim._interact(ev)
            self.assertEqual(ev, [])
            self.assertEqual([i['id'] for i in sim.stock], ['I1'])
            self.assertEqual(sim.stoves[0]['state'], 'idle')

    def test_p3_15_two_burns_same_tick_reserve_one_remaining_id(self):
        with _p3_items_api():
            sim = _p3_fixture()
            limit = int(round(sim.t['burn_s'] * 60))
            sim.stock = [{'id': 'I4', 'kind': 'ca_loc', 'fresh': 70},
                         {'id': 'I5', 'kind': 'ca_loc', 'fresh': 29}]
            sim.customers = [_p3_customer(id='C1', table_id='T1', order_status='assigned',
                                      reserved=[], base_price=40),
                             _p3_customer(id='C2', table_id='T2', order_status='assigned',
                                      reserved=[], base_price=50)]
            for stove, c in zip(sim.stoves, sim.customers):
                stove.update(state='ready', ready_ticks=limit,
                             dish={'order_id': c['id'], 'dish_id': DISH,
                                   'base_price': c['base_price']})
            ev = []
            sim._tick_stoves_and_eating(ev)
            self.assertEqual([(e, d['stove_id'], d['order_status']) for e, d in ev],
                             [('dish_burnt', 'B1', 'reserved'),
                              ('dish_burnt', 'B2', 'unfulfillable')])
            self.assertEqual(sim.customers[0]['reserved'], ['I4'])
            self.assertEqual(sim.customers[1]['reserved'], [])
            self.assertEqual(len(sim.stock), 2)  # đồ đã cháy không hoàn lại kho

    def test_p3_15_tip_uses_discounted_price_not_list_price(self):
        sim = _p3_fixture()
        sim.pos = list(TABLE['pos'])
        sim.hand = {'order_id': 'C1', 'dish_id': DISH, 'base_price': 42}
        sim.customers = [_p3_customer(order_status='assigned', state='waiting',
                                  reserved=[], base_price=42, patience_ticks_left=sim.patience_full)]
        ev = []
        sim._interact(ev)
        self.assertEqual(ev[0][1]['tip'], 8)  # floor(42 * 0.2), không phải 60 * 0.2
        self.assertEqual(sim.customers[0]['base_price'], 42)
        ev = []
        sim._pay(sim.customers[0], 'finished_eating', ev)
        self.assertEqual(ev[0][1]['amount'], 50)
        self.assertEqual(sim.earned, 50)


if __name__ == '__main__':
    unittest.main()
