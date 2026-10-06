#!/usr/bin/env python3
"""Build SVG polygon poses from an authored rig. Python 3.10+, stdlib only."""
import argparse
import copy
import json
import math
from pathlib import Path


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def validate(rig):
    points = rig.get('points', [])
    if not isinstance(points, list) or len(points) < 3:
        raise ValueError('points must contain at least three polygon vertices')
    for p in points:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError('Each vertex must contain x and y')
        finite(p[0], 'x'); finite(p[1], 'y')
    if len(set(map(tuple, points))) != len(points):
        raise ValueError('Duplicate vertices; omit the repeated closing vertex')
    period = finite(rig.get('period', 6), 'period')
    samples = rig.get('samples', 40)
    if period <= 0 or type(samples) is not int or samples < 8:
        raise ValueError('Use a positive period and an integer samples >= 8')
    tufts = rig.get('tufts', [])
    if not isinstance(tufts, list) or not tufts:
        raise ValueError('Author at least one tuft')
    movable, anchors, names = set(), set(), set()
    for tuft in tufts:
        if not isinstance(tuft, dict):
            raise ValueError('Each tuft must be an object')
        name = tuft.get('name')
        if not isinstance(name, str) or not name or name in names:
            raise ValueError('Tuft names must be nonempty and unique')
        names.add(name)
        indices = [tuft.get(k) for k in ('start', 'tip', 'end')]
        if not all(type(i) is int for i in indices):
            raise ValueError(f'{name}: start, tip and end must be integer indices')
        start, tip, end = indices
        if not 0 <= start < tip < end < len(points):
            raise ValueError(f'{name}: require 0 <= start < tip < end < vertex count')
        inside, roots = set(range(start+1, end)), {start, end}
        if inside & (movable | anchors) or roots & movable:
            raise ValueError(f'{name}: tuft interiors overlap or contain another root')
        movable.update(inside); anchors.update(roots)
        if finite(tuft.get('degrees'), 'degrees') <= 0:
            raise ValueError(f'{name}: degrees must be positive')
        finite(tuft.get('phase', 0), 'phase')
        if not 0 <= finite(tuft.get('tip_lag', .025), 'tip_lag') < .5:
            raise ValueError(f'{name}: tip_lag must be in [0, 0.5) cycles')
        a, b, p = points[start], points[end], points[tip]
        height_area = (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        if abs(height_area) < 1e-8:
            raise ValueError(f'{name}: the tip must lie off the root chord')
    return period, samples, movable


def check_crossings(points):
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

    def on_segment(a, b, p):
        return min(a[0],b[0])-1e-8 <= p[0] <= max(a[0],b[0])+1e-8 and min(a[1],b[1])-1e-8 <= p[1] <= max(a[1],b[1])+1e-8

    def intersects(a, b, c, d):
        ab_c, ab_d, cd_a, cd_b = cross(a,b,c), cross(a,b,d), cross(c,d,a), cross(c,d,b)
        if ab_c*ab_d < 0 and cd_a*cd_b < 0:
            return True
        return any(abs(area) < 1e-8 and on_segment(x,y,p) for area,x,y,p in (
            (ab_c,a,b,c), (ab_d,a,b,d), (cd_a,c,d,a), (cd_b,c,d,b)))

    extent = max(max(p[k] for p in points)-min(p[k] for p in points) for k in (0,1))
    cell_size = max(extent/math.sqrt(len(points)), 1e-4)
    segments = list(zip(points, points[1:]+points[:1]))
    cells, seen = {}, set()
    for i,(a,b) in enumerate(segments):
        for x in range(math.floor(min(a[0],b[0])/cell_size), math.floor(max(a[0],b[0])/cell_size)+1):
            for y in range(math.floor(min(a[1],b[1])/cell_size), math.floor(max(a[1],b[1])/cell_size)+1):
                for j in cells.get((x,y), []):
                    if (j,i) in seen or i-j in (1,len(points)-1):
                        continue
                    seen.add((j,i))
                    if intersects(a,b,*segments[j]):
                        raise ValueError(f'Contour segments {j} and {i} intersect; revise the rig or amplitude')
                cells.setdefault((x,y), []).append(i)


def pose(rig, t):
    rest = rig['points']
    result = [tuple(p) for p in rest]
    for tuft in rig['tufts']:
        a, b, tip = (rest[tuft[k]] for k in ('start','end','tip'))
        rx, ry = (a[0]+b[0])/2, (a[1]+b[1])/2
        nx, ny = -(b[1]-a[1]), b[0]-a[0]
        height = (tip[0]-a[0])*nx+(tip[1]-a[1])*ny
        for i in range(tuft['start']+1, tuft['end']):
            x, y = rest[i]
            weight = max(0, min(1, ((x-a[0])*nx+(y-a[1])*ny)/height))**2
            phase = math.tau*(t+tuft.get('phase',0)-tuft.get('tip_lag',.025)*weight)
            wind = (math.sin(phase)+.3*math.sin(2*phase+.4))/1.3
            angle = math.radians(tuft['degrees'])*weight*wind
            c, s = math.cos(angle), math.sin(angle)
            result[i] = (rx+(x-rx)*c-(y-ry)*s, ry+(x-rx)*s+(y-ry)*c)
    return result


def path_data(points):
    def number(x):
        text = f'{x:.4f}'.rstrip('0').rstrip('.')
        return '0' if text == '-0' else text
    return 'M'+'L'.join(f'{number(x)},{number(y)}' for x,y in points)+'Z'


def velocity_changes(frames, period):
    """Measure every boundary of a closed, uniformly timed linear pose sequence."""
    dt = period/(len(frames)-1)
    velocities = [[((b[0]-a[0])/dt,(b[1]-a[1])/dt) for a,b in zip(first,second)] for first,second in zip(frames,frames[1:])]
    jumps = [max(math.dist(a,b) for a,b in zip(velocities[i-1],velocities[i])) for i in range(len(velocities))]
    return {'loop_velocity_change':jumps[0], 'max_boundary_velocity_change':max(jumps)}


def build(rig):
    if not isinstance(rig, dict):
        raise ValueError('The rig must be a JSON object')
    period, samples, movable = validate(rig)
    rest = [tuple(p) for p in rig['points']]
    check_crossings(rest)
    frames = [[tuple(round(v,4) for v in p) for p in pose(rig,i/samples)] for i in range(samples)]
    frames.append(frames[0])
    for tuft in rig['tufts']:
        if len({frame[tuft['tip']] for frame in frames}) < 2:
            raise ValueError(f'{tuft["name"]}: tip motion vanished after rounding; increase amplitude or coordinate scale')
    for frame in frames:
        check_crossings(frame)
        for i,p in enumerate(frame):
            if i not in movable and p != tuple(round(v,4) for v in rest[i]):
                raise ValueError(f'Fixed vertex {i} moved')
    for first, second in zip(frames,frames[1:]):
        check_crossings([((a[0]+b[0])/2,(a[1]+b[1])/2) for a,b in zip(first,second)])
    return {
        'generator': 'build_fur_poses.py/v1',
        'rig': dict(rig, period=period, samples=samples),
        'rest_d': path_data(rest),
        'animation': {'attributeName':'d','dur':f'{period:g}s','repeatCount':'indefinite','calcMode':'linear','values':';'.join(map(path_data,frames))},
        'checks': {
            'stored_poses': len(frames),
            'max_displacement': max(math.dist(p,rest[i]) for frame in frames for i,p in enumerate(frame)),
            **velocity_changes(frames, period),
            'velocity_units': 'source units per second',
            'geometry_coverage': 'rest pose, stored poses and interval midpoints only',
        },
    }


def self_test():
    rig = {'points':[[0,0],[-4,20],[12,0],[12,-12],[0,-12]], 'period':6, 'samples':40,
           'tufts':[{'name':'tip','start':0,'tip':1,'end':2,'degrees':15,'phase':.2}]}
    output = build(rig)
    values = output['animation']['values'].split(';')
    assert values[0] == values[-1] and len(set(values)) > 2
    assert output['checks']['max_displacement'] > 1
    for t in (0,.2,.7,1):
        p = pose(rig,t)
        assert all(p[i] == tuple(rig['points'][i]) for i in (0,2,3,4))
    assert math.dist(pose(rig,0)[1],pose(rig,1)[1]) < 1e-10
    for change in ('overlap','nan','collinear','tiny-motion'):
        broken = copy.deepcopy(rig)
        if change == 'overlap':
            broken['tufts'].append(dict(broken['tufts'][0],name='duplicate-span'))
        elif change == 'nan':
            broken['points'][1][0] = float('nan')
        elif change == 'collinear':
            broken['points'][1] = [6,0]
        else:
            broken['tufts'][0]['degrees'] = .000001
        try:
            build(broken)
        except ValueError:
            continue
        raise AssertionError(f'Invalid {change} rig passed')
    try:
        check_crossings([(0,0),(10,10),(0,10),(10,0)])
    except ValueError:
        pass
    else:
        raise AssertionError('A crossing contour passed')
    print('OK: anchored motion, positional loop, and invalid-geometry checks')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rig',type=Path,nargs='?')
    parser.add_argument('output',type=Path,nargs='?')
    parser.add_argument('--self-test',action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test(); return
    if not args.rig or not args.output:
        parser.error('Provide rig.json and an output JSON path, or --self-test')
    if args.rig.resolve() == args.output.resolve():
        parser.error('Input rig and output must be different files')
    try:
        result = build(json.loads(args.rig.read_text(encoding='utf-8')))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['checks'],indent=2))


if __name__ == '__main__':
    main()
