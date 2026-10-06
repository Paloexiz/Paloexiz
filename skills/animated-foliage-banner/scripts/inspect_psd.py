"""Read PSD metadata and optional cached pixels without compositing or saving the source."""
import argparse
from enum import Enum
import hashlib
import importlib.metadata
import json
from pathlib import Path
import tempfile


def plain(value):
    if isinstance(value, Enum):
        return value.name
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode('ascii', errors='backslashreplace')
    if hasattr(value, 'items'):
        return {str(plain(key)): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if hasattr(value, 'value'):
        return plain(value.value)
    return str(value)


def inspect(source, output, preview=False, pixel_indices=(), mask_indices=()):
    from psd_tools import PSDImage
    from psd_tools.constants import Resource

    before = hashlib.sha256(source.read_bytes()).hexdigest()
    psd = PSDImage.open(source)
    layers = []

    def visit(group, parent=None):
        for layer in group:
            index = len(layers)
            layers.append((layer, parent))
            if layer.is_group():
                visit(layer, index)

    visit(psd)
    if any(index < 0 or index >= len(layers) for index in (*pixel_indices, *mask_indices)):
        raise ValueError('Layer index is outside the preorder layer inventory')
    output.mkdir(parents=True, exist_ok=False)
    report = {
        'source_sha256': before, 'source_bytes': source.stat().st_size,
        'psd_tools': importlib.metadata.version('psd-tools'),
        'canvas': [psd.width, psd.height], 'color_mode': plain(psd.color_mode), 'depth': psd.depth,
        'source_icc_present': Resource.ICC_PROFILE in psd.image_resources,
        'icc_conversion_applied': False,
        'layers': [], 'exports': [], 'warnings': [],
    }
    fields = ('enabled', 'present', 'opacity', 'blend_mode', 'color', 'angle',
              'use_global_light', 'distance', 'size', 'choke', 'noise',
              'anti_aliased', 'layer_knocks_out', 'contour')
    for index, (layer, parent) in enumerate(layers):
        item = {'index': index, 'parent': parent, 'name': layer.name, 'kind': layer.kind,
                'bbox': list(layer.bbox), 'visible': layer.visible,
                'effective_visible': layer.is_visible(), 'opacity_255': layer.opacity,
                'blend_mode': plain(layer.blend_mode), 'clipping': layer.clipping,
                'effects_enabled': layer.effects.enabled, 'effects': []}
        for effect in layer.effects:
            entry = {'type': type(effect).__name__}
            for field in fields:
                try:
                    entry[field] = plain(getattr(effect, field))
                except AttributeError:
                    continue
            item['effects'].append(entry)
        if layer.kind == 'type':
            item['text'] = layer.text
            item['transform'] = list(layer.transform)
        if layer.mask:
            item['mask'] = {'bbox': list(layer.mask.bbox), 'background_color': layer.mask.background_color,
                            'disabled': layer.mask.disabled, 'has_real': layer.mask.has_real(),
                            'export_channel': 'combined' if layer.mask.has_real() else 'user'}
        report['layers'].append(item)

    def export(image, name, kind, index=None):
        if image is None:
            report['warnings'].append(f'{kind}: cached pixels unavailable for layer {index}')
            return
        if image.mode not in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA', 'I;16', 'I;16B'):
            report['warnings'].append(f'{kind}: PNG export skipped for mode {image.mode}, layer {index}; no color conversion applied')
            return
        image.save(output / name)
        report['exports'].append({'file': name, 'kind': kind, 'index': index,
                                  'size': list(image.size), 'mode': image.mode})

    if preview:
        export(psd.topil(apply_icc=False), 'merged-preview.png', 'cached-merged-preview')
    for index in sorted(set(pixel_indices)):
        export(layers[index][0].topil(apply_icc=False), f'layer-{index:03d}.png', 'raw-layer-pixels', index)
    for index in sorted(set(mask_indices)):
        mask = layers[index][0].mask
        export(mask.topil(real=True) if mask else None, f'mask-{index:03d}.png', 'stored-mask', index)
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError('Source changed during inspection; discard this inconsistent report')
    report['source_unchanged'] = True
    (output / 'psd-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def self_test():
    import struct
    from PIL import Image, ImageCms
    from psd_tools import PSDImage
    from psd_tools.api.layers import Group, PixelLayer
    from psd_tools.constants import Resource
    from psd_tools.psd.image_resources import ImageResource

    with tempfile.TemporaryDirectory(prefix='psd-test-') as directory:
        folder = Path(directory); source = folder / 'neutral.psd'
        psd = PSDImage.new('RGB', (12, 9), color=(50, 90, 130))
        group = Group.new(psd, name='Hidden group'); group.visible = False
        PixelLayer.frompil(Image.new('RGBA', (3, 4), (200, 50, 20, 255)), group, 'Accent', top=2, left=1)
        psd.save(source)
        original = source.read_bytes()
        report = inspect(source, folder / 'inspection', preview=True, pixel_indices=[1])
        assert source.read_bytes() == original and report['source_unchanged']
        assert report['canvas'] == [12, 9] and report['layers'][1]['parent'] == 0
        assert report['layers'][1]['bbox'] == [1, 2, 4, 6]
        assert report['layers'][1]['visible'] and not report['layers'][1]['effective_visible']
        assert any(e['kind'] == 'raw-layer-pixels' and e['size'] == [3, 4] for e in report['exports'])
        try:
            inspect(source, folder / 'inspection')
        except FileExistsError:
            pass
        else:
            raise AssertionError('Existing output was overwritten')
        cmyk = folder / 'neutral-cmyk.psd'
        PSDImage.new('CMYK', (12, 9)).save(cmyk)
        result = inspect(cmyk, folder / 'cmyk-inspection', preview=True)
        assert result['source_unchanged'] and not result['exports']
        assert any('mode CMYK' in warning for warning in result['warnings'])
        assert (folder / 'cmyk-inspection' / 'psd-report.json').is_file()

        # Neutral linear-RGB profile makes an accidental ICC conversion observable.
        profile = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
        for index in range(struct.unpack_from('>I', profile, 128)[0]):
            tag, offset, _ = struct.unpack_from('>4sII', profile, 132 + index * 12)
            if tag in (b'rTRC', b'gTRC', b'bTRC'):
                assert profile[offset:offset+4] == b'para'
                struct.pack_into('>H', profile, offset + 8, 0)
                struct.pack_into('>i', profile, offset + 12, 65536)
        profile[84:100] = bytes(16)
        icc_source = folder / 'neutral-icc.psd'
        icc_psd = PSDImage.new('RGB', (3, 2), color=(128, 64, 32))
        PixelLayer.frompil(Image.new('RGB', (3, 2), (128, 64, 32)), icc_psd, 'Neutral patch')
        icc_psd.image_resources[Resource.ICC_PROFILE] = ImageResource(key=Resource.ICC_PROFILE, data=bytes(profile))
        icc_psd.save(icc_source)
        original = icc_source.read_bytes()
        opened = PSDImage.open(icc_source)
        output = folder / 'icc-inspection'
        result = inspect(icc_source, output, preview=True, pixel_indices=[0])
        assert result['source_icc_present'] and result['icc_conversion_applied'] is False
        assert result['depth'] == 8 and not result['warnings']
        for source_image, filename in ((opened, 'merged-preview.png'),
                                       (opened[0], 'layer-000.png')):
            raw = source_image.topil(apply_icc=False)
            managed = source_image.topil(apply_icc=True)
            assert raw.tobytes() != managed.tobytes(), 'ICC fixture must change values when applied'
            with Image.open(output / filename) as exported:
                assert exported.mode == raw.mode and exported.tobytes() == raw.tobytes(), filename
                assert not exported.info.get('icc_profile'), 'Diagnostic PNG must not claim converted color'
        assert icc_source.read_bytes() == original and result['source_unchanged']
    print('OK: neutral PSD, hierarchy, raw pixels, source integrity, no overwrite, unsupported preview mode, ICC preview and layer values')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, nargs='?')
    parser.add_argument('output', type=Path, nargs='?', help='New output directory')
    parser.add_argument('--preview', action='store_true', help='Export cached merged pixels; never recomposite')
    parser.add_argument('--layer', action='append', type=int, default=[], help='Export a preorder layer index; repeatable')
    parser.add_argument('--mask', action='append', type=int, default=[], help='Export a stored mask by layer index; repeatable')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test(); return
        if not args.source or not args.output:
            parser.error('Provide a PSD path and a new output directory')
        report = inspect(args.source, args.output, args.preview, args.layer, args.mask)
        print(json.dumps({'layers': len(report['layers']), 'exports': report['exports'],
                          'warnings': report['warnings'], 'source_unchanged': report['source_unchanged']}, indent=2))
    except ImportError:
        parser.error('Requires psd-tools and Pillow; run in an existing environment or with uv run --with psd-tools')
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
