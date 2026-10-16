import copy
import importlib
import json
from pathlib import Path
import random
import unittest
from unittest.mock import Mock, patch
from scanner import analyze, combine_pages, fetch_snapshot, identity

FIXTURE = json.loads((Path(__file__).parents[1]/'fixtures'/'snapshot.json').read_text())


class ScannerTests(unittest.TestCase):
    def setUp(self): self.pages = copy.deepcopy(FIXTURE['pages'])

    def test_known_fixture_and_peer_exclusion(self):
        r = analyze(self.pages)
        self.assertEqual([c['name'] for c in r['candidates']], ['Refined Example Drill', 'Sharp Example Blade'])
        self.assertEqual(r['candidates'][0]['peerMedian'], 1550000)
        self.assertEqual(r['candidates'][0]['conditionalNet'], 870000)

    def test_order_independence(self):
        before = analyze(self.pages)
        random.Random(42).shuffle(self.pages)
        for p in self.pages: random.Random(2).shuffle(p['auctions'])
        self.assertEqual(analyze(self.pages), before)

    def test_identical_uuid_deduplicates(self):
        self.pages[1]['auctions'].append(copy.deepcopy(self.pages[0]['auctions'][0]))
        self.assertEqual(analyze(self.pages)['auctionCount'], 16)

    def test_conflicting_uuid_rejected(self):
        a = copy.deepcopy(self.pages[0]['auctions'][0]);a['starting_bid'] += 1
        self.pages[1]['auctions'].append(a)
        with self.assertRaises(ValueError): analyze(self.pages)

    def test_partial_or_mixed_snapshot_rejected(self):
        with self.assertRaises(ValueError): analyze(self.pages[:1])
        self.pages[1]['lastUpdated'] += 1
        with self.assertRaises(ValueError): analyze(self.pages)

    def test_pet_levels_and_upgrades_stay_distinct(self):
        a = self.pages[0]['auctions'][0]
        for name in ['Sharp Example Blade ✪', '[Lvl 100] Sharp Example Blade', 'Ancient Example Blade']:
            self.assertNotEqual(identity(a), identity({**a, 'item_name': name}))
        self.assertNotEqual(identity(a), identity({**a, 'item_lore': 'Damage: +101'}))
        self.assertEqual(identity(a), identity({**a, 'item_name': '§a'+a['item_name']}))

    def test_stale_and_future_snapshot_rejected(self):
        now = self.pages[0]['lastUpdated']
        for t in [now+121000, now-1, float('nan')]:
            with self.assertRaises(ValueError): analyze(self.pages, now=t)

    def test_insufficient_peers_and_expired_excluded(self):
        r = analyze(self.pages)
        self.assertEqual(r['excluded']['invalid_or_expired'], 1)
        self.assertEqual(r['excluded']['not_active_bin'], 1)
        self.assertEqual(r['excluded']['insufficient_comparable_groups'], 3)

    def test_invalid_configuration_and_missing_identity(self):
        for kw in [{'maximum_ratio':1},{'fee_rate':-1},{'minimum_comparables':1}]:
            with self.assertRaises(ValueError): analyze(self.pages, **kw)
        self.pages[0]['auctions'][0]['item_lore']=''
        self.assertEqual(analyze(self.pages)['excluded']['missing_identity'],1)

    def test_fetch_is_bounded_and_detects_rollover(self):
        session = Mock(); responses=[]
        for p in self.pages:
            response=Mock();response.json.return_value=p;responses.append(response)
        session.get.side_effect=responses
        self.assertEqual(fetch_snapshot(session), self.pages)
        self.assertEqual(session.get.call_count,2)
        self.assertEqual(session.get.call_args.kwargs['timeout'],15)
        session.get.side_effect=responses
        with self.assertRaises(ValueError): fetch_snapshot(session,max_pages=1)
        self.pages[1]['lastUpdated']+=1;session.get.side_effect=responses
        with self.assertRaises(ValueError):fetch_snapshot(session)

    def test_import_has_no_network_or_loop_side_effect(self):
        with patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            importlib.import_module('SkyblockSniper')


if __name__ == '__main__': unittest.main()
