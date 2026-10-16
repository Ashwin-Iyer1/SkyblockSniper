"""Offline-first listing inspection, inspired by csjh/SkyblockSniper (GPL-3.0)."""
import argparse
import json
import time
from pathlib import Path
from scanner import analyze, fetch_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).parent/'fixtures'/'snapshot.json')
    parser.add_argument('--live-read-only', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent/'review'/'report.json')
    parser.add_argument('--minimum-price', type=float, default=250000)
    parser.add_argument('--maximum-ratio', type=float, default=.65)
    parser.add_argument('--fee-rate', type=float, default=.02)
    parser.add_argument('--max-pages', type=int, default=100)
    args = parser.parse_args()
    try:
        if args.live_read_only:
            pages = fetch_snapshot(max_pages=args.max_pages)
            provenance = 'Explicit public API snapshot; listing prices are not completed sales'
            now = time.time()*1000
        else:
            data = json.loads(args.input.read_text(encoding='utf-8'))
            pages, provenance = data['pages'], data.get('provenance', 'User-supplied snapshot; provenance unverified')
            now = None
        report = analyze(pages, now=now, minimum_price=args.minimum_price, maximum_ratio=args.maximum_ratio, fee_rate=args.fee_rate)
        report['provenance'] = provenance
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        print(f"{len(report['candidates'])} listing outliers across {report['auctionCount']} unique auctions. {provenance}")
        print(f'Review written to {args.output}. No purchases or clipboard changes.')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    except Exception as error:
        parser.exit(1, f'Public fetch failed ({type(error).__name__}); no report was replaced.\n')


if __name__ == '__main__': main()
