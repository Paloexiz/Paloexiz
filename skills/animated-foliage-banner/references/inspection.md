# Inspection tools

Use these tools to answer a concrete source or rendering question. They accept supplied paths and do not require a particular artwork or the scene contract. The examples run from the skill directory and write outside the distributed package. Substitute input/output paths for the actual workspace. All export commands require a new output directory to protect existing files.

## Runtime and first run

| Tool | Required runtime | Output |
| --- | --- | --- |
| `inspect_psd.py` | Python 3.10+, `psd-tools` (tested with 1.24.0) and Pillow | Layer/effect JSON; optional cached preview, raw layers and stored masks |
| `render_svg.cjs` | Node.js 20+, `playwright`, installed Chrome | Frozen full-frame PNG, optional crop PNG, render settings and hashes |
| `compare_images.py` | Python 3.10+, Pillow | Difference metrics; optional paired crops, visible diff PNG and JSON |

Use an available runtime. For a temporary Python tool environment, `uv run --no-project --with psd-tools python -B scripts/inspect_psd.py ...` or `uv run --no-project --with Pillow python -B scripts/compare_images.py ...` supplies dependencies without adding them to the artwork. For Node.js, use an existing Playwright environment or install it in a separate tool workspace; do not add browser dependencies to the SVG. The scripts do not install Chrome. `--help` lists each command's flags.

If Playwright is in a separate workspace, set `NODE_PATH` to its `node_modules` directory before running the commands. Changing the working directory alone does not change an absolute script's module lookup. For example, use `export NODE_PATH=/path/to/tools/node_modules` in a POSIX shell or `$env:NODE_PATH = 'C:/path/to/tools/node_modules'` in PowerShell.

This neutral example exercises assembly, rendering, and comparison without a PSD or private assets:

```sh
python -B scripts/build_banner.py examples/minimal ../example.svg
node scripts/render_svg.cjs ../example.svg ../frame-zero --time 0
node scripts/render_svg.cjs ../example.svg ../frame-one --time 1 --css-time 0
python -B scripts/compare_images.py ../frame-zero/frame.png ../frame-one/frame.png --output-dir ../comparison
```

