"""Fixed comparison baselines for chain-efficiency review (60 fps)."""
from .engine import CHAIN_BONUS, COLOR_BONUS, _group_bonus
from .time_calc import consumption_frames

OJAMA_POINT = 70
# Standard nuisance icons in Puyo Puyo eSports (in nuisance-puyo units).
NUISANCE = (("王冠", 720), ("月", 360), ("星", 180), ("赤玉", 30), ("大玉", 6), ("小玉", 1))


def nuisance(score):
    return max(0, score // OJAMA_POINT)


def nuisance_parts(score):
    """Game-style decomposition: crown/moon/star/red/large/small."""
    rest = nuisance(score)
    parts = []
    for name, amount in NUISANCE:
        n, rest = divmod(rest, amount)
        if n:
            parts.append((name, n))
    return parts


def nuisance_label(score):
    return ' '.join(f'{name}{n}' for name,n in nuisance_parts(score)) or '0個'


def _metrics(score, erased, remaining, frames):
    consume = consumption_frames(remaining, 0, erased)
    seconds = (frames + consume) / 60
    return {'score': score, 'erased': erased, 'remaining': remaining,
            'frames': frames, 'consume_frames': consume, 'seconds': seconds,
            'efficiency': score / seconds if seconds > 0 else 0.0}


def four_clear_rows():
    """Four colored puyos erased at every step; each step falls 1 cell; 1 remains."""
    rows = []
    score = 0
    for chain in range(1, 20):
        score += 40 * max(1, CHAIN_BONUS[chain])
        rows.append({'chain': chain, **_metrics(score, 4 * chain, 1, 80 * chain)})
    return rows


def double_rows(height, quick, maximum=12):
    """First chain 4; second chain has two groups of lengths a and b.

    Remaining board is modeled as a full rectangle of height *height*.
    """
    if not isinstance(height, int) or not 0 <= height <= 12:
        raise ValueError('高さは0〜12の整数で指定してください')
    rows = []
    for a in range(4, maximum + 1):
        for b in range(a, maximum + 1):
            if 6 * height + 4 + a + b > 78:
                continue
            multiplier = max(1, CHAIN_BONUS[2] + _group_bonus(a) + _group_bonus(b))
            score = 40 + 10 * (a + b) * multiplier
            rows.append({'groups': f'{a}+{b}', 'a': a, 'b': b,
                         **_metrics(score, 4 + a + b, 6 * height, 80 + (55 if quick else 80))})
    return rows



def multi_rows(height, quick, maximum=12, group_counts=(2,3,4)):
    """2-chain double/triple/quadruple; preserve established 2-double score baseline."""
    from itertools import combinations_with_replacement
    if not isinstance(height,int) or not 0<=height<=12:
        raise ValueError('高さは0〜12の整数で指定してください')
    rows=[]
    for count in group_counts:
        if count not in (2,3,4):raise ValueError('同時消しは2〜4色のみ')
        for groups in combinations_with_replacement(range(4,maximum+1),count):
            # 13 rows x 6 columns: even before checking reachable shape,
            # the initial board must contain the first 4 + second-step groups
            # and the six-column residual height.
            if 6 * height + 4 + sum(groups) > 78:
                continue
            bonus=max(1,CHAIN_BONUS[2]+sum(_group_bonus(n) for n in groups)+(COLOR_BONUS[count] if count>2 else 0))
            score=40+10*sum(groups)*bonus
            rows.append({'kind':{2:'2ダブ',3:'2トリ',4:'2クア'}[count],
                         'groups':'+'.join(map(str,groups)),'group_count':count,
                         'sizes':groups,**_metrics(score,4+sum(groups),6*height,80+(55 if quick else 80))})
    return sorted(rows,key=lambda r:(r['efficiency'],r['score'],r['group_count'],r['sizes']))


# Ten-million-point time-attack pace, expressed in points per second.
TA_PACES = {minutes: 10_000_000 / (minutes * 60) for minutes in (120, 100, 80)}


def group_equal_metrics(rows):
    """Group exact score/efficiency matches without rounding away differences."""
    grouped = {}
    for row in rows:
        key = (row['score'], row['efficiency'])
        if key not in grouped:
            grouped[key] = dict(row, variants=[])
        grouped[key]['variants'].append((row['kind'], row['groups']))
    result = []
    for row in grouped.values():
        variants = row['variants']
        row['kind'] = ' / '.join(dict.fromkeys(kind for kind, _ in variants))
        row['groups'] = variants[0][1] + (f' ほか{len(variants)-1}通り' if len(variants)>1 else '')
        result.append(row)
    return sorted(result, key=lambda row: (row['efficiency'], row['score']))


def four_clear_at_height(chain, height):
    """4-puyo-per-link chain efficiency assuming the same residual height.

    Uses the reference table's 80 frames per step and the standard
    consumption-time correction. This is a normalized comparison, not a
    claim that every board shape can produce the chain.
    """
    if not isinstance(chain, int) or not 1 <= chain <= 19:
        raise ValueError('連鎖数は1〜19で指定してください')
    if not isinstance(height, int) or not 0 <= height <= 12:
        raise ValueError('高さは0〜12で指定してください')
    score = sum(40 * max(1, CHAIN_BONUS[n]) for n in range(1, chain + 1))
    return {'chain': chain, 'height': height,
            **_metrics(score, 4 * chain, 6 * height, 80 * chain)}
