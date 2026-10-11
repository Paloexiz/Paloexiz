"""Read the optional contour rig without interpreting unrelated SVG metadata."""
import json


def read_motion_data(root):
    elements = root.findall('.//*[@id="fur-motion-data"]')
    if len(elements) != 1:
        raise ValueError('Expected exactly one fur-motion-data element')
    element = elements[0]
    # Foreign child payloads are not part of the rig JSON.
    text = (element.text or '') + ''.join(child.tail or '' for child in element)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError('fur-motion-data must contain a JSON object in its direct text') from exc
    if not isinstance(data, dict):
        raise ValueError('fur-motion-data must contain a JSON object')
    return data
