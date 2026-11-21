"""TICKET-02 sections 2/4: integration boundaries, not just individual hooks."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer, LiveInputs, BUTTONS_V11
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from chonoi.live import LiveGame


class DayIntegration(unittest.TestCase):
    def setUp(self):
        self.t = deepcopy(load_contract()["tuning"])
        self.sc = {"gather": {"time_left_ticks": 1, "hold": ["ca_loc"], "random_fish": False},
                   "quan": {"time_left_ticks": 1}, "day": {"money": 200, "earned": 200}}

    def session(self, days=2):
        return Session("day", self.t, deepcopy(self.sc), 42, days=days)

    def test_phase_event_context_inventory_and_reset(self):
        s=self.session(); ip=InputPlayer([], BUTTONS_V11)
        first=s.step(ip.advance(0))
        self.assertEqual([(e['name'],e['phase'],e['day']) for e in first], [('gather_end','gather',1),('phase_start','quan',1)])
        self.assertEqual(s.snapshot()['phase_tick'],0)
        self.assertEqual(s.snapshot()['stock'],{'ca_loc':1})
        self.assertEqual(s.sim.active.dish_pool,sorted(self.t['day_plan'][0]['dishes']))
        s.step(ip.advance(1)); self.assertEqual(s.snapshot()['phase'],'shop')
        self.assertEqual(s.end_row()['days_completed'],0)
        li=LiveInputs(BUTTONS_V11); li.set(buy='oxygen',shop_done=True)
        rows=s.step(li.advance())
        self.assertEqual([r['name'] for r in rows],['bought','shop_end','day_start','day_plan','phase_start'])
        self.assertEqual(rows[1]['day'],1);self.assertEqual(rows[2]['day'],2)
        self.assertEqual(s.sim.days_completed,1); self.assertEqual(s.sim.money,0)
        self.assertEqual(s.sim.earned,200);self.assertEqual(s.snapshot()['score'],500)
        self.assertEqual(s.snapshot()['active_upgrades'],{'oxygen':1})
        self.assertEqual(s.snapshot()['player']['oxygen_ticks'],2700)
        self.assertEqual(s.snapshot()['player']['hp'],3)
        self.assertEqual(s.snapshot()['phase_tick'],0)

    def test_shop_buy_pending_active_and_failures(self):
        s=self.session(); ip=InputPlayer([],BUTTONS_V11)
        s.step(ip.advance(0));s.step(ip.advance(1))
        li=LiveInputs(BUTTONS_V11);li.set(buy='hp')
        self.assertEqual(s.step(li.advance())[0]['data']['reason'],'funds')
        li.set(buy='bogus');self.assertEqual(s.step(li.advance())[0]['data']['reason'],'unknown')
        li.set(buy='oxygen');self.assertEqual(s.step(li.advance())[0]['name'],'bought')
        self.assertEqual(s.snapshot()['upgrades'],{'oxygen':1});self.assertEqual(s.snapshot()['active_upgrades'],{})
        self.assertEqual(s.sim.money,0);self.assertEqual(s.sim.earned,200)
        s.sim.money=1000;s.sim.earned=1200
        li.set(buy='oxygen');s.step(li.advance())
        li.set(buy='oxygen');self.assertEqual(s.step(li.advance())[0]['data']['reason'],'max_level')
        self.assertEqual(s.sim.money,600)

    def test_last_shop_step_buy_before_done_and_final_day(self):
        s=self.session(days=1);li=LiveInputs(BUTTONS_V11)
        s.step(li.advance());s.step(li.advance());s.sim.shop_left=1
        li.set(buy='oxygen',shop_done=True)
        rows=s.step(li.advance());self.assertEqual([r['name'] for r in rows],['bought','shop_end'])
        self.assertEqual(rows[-1]['data'],{'reason':'done'})
        self.assertEqual(s.end_row()['reason'],'days_complete');self.assertEqual(s.end_row()['days_completed'],1)

    def test_shop_auto_close_after_600_active_steps(self):
        s=self.session(days=1);li=LiveInputs(BUTTONS_V11)
        s.step(li.advance());s.step(li.advance())
        for _ in range(599):s.step(li.advance())
        self.assertFalse(s.done)
        self.assertEqual(s.step(li.advance())[-1]['data'],{'reason':'time'})
        self.assertTrue(s.done)

    def test_pause_stops_shop_buy_and_all_gameplay_resume_same_step(self):
        s=self.session();li=LiveInputs(BUTTONS_V11)
        s.step(li.advance());s.step(li.advance())
        li.set(pause=True,buy='oxygen');rows=s.step(li.advance())
        self.assertEqual([r['name'] for r in rows],['paused'])
        self.assertEqual(s.snapshot()['state'],'paused');before=deepcopy(s.snapshot())
        li.set(pause=False,buy='hp',shop_done=True)
        for _ in range(100):s.step(li.advance())
        after=s.snapshot()
        for k in ('sim_tick','phase_tick','time_left_ticks','money','upgrades'):
            self.assertEqual(before[k],after[k],k)
        self.assertEqual(after['tick'],before['tick']+100)
        li.set(pause=True,buy='oxygen')
        rows=s.step(li.advance())
        self.assertEqual([r['name'] for r in rows],['resumed','bought'])
        self.assertEqual(s.sim.shop_left,599)
        # held shop_done was latched while paused; it must not close now
        self.assertEqual(s.sim.phase,'shop')

    def test_gather_pause_freezes_fish_monsters_and_oxygen(self):
        s=Session('gather',self.t,{},1);li=LiveInputs(BUTTONS_V11);li.set(pause=True)
        s.step(li.advance());before=deepcopy(s.snapshot())
        for _ in range(10):s.step(li.advance())
        after=s.snapshot()
        for k in ('player','fish','monsters','time_left_ticks','phase_tick','sim_tick'):
            self.assertEqual(before[k],after[k],k)

    def test_quan_template_outside_day_plan_is_rejected_at_handoff(self):
        self.sc['quan']['customers'] = [{'id':'C1','table_id':'T1',
            'dish_id':'lau_mam','order_status':'unfulfillable','reserved':{}}]
        s=self.session()
        with self.assertRaises(BadInput):s.step(LiveInputs().advance())

    def test_fainted_still_opens_quan_with_empty_inventory(self):
        self.sc['gather']={'player':{'pos':[60,20],'hp':1},'hold':['ca_loc'], 'random_fish':False,
          'monsters':[{'id':'M1','kind':'ca_sau','pos':[60,20.5],'waypoints':[[60,20.5],[64,20.5]]}]}
        s=self.session();rows=s.step(LiveInputs().advance())
        self.assertIn('faint',[r['name'] for r in rows]);self.assertEqual(s.snapshot()['phase'],'quan')
        self.assertEqual(s.snapshot()['stock'],{})

    def test_day_three_has_second_monster_and_upgraded_full_hp(self):
        self.sc['day']['upgrades']={'hp':2}
        s=self.session(days=3);li=LiveInputs(BUTTONS_V11)
        for _ in range(2):
            s.step(li.advance());s.step(li.advance());li.set(shop_done=True);s.step(li.advance());li.set(shop_done=False)
        self.assertEqual(s.sim.day,3)
        self.assertEqual([m['id'] for m in s.snapshot()['monsters']],['M1','M2'])
        self.assertEqual(s.snapshot()['player']['hp'],5)

    def test_default_full_day_within_budget(self):
        s=Session('day',self.t,{},1);li=LiveInputs(BUTTONS_V11)
        for _ in range(22200):s.step(li.advance())
        self.assertEqual(s.end_row()['reason'],'days_complete');self.assertEqual(s.sim_tick,22200)

    def test_headless_days_deterministic_and_initial_events(self):
        with tempfile.TemporaryDirectory() as d:
            outputs=[]
            for i in range(2):
                path=Path(d)/f'{i}.jsonl'
                cmd=[sys.executable,'-m','chonoi.headless','--mode','day','--days','5','--seed','42','--ticks','111000','--out',str(path),'--snapshot-every','1000']
                r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
                outputs.append(path.read_bytes())
            self.assertEqual(*outputs)
            rows=[json.loads(x) for x in outputs[0].splitlines()]
            self.assertEqual([r['name'] for r in rows[:3]],['day_start','day_plan','phase_start'])
            self.assertEqual(rows[-1]['days_completed'],5)
            self.assertEqual(rows[-1]['reason'],'days_complete')
            plans=[r for r in rows if r.get('name')=='day_plan']
            self.assertEqual([r['day'] for r in plans],[1,2,3,4,5])

    def test_scenario_validation_and_plan_override(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s.json'
            p.write_text(json.dumps({'day':{'day_plan':{'1':{'dishes':{'lau_mam':2}}}}}))
            sc=load_scenario(p,'day',self.t)
            self.assertEqual(sc['day']['day_plan'][0]['ingredients'],{'ca_linh':4,'ca_keo':2,'keo_neo':2,'bong_dien_dien':2})
            for bad in ({'day':{'money':200}}, {'day':{'money':201,'earned':200}}, {'quan':{'stock':{}}},
                        {'day':{'upgrades':{'hp':3}}}, {'day':{'day_plan':{'1':{'dishes':{'lau_mam':1},'ingredients':{}}}}}):
                p.write_text(json.dumps(bad))
                with self.assertRaises(BadInput):load_scenario(p,'day',self.t)

    def test_phase_snapshot_and_one_shot_buy_in_headless(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'scenario.json').write_text(json.dumps(self.sc))
            (p/'inputs.json').write_text(json.dumps({'frames':[{'tick':2,'buy':'oxygen'}]}))
            cmd=[sys.executable,'-m','chonoi.headless','--mode','day','--seed','1','--days','2','--ticks','10','--snapshot-every','100',
                 '--scenario',str(p/'scenario.json'),'--inputs',str(p/'inputs.json'),'--out',str(p/'o.jsonl')]
            r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            rows=[json.loads(x) for x in (p/'o.jsonl').read_text().splitlines()]
            snapshots=[r for r in rows if r['type']=='snapshot']
            self.assertEqual([(r['tick'],r['phase'],r['phase_tick']) for r in snapshots[:3]],[(0,'gather',0),(1,'quan',0),(2,'shop',0)])
            self.assertEqual(len([r for r in rows if r.get('name')=='bought']),1)
            self.assertFalse(any(r.get('name')=='buy_failed' for r in rows))

    def test_cli_days_flags_and_mode_files(self):
        with tempfile.TemporaryDirectory() as d:
            for flags in (['--mode','gather','--days','1'],['--mode','day','--days','0'],['--mode','day','--days','6'],['--mode','day','--inventory',str(Path(d)/'missing')]):
                out=Path(d)/'o.jsonl';r=subprocess.run([sys.executable,'-m','chonoi.headless',*flags,'--seed','1','--ticks','0','--out',str(out)],capture_output=True)
                self.assertEqual(r.returncode,2);self.assertFalse(out.exists())

    def test_live_menu_intros_shop_and_summary(self):
        game=LiveGame('day',self.t,self.sc,1,days=1)
        game._tick_once();self.assertEqual(game.session.tick,0)
        game.navigate('play');self.assertEqual(game.screen,'dayintro')
        game.navigate('continue');game._tick_once();self.assertEqual(game.screen,'eveningintro')
        game.navigate('continue');game._tick_once();self.assertEqual(game.screen,'dayresult')
        self.assertEqual(game.session.sim.days_completed,0)
        game.navigate('continue');game.set_input({'pause':True});game._tick_once()
        self.assertTrue(game.session.paused);left=game.session.sim.shop_left
        for _ in range(10):game._tick_once()
        self.assertEqual(left,game.session.sim.shop_left)
        game.navigate('continue');game._tick_once();self.assertFalse(game.session.paused)
        game.set_input({'buy':'oxygen','shop_done':True});game._tick_once()
        self.assertEqual(game.screen,'summary')
        self.assertEqual(json.loads(game.state_json())['days_completed'],1)
        game.navigate('menu');game.navigate('play');self.assertEqual(game.session.sim.money,200)
        game.set_input({'pause':True});game._tick_once();game.navigate('menu')
        self.assertFalse(game.session.paused)
        self.assertEqual(game.screen,'menu')


class MonsterData(unittest.TestCase):
    def setUp(self):self.t=deepcopy(load_contract()['tuning'])

    def test_patrol_chase_and_detection_are_configurable(self):
        cfg=self.t['gather']['monsters']['species']['ca_sau'];cfg['patrol_speed']=0;cfg['detect_radius']=0
        s=Session('gather',self.t,{'player':{'pos':[60,20]}},1);li=LiveInputs()
        before=deepcopy(s.snapshot()['monsters']);s.step(li.advance());self.assertEqual(s.snapshot()['monsters'],before)
        cfg['detect_radius']=10;cfg['chase_speed']=0
        s.step(li.advance());self.assertEqual(s.sim.monsters[0]['state'],'chase');self.assertEqual(s.sim.monsters[0]['pos'],[60,24])

    def test_hit_radius_loss_invulnerability_recoil_from_data(self):
        cfg=self.t['gather']['monsters']['species']['ca_sau'];cfg.update(hit_radius=5,recoil_ticks=2,recoil_dist=4,chase_speed=0)
        self.t['gather']['monsters'].update(invuln_ticks=20,loss_ratio=1)
        s=Session('gather',self.t,{'player':{'pos':[60,20]},'hold':['ca_loc','ca_linh']},1);li=LiveInputs()
        s.step(li.advance());self.assertEqual(s.sim.hold,[]);self.assertEqual(s.sim.invuln_ticks,20)
        self.assertEqual(s.sim.monsters[0]['state_ticks_left'],2)
        old=s.sim.monsters[0]['pos'][:];s.step(li.advance());self.assertAlmostEqual(s.sim.monsters[0]['pos'][1]-old[1],2)

    def test_bad_monster_and_shop_data_raise_bad_input(self):
        for mutate in (lambda t:t['shop'].update(max_ticks=0),
                       lambda t:t['shop']['upgrades']['hp'][0].update(price=-1),
                       lambda t:t['gather']['monsters']['species']['ca_sau'].update(recoil_ticks=0),
                       lambda t:t['gather']['monsters'].update(loss_ratio=2)):
            tuning=deepcopy(self.t);mutate(tuning)
            with self.assertRaises(BadInput):validate_tuning(tuning)

    def test_recoil_last_step_does_not_hit(self):
        cfg=self.t['gather']['monsters']['species']['ca_sau'];cfg['recoil_dist']=0
        sc={'player':{'pos':[60,20]},'monsters':[{'id':'M1','kind':'ca_sau','pos':[60,20],
            'waypoints':[[60,20],[64,20]],'state':'recoil','state_ticks_left':1,'recoil_dir':[1,0]}]}
        s=Session('gather',self.t,sc,1);li=LiveInputs()
        self.assertNotIn('monster_hit',[r['name'] for r in s.step(li.advance())])
        self.assertIn('monster_hit',[r['name'] for r in s.step(li.advance())])


if __name__=='__main__':unittest.main()
