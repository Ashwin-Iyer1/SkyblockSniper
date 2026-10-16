"""Deterministic BIN listing comparison. No purchases, clipboard writes or notifications."""
from collections import Counter, defaultdict
import hashlib
import math
import re
from statistics import median


def clean_text(value):
    return re.sub(r'\s+', ' ', re.sub(r'§.', '', str(value))).strip()


def identity(auction):
    """Conservative display fingerprint; preserve levels, reforges, stars and lore."""
    name = clean_text(auction.get('item_name', ''))
    tier = clean_text(auction.get('tier', ''))
    lore = clean_text(auction.get('item_lore', ''))
    if not name or not tier or not lore:
        raise ValueError('Name, tier and lore are required for comparison')
    return (name, tier, hashlib.sha256(lore.encode('utf-8')).hexdigest())


def combine_pages(pages):
    if not pages or not isinstance(pages, list):
        raise ValueError('A nonempty list of API pages is required')
    first = pages[0]
    total, timestamp = first.get('totalPages'), first.get('lastUpdated')
    if not isinstance(total, int) or not 1 <= total <= 1000 or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):
        raise ValueError('Invalid snapshot metadata')
    if len(pages) != total or {p.get('page') for p in pages} != set(range(total)):
        raise ValueError('Snapshot has missing or duplicate pages')
    auctions, seen = [], {}
    for page in pages:
        if page.get('success') is not True or page.get('lastUpdated') != timestamp or page.get('totalPages') != total:
            raise ValueError('Snapshot changed during pagination; discard and retry')
        if not isinstance(page.get('auctions'), list):
            raise ValueError('Missing auction records')
        for auction in page['auctions']:
            uid = auction.get('uuid')
            if not isinstance(uid, str) or not uid:
                raise ValueError('Every auction must have a UUID')
            if uid in seen and seen[uid] != auction:
                raise ValueError('Conflicting duplicate auction UUID')
            if uid not in seen:
                auctions.append(auction)
                seen[uid] = auction
    return timestamp, auctions


def analyze(pages, *, now=None, minimum_price=250000, maximum_ratio=.65, minimum_comparables=2, fee_rate=.02, max_snapshot_age=120, max_listing_age=300):
    if not math.isfinite(minimum_price) or minimum_price < 0 or not 0 < maximum_ratio < 1 or not 0 <= fee_rate < 1:
        raise ValueError('Invalid price, ratio or fee configuration')
    if not isinstance(minimum_comparables, int) or minimum_comparables < 2:
        raise ValueError('At least two comparable listings are required')
    if not math.isfinite(max_listing_age) or max_listing_age < 0 or not math.isfinite(max_snapshot_age) or max_snapshot_age < 0:
        raise ValueError('Age limits must be nonnegative and finite')
    timestamp, auctions = combine_pages(pages)
    now = timestamp if now is None else now
    if not isinstance(now, (int, float)) or not math.isfinite(now) or now < timestamp or now - timestamp > max_snapshot_age * 1000:
        raise ValueError('Snapshot is stale or dated in the future')
    groups, excluded = defaultdict(list), Counter()
    for auction in auctions:
        if auction.get('bin') is not True or auction.get('claimed') is not False:
            excluded['not_active_bin'] += 1
            continue
        price, start, end = auction.get('starting_bid'), auction.get('start'), auction.get('end')
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in [price, start, end]) or price <= 0 or start > now or end <= now:
            excluded['invalid_or_expired'] += 1
            continue
        try:
            key = identity(auction)
        except ValueError:
            excluded['missing_identity'] += 1
            continue
        groups[key].append(auction)
    candidates = []
    for key, listings in groups.items():
        ordered = sorted(listings, key=lambda a: (a['starting_bid'], a['uuid']))
        candidate, peers = ordered[0], ordered[1:]
        if len(peers) < minimum_comparables:
            excluded['insufficient_comparable_groups'] += 1
            continue
        if candidate['starting_bid'] < minimum_price or now - candidate['start'] > max_listing_age * 1000:
            continue
        second = peers[0]['starting_bid']
        ratio = candidate['starting_bid'] / second
        if ratio >= maximum_ratio:
            continue
        baseline = median(a['starting_bid'] for a in peers)
        # Listing prices are not sales evidence; this is only a conditional scenario.
        resale = second
        candidates.append({'uuid': candidate['uuid'], 'name': key[0], 'tier': key[1], 'fingerprint': key[2],
                           'price': candidate['starting_bid'], 'nextListing': second, 'peerMedian': baseline,
                           'peerCount': len(peers), 'ratioToNext': ratio, 'listingAgeSeconds': (now-candidate['start'])/1000,
                           'conditionalNet': resale*(1-fee_rate)-candidate['starting_bid'],
                           'peers': [{'uuid': a['uuid'], 'price': a['starting_bid']} for a in peers]})
    return {'schemaVersion': 1, 'snapshotTime': timestamp, 'evaluatedAt': now, 'auctionCount': len(auctions),
            'groupCount': len(groups), 'excluded': dict(sorted(excluded.items())),
            'parameters': {'minimumPrice': minimum_price, 'maximumRatio': maximum_ratio, 'minimumComparables': minimum_comparables,
                           'feeRate': fee_rate, 'maxListingAgeSeconds': max_listing_age},
            'candidates': sorted(candidates, key=lambda c: (-c['conditionalNet'], c['uuid']))}


def fetch_snapshot(session=None, *, max_pages=100, timeout=15):
    """Explicit bounded public reads; abort mixed snapshots instead of analyzing them."""
    if session is None:
        import requests
        with requests.Session() as client:
            return fetch_snapshot(client, max_pages=max_pages, timeout=timeout)
    def fetch(page):
        response = session.get('https://api.hypixel.net/v2/skyblock/auctions', params={'page': page}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    first = fetch(0)
    total = first.get('totalPages')
    if not isinstance(total, int) or not 1 <= total <= max_pages:
        raise ValueError('Page count exceeds the configured request bound')
    pages = [first]
    for page in range(1, total):
        data = fetch(page)
        if data.get('lastUpdated') != first.get('lastUpdated'):
            raise ValueError('Snapshot rolled over while fetching; rerun a fresh scan')
        pages.append(data)
    combine_pages(pages)
    return pages
