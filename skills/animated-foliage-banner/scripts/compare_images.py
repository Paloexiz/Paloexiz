"""Compare equal-sized rasters without resizing (Python 3.10+, Pillow)."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


def compare(before, after, region=None, tolerance=0):
    if before.size != after.size:
        raise ValueError('Image dimensions differ; align them explicitly before comparison')
    if not 0 <= tolerance <= 255:
        raise ValueError('Tolerance must be between 0 and 255')
    x, y, width, height = region or (0, 0, *before.size)
    if min(x, y) < 0 or min(width, height) <= 0 or x+width > before.width or y+height > before.height:
        raise ValueError('Region must fit entirely inside both images')
    box = (x, y, x+width, y+height)
    a, b = (image.convert('RGBA').crop(box) for image in (before, after))
    diff = ImageChops.difference(a, b)
    maximum = diff.getchannel('R')
    for channel in ('G', 'B', 'A'):
        maximum = ImageChops.lighter(maximum, diff.getchannel(channel))
    histogram = maximum.histogram()
    changed = maximum.point(lambda value: 255 if value > tolerance else 0)
    bounds = changed.getbbox()
    count = sum(histogram[tolerance+1:])
    report = {
        'size': list(before.size), 'region': [x, y, width, height], 'tolerance': tolerance,
        'changed_pixels': count, 'changed_fraction': count/(width*height),
        'changed_bbox': [bounds[0]+x, bounds[1]+y, bounds[2]+x, bounds[3]+y] if bounds else None,
        'max_channel_delta': maximum.getextrema()[1],
        'mean_absolute_rgba_delta': sum(ImageStat.Stat(diff).mean)/4,
    }
    # Keep alpha-only differences visible instead of making the diff transparent.
    return report, (a, b, maximum.convert('RGB'))


def self_test():
    a = Image.new('RGBA', (5, 4), (10, 20, 30, 255)); b = a.copy()
    b.putpixel((3, 2), (10, 20, 30, 250))
    result, _ = compare(a, b, (2, 1, 3, 3))
    assert result['changed_pixels'] == 1 and result['changed_bbox'] == [3, 2, 4, 3]
    assert result['max_channel_delta'] == 5
    assert compare(a, b, tolerance=5)[0]['changed_pixels'] == 0
    assert compare(a, a)[0]['changed_pixels'] == 0
    for other, region in ((Image.new('RGB', (1, 1)), None), (a, (-1, 0, 2, 2))):
        try:
            compare(a, other, region)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid comparison accepted')
    print('OK: alpha-only differences, crop coordinates, tolerance, identity, invalid inputs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path, nargs='?')
    parser.add_argument('after', type=Path, nargs='?')
    parser.add_argument('--region', type=int, nargs=4, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'))
    parser.add_argument('--tolerance', type=int, default=0)
    parser.add_argument('--output-dir', type=Path, help='New directory for JSON, paired crops, and a maximum-channel diff')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test(); return
    if not args.before or not args.after:
        parser.error('Provide before and after image paths')
    try:
        with Image.open(args.before) as before, Image.open(args.after) as after:
            report, images = compare(before, after, args.region, args.tolerance)
        report['sha256'] = {name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for name, p in [('before', args.before), ('after', args.after)]}
        output = json.dumps(report, indent=2) + '\n'
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=False)
            for name, image in zip(('before', 'after', 'diff'), images):
                image.save(args.output_dir / f'{name}.png')
            (args.output_dir / 'comparison.json').write_text(output, encoding='utf-8')
        print(output, end='')
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
