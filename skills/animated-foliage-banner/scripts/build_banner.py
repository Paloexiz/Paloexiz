"""Generate contour motion in an authored SVG (Python 3.10+, stdlib)."""
import argparse
import json
import math
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET
from build_fur_poses import check_crossings, finite, path_data, validate, velocity_changes

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


class SceneBuilder(ET.TreeBuilder):
    """Retain author notes inside and outside the SVG root."""
    def __init__(self):
        super().__init__(insert_comments=True, insert_pis=True)
        self.depth = 0
        self.started = False
        self.before, self.after = [], []

    def start(self, tag, attrs):
        self.depth += 1
        self.started = True
        return super().start(tag, attrs)

    def end(self, tag):
        node = super().end(tag)
        self.depth -= 1
        return node

    def outside(self, node):
        if self.depth == 0:
            (self.after if self.started else self.before).append(node)
        return node

    def comment(self, text):
        return self.outside(super().comment(text))

    def pi(self, target, text):
        return self.outside(super().pi(target, text))

    def doctype(self, name, pubid, system):
        raise ValueError('DTD-bearing SVGs are unsupported; input has not been modified')


def curve(controls, t):
    """Periodic uniform Catmull-Rom; matching tangents at every control and the seam."""
    q = (t % 1) * len(controls)
    i = math.floor(q)
    u = q - i
    a, b, c, d = (controls[j % len(controls)] for j in (i-1, i, i+1, i+2))
    return [tuple(.5*(2*y+(-x+z)*u+(2*x-5*y+4*z-w)*u*u+(-x+3*y-3*z+w)*u*u*u)
                  for x, y, z, w in zip(*p)) for p in zip(a, b, c, d)]


def pose_path(frame, rest_coordinates, moving):
    """Keep untracked source coordinates exact; round only authored motion."""
    def source_pair(pair):
        parts = (part.rstrip('0').rstrip('.') if '.' in part else part for part in pair.split(','))
        return ','.join('0' if part in ('', '-', '-0') else part for part in parts)
    return 'M' + 'L'.join(path_data([p])[1:-1] if i in moving else source_pair(rest_coordinates[i])
                         for i, p in enumerate(frame)) + 'Z'


def build(source, motion_path=None):
    builder = SceneBuilder()
    root = ET.parse(source if motion_path else source / 'scene.svg',
                    parser=ET.XMLParser(target=builder)).getroot()
    motion = json.loads((motion_path or source / 'motion.json').read_text(encoding='utf-8'))
    outline = root.find('.//*[@id="fur-outline"]')
    data = json.loads(root.find('.//*[@id="fur-motion-data"]').text)
    d = outline.get('d')
    if not re.fullmatch(r'M[\d.,L-]+Z', d):
        raise ValueError('The authored contour must use M/L/Z polygon commands')
    rest = [tuple(map(float, p)) for p in re.findall(r'(-?[\d.]+),(-?[\d.]+)', d)]
    rest_coordinates = d[1:-1].split('L')
    period, samples, movable = validate(dict(data, points=rest, samples=motion['intervals']))
    indices, controls = motion['vertices'], motion['poses']
    if not isinstance(indices, list) or not indices or any(type(i) is not int or i not in movable for i in indices) or len(set(indices)) != len(indices):
        raise ValueError('Motion vertices must be unique authored tuft interiors')
    if not all(t['tip'] in indices for t in data['tufts']):
        raise ValueError('Every tuft tip needs an authored motion track')
    moving = set(indices)
    if not isinstance(controls, list) or len(controls) < 4:
        raise ValueError('At least four equally spaced periodic control poses are required; omit the repeated last pose')
    for frame in controls:
        if not isinstance(frame, list) or len(frame) != len(indices):
            raise ValueError('Control-pose topology changed')
        for p in frame:
            if not isinstance(p, list) or len(p) != 2:
                raise ValueError('Each motion vertex must contain x and y')
            finite(p[0], 'x'); finite(p[1], 'y')
    animations = outline.findall(f'{{{NS}}}animate')
    if animations and not motion_path:
        raise ValueError('Use an SVG input with --motion to refresh existing fur poses')
    if len(animations) > 1 or any(a.get('attributeName') != 'd' for a in animations):
        raise ValueError('Expected at most one contour d animation')
    check_crossings(rest)
    frames = []
    for i in range(samples):
        frame = list(rest)
        for index, p in zip(indices, curve(controls, i/samples)):
            frame[index] = tuple(round(v, 4) for v in p)
        frames.append(frame)
    frames.append(frames[0])
    for tuft in data['tufts']:
        if len({f[tuft['tip']] for f in frames}) < 2:
            raise ValueError(f'{tuft["name"]}: static motion track')
    for frame in frames:
        check_crossings(frame)
    for a, b in zip(frames, frames[1:]):
        check_crossings([((p[0]+q[0])/2, (p[1]+q[1])/2) for p, q in zip(a, b)])
    animation = animations[0] if animations else ET.SubElement(outline, f'{{{NS}}}animate')
    if not animation.get('id'):
        existing_ids = {element.get('id') for element in root.iter()}
        animation_id, suffix = 'fur-sway', 0
        while animation_id in existing_ids:
            suffix += 1
            animation_id = f'fur-sway-{suffix}'
        animation.set('id', animation_id)
    animation.attrib.update({
        'attributeName':'d', 'dur':f'{period:g}s',
        'repeatCount':'indefinite', 'calcMode':'linear',
        'values':';'.join(pose_path(frame, rest_coordinates, moving) for frame in frames)})
    payload = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    declaration, body = payload.split(b'\n', 1)
    payload = b'\n'.join([declaration, *(ET.tostring(node, encoding='utf-8') for node in builder.before),
                          body, *(ET.tostring(node, encoding='utf-8') for node in builder.after)])
    stats = dict(velocity_changes(frames, period), stored_poses=len(frames), bytes=len(payload),
                 max_displacement=max(math.dist(p, r) for frame in frames for p, r in zip(frame, rest)))
    return payload, stats