The second capture advances the contour while holding CSS foliage at zero. Inspect the paired images and changed region; different pixels establish a visible difference, not whether that difference looks natural. For a contract-compliant scene, continue with the [playback check](production.md#scene-contract-checks) to verify actual image embedding and reduced motion.

## Optional PSD inspection

Skip this section for flat images. Inventory the source before choosing layer indices:

```sh
python -B scripts/inspect_psd.py ../source.psd ../inventory --preview
```

Read `psd-report.json`. Layer indices are zero-based preorder traversal; `parent` records the group index, so duplicate names remain distinguishable. The report records canvas dimensions, layer bounds, local/effective visibility, clipping, blend modes, mask bounds, effect enablement/parameters, and text/transform metadata where present. Layer opacity uses 0–255; effect opacity follows the source API's percentage units. It is a selected inventory, not a complete serialization of every Photoshop feature or font resource.

After identifying the relevant index, add repeatable `--layer INDEX` or `--mask INDEX` flags with a different output directory. Raw layer pixels do not include composited layer effects. Mask exports use the stored combined pixel/vector channel when present, otherwise the stored user channel; `export_channel` records this choice. No mask is synthesized. Reported bounds and background describe that selected channel; use them to place the crop, which does not start at the canvas origin.

`--preview` exports cached merged pixels only. The tool never recomposites layers or saves the source PSD; it verifies the source hash after reading. A missing cached preview/layer/mask produces a warning, not proof that the source is empty. If a required feature cannot be inspected, use a supplied flat preview or a native editor when available, and state the limitation. Source text and layer names can be private: keep reports with the work, outside the shared skill.

Both cached previews and layer exports explicitly disable ICC conversion (`apply_icc=False`). The report records `source_icc_present`, `icc_conversion_applied: false`, and the source bit `depth`. The source profile is neither applied nor copied into these diagnostic PNGs; their untagged values are for channel comparisons, not proof of color-managed appearance. Here, `raw-layer-pixels` means uncomposited decoded pixels, not a lossless dump of every PSD channel: psd-tools can reduce 16/32-bit samples to 8-bit and adjust cached-preview transparency during decoding.

When decoded pixels have a mode that PNG cannot preserve, such as CMYK, the inventory still completes and a warning identifies the skipped export. Obtain an explicitly color-managed RGB preview from the source application when visual comparison requires one.

## Fixed-time rendering

```sh
node scripts/render_svg.cjs ../artwork.svg ../detail --width 800 --time 1.5 --css-time 0 --scale 2 --crop 20,30,160,60
```

- `--time` selects the SMIL clock in seconds. CSS uses the same time unless `--css-time` is supplied; setting it to zero isolates contour movement. This requires declarative time-based animation, not scripts or user events.
- `--width`/`--height` are rendered CSS pixels. With one dimension, the tool preserves the source aspect ratio. With neither, it uses declared absolute dimensions, then the viewBox, then the browser's default size. Supplying both intentionally sets the viewport; the SVG's own `preserveAspectRatio` still applies.
- `--crop X,Y,WIDTH,HEIGHT` is a rectangle in that rendered canvas, not in unscaled viewBox coordinates. It must fit the canvas. `--scale` controls pixels per CSS pixel; scale 2 makes a 160 × 60 crop into a 320 × 120 PNG. Captures are limited to 64 megapixels.
- `--motion reduce` selects the document's reduced-motion styles. It does not prove that an embedded image receives the same preference; use the dedicated playback check for that question.

Outputs are `frame.png`, optional `crop.png`, and `render.json`. The report records input/frame hashes, Chrome version, dimensions, clocks, scale, crop, and browser warnings. Compare captures made with the same settings. PNG alpha is preserved.

The tool serves one SVG over loopback, blocks source scripts and external resources, and never changes the input. Missing external images/fonts can therefore affect a capture; inspect warnings before treating it as a fidelity result. This is a direct-SVG diagnostic, not hosted or image-embedding validation. If Chrome cannot launch, retain the input and report the environment error; do not interpret a missing capture as an artwork failure.

## Raster comparison

```sh
python -B scripts/compare_images.py ../reference.png ../candidate.png --region 10 20 120 60 --tolerance 1 --output-dir ../detail-diff
```

Input dimensions must match; the tool does not silently resize or align them. Region coordinates are integer source-image pixels. It compares decoded RGBA channel values, including alpha and RGB stored under transparency; it does not align animation phases, apply ICC conversion, or make a perceptual similarity judgment. Render or export both inputs under equivalent color and scale settings first.

`changed_pixels` counts pixels with any channel difference strictly greater than `--tolerance` (default 0). `changed_bbox` is in full-image coordinates with an exclusive right/bottom edge; `null` means no above-threshold differences. Maximum and mean differences remain unthresholded, so small changes are still visible in the report. Use a tolerance only when justified by the renderer and task.

Without `--output-dir`, JSON goes to stdout. With it, the command also writes `before.png`, `after.png`, a grayscale maximum-channel `diff.png`, and `comparison.json`. The diff keeps alpha-only changes visible; it is a diagnostic map, not a modified artwork. A large difference does not identify its cause. Return to layer/effect inspection or fixed-time rendering to isolate it; identical pixels alone do not establish motion or source fidelity.

## Checks and retention

Use `python -B` for these tools and for temporary Python checks that import them. Pass `-B` to the Python interpreter even when using `uv run`. It suppresses new bytecode writes; it neither deletes existing caches nor prevents reading them. Confirmed disposable caches from earlier runs must be removed separately. A Git ignore rule does not exclude files from a directory copy or an archive.

When validating a changed skill, compare its file list and hashes before and after a representative documented run. Keep generated output outside the package. Before distribution, inspect the actual candidate folder or archive file list: include only reviewed skill sources/resources and licenses; exclude caches, local inputs, logs, outputs, and temporary environments. Do not infer a clean package from Git status alone. From the candidate skill directory, this check rejects Python cache and compiled artifacts without writing bytecode:

```sh
python -B -c "from pathlib import Path; assert Path('SKILL.md').is_file(), 'Run from the candidate skill directory'; bad = [str(p) for p in Path('.').rglob('*') if p.name == '__pycache__' or p.suffix.lower() in ('.pyc', '.pyo', '.pyd')]; print(bad); raise SystemExit(bool(bad))"
```

Run these when changing the corresponding tool, not for every banner edit:

```sh
python -B scripts/inspect_psd.py --self-test
node scripts/render_svg.cjs --self-test
python -B scripts/compare_images.py --self-test
```

The tests use neutral generated data. They cover source integrity and hierarchy, ICC-free preview/layer pixel values, frozen CSS/SMIL clocks and crop scaling, and RGBA differences/coordinates/tolerance. The renderer's shared clock helper is also used by `check_banner_browser.cjs`; run that check against the bundled example when changing the helper.

Preserve the reusable scripts and private authoring inputs. Keep only the screenshots and JSON needed to justify a decision in the work's local evidence directory; discard disposable captures and temporary environments once no longer needed. Do not promote a one-work repair script, fixed layer name, palette threshold, or identity-bearing fixture into this skill.
