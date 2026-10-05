from __future__ import annotations
import argparse, csv, hashlib, json, math, platform, random, statistics, time
from pathlib import Path

SEED = 20261004

def percentile(xs, q):
    if not xs:
        return None
    ys = sorted(float(x) for x in xs)
    if len(ys) == 1:
        return ys[0]
    pos = (len(ys)-1)*q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ys[lo]
    return ys[lo]*(hi-pos) + ys[hi]*(pos-lo)

def iqr(xs):
    if not xs:
        return (None, None)
    return percentile(xs, .25), percentile(xs, .75)

def safe_median(xs):
    return statistics.median(xs) if xs else None

def bootstrap_ci_median(xs, nboot=4000, alpha=.05):
    if not xs:
        return (None, None)
    vals = [float(x) for x in xs]
    r = random.Random(SEED + len(vals) + int(sum(vals)) % 100000)
    boots = []
    for _ in range(nboot):
        sample = [vals[r.randrange(len(vals))] for _ in vals]
        boots.append(statistics.median(sample))
    return percentile(boots, alpha/2), percentile(boots, 1-alpha/2)

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def load_runs(root: Path):
    rows = []
    for p in sorted(root.glob('target_*/run_*/summary.json')):
        doc = json.loads(p.read_text(encoding='utf-8'))
        runs = doc.get('runs', [])
        if len(runs) != 1:
            continue
        r = dict(runs[0])
        r['evidence_file'] = str(p.relative_to(root))
        rows.append(r)
    return rows

def main():
    ap = argparse.ArgumentParser(description='Aggregate STREAM-SURE Phase 6B replicated E16 trials')
    ap.add_argument('--root', required=True)
    ap.add_argument('--expected-repetitions', type=int, default=30)
    args = ap.parse_args()
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    rows = load_runs(root)
    if not rows:
        raise SystemExit('No Phase 6B run summaries found')

    targets = sorted({int(r['target_input_events_per_sec']) for r in rows})
    raw = root/'replicate_runs.csv'
    fields = [
        'target_input_events_per_sec','run_id','sustained','completion_ratio',
        'actual_input_events_per_sec','certificate_throughput_per_sec',
        'latency_p50_ms','latency_p95_ms','latency_p99_ms','latency_max_ms',
        'producer_elapsed_sec','end_to_end_elapsed_sec','delivery_errors',
        'consumer_errors','certificates_received','decisions_target','evidence_file'
    ]
    with raw.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})

    summaries = []
    for t in targets:
        rr = [r for r in rows if int(r['target_input_events_per_sec']) == t]
        def vals(k):
            return [float(r[k]) for r in rr if r.get(k) is not None]

        p95 = vals('latency_p95_ms')
        p99 = vals('latency_p99_ms')
        thr = vals('certificate_throughput_per_sec')
        comp = vals('completion_ratio')
        actual = vals('actual_input_events_per_sec')
        p95_q1, p95_q3 = iqr(p95)
        thr_q1, thr_q3 = iqr(thr)
        p95_lo, p95_hi = bootstrap_ci_median(p95)
        thr_lo, thr_hi = bootstrap_ci_median(thr)
        sustained_count = sum(bool(r.get('sustained')) for r in rr)
        zero_certificate_runs = sum(int(r.get('certificates_received') or 0) == 0 for r in rr)
        incomplete_runs = sum(float(r.get('completion_ratio') or 0.0) < 0.99 for r in rr)
        missing_latency_runs = len(rr) - len(p95)

        summaries.append({
            'target_input_events_per_sec': t,
            'n': len(rr),
            'sustained_count': sustained_count,
            'sustained_rate': sustained_count/len(rr) if rr else None,
            'incomplete_runs': incomplete_runs,
            'zero_certificate_runs': zero_certificate_runs,
            'latency_observed_runs': len(p95),
            'latency_missing_runs': missing_latency_runs,
            'completion_ratio_median': safe_median(comp),
            'completion_ratio_min': min(comp) if comp else None,
            'actual_input_eps_median': safe_median(actual),
            'certificate_throughput_median': safe_median(thr),
            'certificate_throughput_q1': thr_q1,
            'certificate_throughput_q3': thr_q3,
            'certificate_throughput_median_ci95_low': thr_lo,
            'certificate_throughput_median_ci95_high': thr_hi,
            'latency_p95_median_ms': safe_median(p95),
            'latency_p95_q1_ms': p95_q1,
            'latency_p95_q3_ms': p95_q3,
            'latency_p95_median_ci95_low_ms': p95_lo,
            'latency_p95_median_ci95_high_ms': p95_hi,
            'latency_p99_median_ms': safe_median(p99),
            'delivery_errors_total': sum(int(r.get('delivery_errors',0)) for r in rr),
            'consumer_errors_total': sum(int(r.get('consumer_errors',0)) for r in rr),
        })

    agg = root/'aggregate_reproducibility.csv'
    with agg.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        w.writeheader()
        w.writerows(summaries)

    complete = all(s['n'] == args.expected_repetitions for s in summaries)
    evidence_ok = all(s['delivery_errors_total'] == 0 and s['consumer_errors_total'] == 0 for s in summaries)
    missing_latency_total = sum(s['latency_missing_runs'] for s in summaries)
    zero_certificate_total = sum(s['zero_certificate_runs'] for s in summaries)
    result = {
        'phase': 'E16-Phase6B',
        'generated_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'expected_repetitions_per_target': args.expected_repetitions,
        'targets': targets,
        'total_runs': len(rows),
        'replication_complete': complete,
        'transport_error_free': evidence_ok,
        'runs_with_missing_latency': missing_latency_total,
        'zero_certificate_runs': zero_certificate_total,
        'summary': summaries,
        'environment': {'python': platform.python_version(), 'platform': platform.platform()},
        'statistical_note': (
            'Medians and IQR are computed across independent run summaries. Median 95% CIs use '
            'deterministic nonparametric bootstrap (4000 resamples; seed fixed for reproducibility). '
            'Latency statistics exclude runs with zero completed certificates; those runs are retained '
            'in completion/sustained statistics and explicitly counted as missing-latency observations.'
        ),
        'publication_note': (
            'Do not call a target real-time solely because sustained_rate=1.0. Report latency distribution, '
            'completion, throughput, sustained rate, and zero-certificate/incomplete runs together. A run with '
            'zero certificates is a valid failed observation and must not be silently dropped.'
        )
    }
    (root/'reproducibility_summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

    manifest = {}
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name != 'SHA256SUMS.json':
            manifest[str(p.relative_to(root))] = sha256(p)
    (root/'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    print(json.dumps({
        'targets': targets,
        'total_runs': len(rows),
        'replication_complete': complete,
        'transport_error_free': evidence_ok,
        'runs_with_missing_latency': missing_latency_total,
        'zero_certificate_runs': zero_certificate_total,
        'evidence_root': str(root)
    }, indent=2))
    print('PHASE6B_EVIDENCE_AGGREGATION=PASS')

if __name__ == '__main__':
    main()