def self_test():
    from io import BytesIO
    from unittest.mock import patch

    assert pose_path([(220.00001, 80), (260.123456, 20)], ['220.00001,80', '260,20'], {1}) == 'M220.00001,80L260.1235,20Z'
    assert pose_path([(220, 80)], ['220.000,80.0'], set()) == 'M220,80Z'
    assert pose_path([(0, 0)], ['-.000,0.0'], set()) == 'M0,0Z'
    controls = [[(x, y)] for x, y in ((0, 0), (1, 2), (3, 0), (1, -2))]
    for i, p in enumerate(controls):
        assert curve(controls, i/4) == p
    assert curve(controls, 0) == curve(controls, 1)
    h = 1e-7
    for t in (0, .25, .5, .75):
        p, before, after = curve(controls, t)[0], curve(controls, t-h)[0], curve(controls, t+h)[0]
        left = tuple((a-b)/h for a, b in zip(p, before))
        right = tuple((a-b)/h for a, b in zip(after, p))
        assert math.dist(left, right) < 1e-4
    example = Path(__file__).resolve().parent.parent / 'examples' / 'minimal'
    for occupied, expected in (((), 'fur-sway'), (('fur-sway',), 'fur-sway-1'),
                               (('fur-sway', 'fur-sway-1'), 'fur-sway-2')):
        scene = ET.parse(example / 'scene.svg')
        for identifier in occupied:
            ET.SubElement(scene.getroot(), f'{{{NS}}}g', {'id': identifier})
        with patch.object(ET, 'parse', return_value=scene):
            payload, _ = build(example)
        result = ET.fromstring(payload)
        ids = [element.get('id') for element in result.iter() if element.get('id')]
        assert len(ids) == len(set(ids)), 'Generated animation collides with a source ID'
        assert result.find(f'.//*[@id="fur-outline"]/{{{NS}}}animate').get('id') == expected
        assert all(result.find(f'.//*[@id="{identifier}"]').tag == f'{{{NS}}}g' for identifier in occupied)
        with patch.object(ET, 'parse', return_value=ET.ElementTree(result)):
            refreshed, _ = build(Path('renamed.svg'), example / 'motion.json')
        assert refreshed == payload, 'Refreshing the generated SVG changed its content or animation ID'
    result.find(f'.//*[@id="fur-outline"]/{{{NS}}}animate').set('attributeName', 'opacity')
    with patch.object(ET, 'parse', return_value=ET.ElementTree(result)):
        try:
            build(Path('renamed.svg'), example / 'motion.json')
        except ValueError:
            pass
        else:
            raise AssertionError('Unrelated animation was overwritten')
    notes = [b'<!-- document note -->', b'<?editor editable="yes"?>',
             b'<!-- layer note -->', b'<?inside hint="kept"?>', b'<!-- trailing note -->']
    annotated = b'\n'.join(notes[:2]) + payload.replace(b'</svg>', b''.join(notes[2:4])+b'</svg>') + notes[4]
    annotated = annotated.replace(b"<?xml version='1.0' encoding='utf-8'?>\n", b'')
    refreshed, _ = build(BytesIO(annotated), example / 'motion.json')
    assert all(note in refreshed for note in notes), 'Author comments or processing instructions were lost'
    assert build(BytesIO(refreshed), example / 'motion.json')[0] == refreshed
    try:
        build(BytesIO(b'<!DOCTYPE svg []>' + annotated), example / 'motion.json')
    except ValueError:
        pass
    else:
        raise AssertionError('Unsupported DTD was silently discarded')
    print('OK: precision, periodic tangents, unique IDs, repeatable refresh, author notes, unsupported-animation/DTD rejection')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, nargs='?')
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--motion', type=Path, help='Motion controls for an SVG input; output may be the same SVG')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test(); return
    if not args.source or not args.output:
        parser.error('Provide source and output paths, or --self-test')
    if not args.motion and args.output.resolve().is_relative_to(args.source.resolve()):
        parser.error('Write the output outside the source directory')
    if args.motion and args.output.resolve() == args.motion.resolve():
        parser.error('Output must not overwrite motion controls')
    temporary = None
    try:
        payload, stats = build(args.source, args.motion)
        output = args.output.resolve()
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=f'.{output.name}.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        temporary.replace(output)
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError) as exc:
        parser.error(str(exc))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()
