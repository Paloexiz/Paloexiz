"""Exercise the checker CLI with equivalent metadata layouts. Requires Pillow."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_banner import build


class MetadataInputTests(unittest.TestCase):
    def test_self_test_preserves_supported_inputs(self):
        scripts = Path(__file__).resolve().parent
        payload, _ = build(scripts.parent / 'examples' / 'minimal')
        with tempfile.TemporaryDirectory() as directory:
            for layout in ('direct', 'tail', 'split', 'nested', 'referenced-child'):
                with self.subTest(layout=layout):
                    root = ET.fromstring(payload)
                    metadata = root.find('.//*[@id="fur-motion-data"]')
                    text = metadata.text
                    if layout in ('tail', 'split', 'referenced-child'):
                        child = ET.SubElement(metadata, '{urn:example:foreign}record')
                        child.text = 'Unrelated metadata'
                        cut = len(text) // 3 if layout == 'split' else 0
                        metadata.text, child.tail = text[:cut], text[cut:]
                        if layout == 'split':
                            child.tail = text[cut:2 * cut]
                            ET.SubElement(metadata, '{urn:example:foreign}extra').tail = text[2 * cut:]
                        if layout == 'referenced-child':
                            shape = ET.SubElement(metadata, '{http://www.w3.org/2000/svg}path',
                                                  {'id': 'auxiliary-shape', 'd': 'M0,0L1,0L0,1Z'})
                            ET.SubElement(root, '{http://www.w3.org/2000/svg}use', {'href': '#' + shape.get('id')})
                    elif layout == 'nested':
                        del metadata.attrib['id']
                        metadata.text = None
                        ET.SubElement(metadata, '{urn:example:motion}data', {'id': 'fur-motion-data'}).text = text
                    svg = Path(directory) / f'{layout}.svg'
                    original = ET.tostring(root)
                    svg.write_bytes(original)
                    for arguments in ([], ['--self-test']):
                        result = subprocess.run([sys.executable, '-B', str(scripts / 'check_fur_motion.py'),
                                                 str(svg), *arguments], cwd=directory,
                                                capture_output=True, text=True, encoding='utf-8')
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertEqual(svg.read_bytes(), original, 'Checker changed its input')


if __name__ == '__main__':
    unittest.main()
