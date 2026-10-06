"""Check the documented foliage scene contract, not arbitrary SVG. Requires Pillow."""
import argparse
import base64
import io
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image
from build_fur_poses import check_crossings, validate, velocity_changes

NS = {'s': 'http://www.w3.org/2000/svg'}


def points(d):
    assert re.fullmatch(r'M[\d.,L-]+Z', d), 'Unexpected path commands'
    return [tuple(map(float, pair)) for pair in re.findall(r'(-?[\d.]+),(-?[\d.]+)', d)]


def check(path, quiet=False):
    root = ET.parse(path).getroot()
    data = json.loads(root.find('.//*[@id="fur-motion-data"]').text)
    outline = root.find('.//*[@id="fur-outline"]')
    rest = points(outline.get('d'))
    animation = outline.find('s:animate', NS)
    assert animation is not None, 'Missing contour animation'
    assert animation.get('calcMode') == 'linear', 'Fur interpolation must be linear'
    assert animation.get('attributeName') == 'd', 'Fur animation must target the contour'
    frames = [points(d) for d in animation.get('values').split(';')]
    period, _, movable = validate(dict(data, points=rest, samples=len(frames)-1))
    assert animation.get('repeatCount') == 'indefinite'
    assert animation.get('dur') == f'{period:g}s', 'Duration differs from the rig'
    assert animation.get('keyTimes') is None, 'Expected uniformly spaced poses'
    assert frames[0] == frames[-1], 'Cycle has a seam'
    check_crossings(rest)
    for frame in frames:
        assert len(frame) == len(rest), 'Path topology changed'
        check_crossings(frame)
        assert all(p == rest[i] for i, p in enumerate(frame) if i not in movable), 'A fixed contour point moved'
    for first, second in zip(frames, frames[1:]):
        check_crossings([((a[0]+b[0])/2, (a[1]+b[1])/2) for a, b in zip(first, second)])
    for tuft in data['tufts']:
        assert len({frame[tuft['tip']] for frame in frames}) > 1, f'{tuft["name"]}: static tip'
    still = root.find('.//*[@id="fur-still"]')
    assert still is not None and len(still) == 0 and points(still.get('d')) == rest, 'Invalid rest contour'

    style = root.find('s:style', NS)
    css = re.sub(r'/\*.*?\*/', '', style.text or '', flags=re.S) if style is not None else ''
    for selector, name in (('branch', 'branch-wind'), ('leaf', 'leaf-flutter')):
        rule = re.search(r'\.' + selector + r'\s*\{([^}]*)\}', css)
        assert rule and re.search(r'animation\s*:\s*' + name + r'\b[^;{}]*\binfinite\s*;', rule[1]), f'Missing leaf animation: .{selector}'
        assert re.search(r'transform-origin\s*:\s*0\s+0\s*;', rule[1]), f'Leaf origin changed: .{selector}'
        assert re.search(r'@keyframes\s+' + name + r'\s*\{', css), f'Missing keyframes: {name}'
    branches = root.findall('.//s:g[@class="branch"]', NS)
    leaves = root.findall('.//s:g[@class="leaf"]', NS)
    assert branches and len(branches) == len(leaves) and all(len(b.findall('s:g[@class="leaf"]', NS)) == 1 for b in branches), 'Expected one leaf per branch'

    pairs = 0
    for parent in root.iter():
        dynamic = parent.findall('s:use[@class="motion-contour"]', NS)
        static = parent.findall('s:use[@class="still-contour"]', NS)
        if dynamic or static:
            assert len(dynamic) == len(static) == 1, 'Incomplete contour pair'
            assert dynamic[0].get('href') == '#fur-outline' and static[0].get('href') == '#fur-still', 'Contour pair references differ'
            attributes = lambda element: {k: v for k, v in element.attrib.items() if k not in ('id', 'class', 'href')}
            assert attributes(dynamic[0]) == attributes(static[0]), 'Contour pair presentation differs'
            pairs += 1
    assert pairs, 'No contour pairs'
    assert not root.findall('.//s:script', NS)
    ids = [e.get('id') for e in root.iter() if e.get('id')]
    assert len(ids) == len(set(ids)), 'Duplicate IDs'
    for element in root.iter():
        for key, value in element.attrib.items():
            if key.rsplit('}', 1)[-1] == 'href':
                assert value.startswith('#') or value.startswith('data:image/'), 'External resource'
                if value.startswith('#'):
                    assert value[1:] in ids, 'Unresolved reference'
    images = root.findall('.//s:image', NS)
    for element in images:
        href = element.get('href') or element.get('{http://www.w3.org/1999/xlink}href')
        assert href and re.match(r'data:image/(png|jpeg|webp);base64,', href), 'Use embedded PNG/JPEG/WebP images'
        with Image.open(io.BytesIO(base64.b64decode(href.split(',', 1)[1], validate=True))) as image:
            image.load()
    velocity = velocity_changes(frames, period)
    if not quiet:
        print(json.dumps(dict(tufts=len(data['tufts']), poses=len(frames), leaves=len(leaves), contour_pairs=pairs,
                              embedded_images=len(images), max_displacement=max(math.dist(p, r) for f in frames for p, r in zip(f, rest)),
                              **velocity), indent=2))


def self_test(path):
    original = path.read_bytes()
    check(io.BytesIO(original))
    for mutation, message in (('empty-style', 'Missing leaf animation'), ('discrete', 'Fur interpolation'), ('static-tip', 'static tip')):
        root = ET.fromstring(original)
        if mutation == 'empty-style':
            root.find('s:style', NS).text = ''
        elif mutation == 'discrete':
            root.find('.//*[@id="fur-outline"]/s:animate', NS).set('calcMode', 'discrete')
        else:
            outline = root.find('.//*[@id="fur-outline"]')
            animation = outline.find('s:animate', NS)
            animation.set('values', ';'.join([outline.get('d')] * len(animation.get('values').split(';'))))
        try:
            check(io.BytesIO(ET.tostring(root)), quiet=True)
        except AssertionError as exc:
            assert message in str(exc), f'{mutation} failed for an unrelated reason: {exc}'
            print(f'OK: rejected {mutation}: {exc}')
        else:
            raise AssertionError(f'{mutation} unexpectedly passed')
    assert path.read_bytes() == original, 'Regression check changed the input SVG'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svg', type=Path)
    parser.add_argument('--self-test', action='store_true', help='Also reject in-memory motion regressions')
    args = parser.parse_args()
    self_test(args.svg) if args.self_test else check(args.svg)
