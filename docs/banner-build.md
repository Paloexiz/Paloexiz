# Banner authoring and assembly

Start with a flat image, separated assets, or an optional layered source. Follow the [production guide](../skills/animated-foliage-banner/references/production.md) to separate textures, leaf alpha, fixed pivots, contour geometry, shadows, and lettering. A PSD and a paid editor are not prerequisites. Identify reconstructed hidden pixels and estimated effects explicitly.

## Authoring inputs

The optional assembler takes an editable SVG and separate motion controls:

- The SVG contains embedded textures or vector shapes, leaf placement and CSS motion, lettering, masks, effects, a rest contour, a rig, and reduced-motion selection. The displayed artifact can also be the editable input.
- `motion.json`: contour vertex indices, equally spaced periodic control poses, and output sampling density.

The [scene contract](../skills/animated-foliage-banner/references/production.md#scene-contract-and-minimal-example) defines the supported IDs and structure. The assembler does not segment a flat image or infer source layers. Keep input hashes, dependencies, font provenance, coordinate mapping, reconstruction limits, and the build command in a per-work record. Private inputs and records belong in durable local storage excluded from publication; public examples should be independent, neutral assets.

## Run the independent example

From the repository root, with Python 3.10 or later. Use `-B` for these commands and temporary checks that import skill helpers so they do not write bytecode into the skill directory:

```sh
python -B skills/animated-foliage-banner/scripts/build_banner.py skills/animated-foliage-banner/examples/minimal example.svg
python -B skills/animated-foliage-banner/scripts/build_banner.py example.svg example.svg --motion skills/animated-foliage-banner/examples/minimal/motion.json
python -B skills/animated-foliage-banner/scripts/build_banner.py --self-test
python -B skills/animated-foliage-banner/scripts/build_fur_poses.py --self-test
```

The example contains simple vector shapes and needs no external artwork, font, or Python package. The generator samples a periodic Catmull–Rom curve, rounds moving coordinates to four decimal places, checks stored contours and interval midpoints for intersections, and emits linear SMIL poses with a repeated first pose. Untracked vertices stay at rest. Scene resources are carried through without image decoding or re-encoding.

The source curve has matching tangents; exported linear interpolation still has velocity changes at pose boundaries. Use the reported velocity changes and rendered size to choose sampling density. More poses increase payload size and do not establish physical accuracy.

With Pillow available, check structure and in-memory motion regressions:

```sh
python -B skills/animated-foliage-banner/scripts/check_fur_motion.py example.svg --self-test
```

With Node.js, Playwright, and installed Chrome, check actual image embedding:

```sh
node skills/animated-foliage-banner/scripts/check_banner_browser.cjs example.svg browser-check --self-test
```

See [check coverage and limits](../skills/animated-foliage-banner/references/production.md#scene-contract-checks). Keep generated examples, screenshots, and execution reports local. These checks do not replace visual comparison with the supplied reference or verification on the intended host.

For source inspection or a localized visual question, use the [diagnostic workflow](../skills/animated-foliage-banner/references/inspection.md): optional PSD inventory, fixed-time SVG captures, and same-size raster comparison. That guide includes a neutral end-to-end example, runtime requirements, parameter units, outputs, and limits. These operations also work outside the authored scene contract.

## Deliver one artifact

Keep one editable SVG and reference it directly from the README with a relative image path. In this repository that path is `artifacts/banner.svg`. Edit its scene content directly and use the SVG input mode to refresh contour motion in place from retained controls. The assembler validates before atomically replacing the output. Use Git commits for version history; a second scene copy is unnecessary. Directory input remains a convenient shorthand for the bundled example. Copying the skill to another workspace preserves that example and adjacent Python imports without requiring this repository's artwork.

When distributing the skill itself, follow its [package hygiene check](../skills/animated-foliage-banner/references/inspection.md#checks-and-retention) on the actual candidate directory or archive; repository ignore rules do not control direct copies.

For repeatable assembly, retain the SVG, motion controls and generator version in their appropriate public or private storage. Compare output hashes when refreshing unchanged inputs; use a reviewed visual and structural tolerance when changing native exports or encoders. Regenerating contour motion does not repeat the earlier extraction, tracing, texture repair, or typography work automatically.
