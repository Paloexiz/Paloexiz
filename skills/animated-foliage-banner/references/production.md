# Production guide

Read only the route matching the available input. These are technical methods for the chosen artwork, not requirements to add subjects, texture, lettering, or effects. None requires a specific operating system or paid editor.

## Input routes

### Original work from a brief

With no reference or assets, establish the intended content and destination from the request, then author the composition independently. State consequential assumptions; ask only when missing information blocks the requested result. There are no hidden source layers or fidelity targets to reconstruct. Select the sections below for the elements actually created. A foliage-only scene need not acquire a character, and an unrelated banner need not acquire foliage to use these tools. The minimal example demonstrates an API contract, not a composition to imitate.

### A. A single flat PNG/JPG

1. Inspect the actual resolution and color/alpha channels. Record visible text, major region boundaries, repeated leaf shapes, apparent light direction, and the desired composition. Do not invent hidden layer names or font metadata.
2. Trace the subject silhouette and visible foreground/background regions in source coordinates. Prefer a small manually corrected contour over a noisy automatic trace. Preserve distinctive ears, muzzle, chin, neck, and tuft tips if they exist.
3. For each moving leaf, choose an identifiable leaf or small connected cluster. Author its alpha and stem pivot. Prefer clean pixels away from text, the silhouette boundary, and baked effects. Preserve the original grain rather than turning every leaf into a generic icon.
4. Build the backing field from clean nearby regions or a repeatable texture patch. Fill the leaf's vacated region and enough surrounding area for its sweep. A nearby patch may be more faithful than broad inpainting. Check for repeating seams and conspicuous smooth patches.
5. For a patterned silhouette, reconstruct a clean interior field from representative unshadowed pixels. Extend it past the contour's full motion envelope. Do not propagate background colors into the interior when extending an edge.
6. Where shadows, text, or occlusion hide the needed pixels, treat the reconstruction as inferred. Use available image-editing capabilities or author a compatible texture; preserve observed regions. Do not advertise pixel-exact recovery of missing information.
7. Transcribe readable text. When the typeface is unknown, keep it as a static extracted visual if that is clean and sufficient, or use an identified substitute with similar proportions. Do not infer a font's license from the screenshot. Ask for exact wording only when it cannot be read and is necessary.

This route can reproduce the composition and motion character without an original PSD. Its uncertainty concerns hidden pixels, original typography, and source effect parameters. Record those limits with the deliverable, not as repeated requests for unavailable assets.

### B. Separated assets, with gaps

Use provided transparency, masks, lettering, and texture fields directly after inspection. Align them in one coordinate system. Check whether a supplied cutout already includes a shadow or colored fringe. Use route A only for the missing regions or effects. A missing font file does not invalidate supplied outlined or raster lettering.

### C. A layered source, when supplied

Record layer order, visibility, clipping dependencies, group isolation, blend mode, masks, effect parameters, and type transforms. Cached merged pixels, raw layer pixels, and a fresh composite are different observations.

`psd-tools` can inspect a PSD without Photoshop, but its rendering coverage is version- and feature-dependent. Compare its result with a trusted preview before relying on it for complex effects. When native Photoshop is available and a mismatch matters, export from a byte copy in a temporary workspace; preserve the original and verify its hash. ExtendScript/COM and UXP are different APIs. Do not assume either exists on another user's machine.

Use the [optional PSD inspector](inspection.md#optional-psd-inspection) for a repeatable read-only inventory and cached exports before writing another temporary extraction script.

For color extraction, disable the source masks and shadows that will become dynamic. Export the unmasked color field separately from the alpha/mask and from the effect. If no native compositor is available, use cached pixels or the flattened reference through route A and state the approximation.

## Layer assembly

Choose paint order from the artwork. Separate resources only where motion or compositing requires it:

| When present | Technical separation |
| --- | --- |
| Extracted moving foliage | Clean backing field, leaf color/alpha, placement, and local motion |
| A moving silhouette | Interior paint and contour geometry shared by its relevant clips, masks, and effects |
| A shadow or reveal | Its geometry, color, blend behavior, and filter region |
| Lettering | Glyph appearance and any layer/group effects that need independent control |

A mask can reveal a colored backing field and look like a cast shadow; inspect both sides before choosing a black shadow filter. Omit components the brief or source does not contain.

Keep grain/detail rasterized where appropriate. Embedded data URLs make an artifact independent of local image files, but increase its byte size. Resize and encode against the actual display size and pixel density. Share repeated resources with references when practical and measure the result.

For a true inner shadow, derive an edge band from the contour alpha and an eroded/blurred/offset version of it, then color that band and clip it inside the subject. Set filter coordinate units, region, and color interpolation explicitly. Photoshop size/choke values are not automatically identical to SVG morphology radius or Gaussian deviation. Fit and compare the edge effect independently of the leaf texture.

Canvas cropping is not a physical silhouette edge. Extend a touched contour beyond the canvas far enough for mask offsets and filter support, keeping added closure vertices fixed across poses. Inspect text-layer and parent-group effects separately; apply canvas-pixel offsets outside glyph scaling and avoid duplicating effects already baked into an export. Use [fixed-time crops and raster comparisons](inspection.md) to inspect these boundaries.

## Motion and the optional fur helper

Keep placement in a parent transform and perform local rotation, skew, or controlled bending around the authored attachment. When using the example's `(0, 0)` convention, place the actual stem endpoint there. A stationary transform origin does not establish that the drawn root is stationary: transform the identified root point through its full ancestor chain at several phases and compare its screen coordinates. Inspect connection to the supporting geometry, using a per-work tolerance in rendered pixels. Related foliage can share wind timing with local stiffness and phase differences.

For compatible polygonal fur, author spans on a consistent contour. The helper accepts a **closed polygon without a repeated closing vertex**, using sequential indices and non-wrapping tuft ranges:

```json
{
  "points": [[0, 0], [-4, 20], [12, 0], [12, -12], [0, -12]],
  "period": 6,
  "samples": 40,
  "tufts": [
    {"name": "tip", "start": 0, "tip": 1, "end": 2,
     "degrees": 15, "phase": 0.2, "tip_lag": 0.025}
  ]
}
```

`phase` and `tip_lag` are fractions of a cycle, not seconds. Coordinates and angles are design inputs, not inferred from a file name. A tuft is the contour span between two fixed root boundaries; its perpendicular distance from the root chord controls deformation strength. Shared endpoints are allowed; overlapping interiors are rejected. Reindex a closed contour if a tuft would cross its final/first vertex.

Run with Python 3.10 or later; the helper itself has no third-party dependencies:

```sh
python -B scripts/build_fur_poses.py rig.json poses.json
python -B scripts/build_fur_poses.py --self-test
```

The result contains `rest_d`, an `animation` object suitable for an SVG `animate` element, a preserved rig, and sampled motion statistics. Assemble it into the work's own build script. Keep `rig.json`, the generator version, and the assembly command as durable source files.

The helper uses a periodic primary signal plus a weaker second harmonic and root-to-tip weighting. It checks its stored poses and midpoints for crossings and keeps non-tuft vertices fixed. These sampled checks are not a proof against every intermediate collision. Linear pose interpolation has piecewise-constant velocity; the reported largest boundary velocity change makes that approximation visible. Increase sampling only when the intended output size warrants the extra bytes, or author a different interpolation scheme with verified tangents. Do not call a position-only loop test a smooth-velocity guarantee.

The helper neither segments images nor repairs poor anchors. A wrong mask or root can produce plausible-looking output while remaining visually wrong. Compare the rig to the supplied artwork and test the source image's visible small tufts, not just the largest spikes.

### Scene contract and minimal example

The optional `build_banner.py` generates contour motion in an editable SVG using separate motion controls. Pass the SVG and `--motion` to refresh an existing work. A directory input is shorthand for its `scene.svg` and `motion.json`, as used by the bundled example. Its authored tracks use a periodic Catmull–Rom curve, exported as uniformly sampled linear poses. It does not infer missing pixels or original layers. The [minimal scene](../examples/minimal/scene.svg) and [motion controls](../examples/minimal/motion.json) are independent geometric examples.

The assembler and accompanying checks support this deliberately small contract. Its IDs, polygon syntax, paired foliage animations, and contour references are tool requirements, not requirements for every work. Curves or other animation systems may be more suitable; verify those with checks tailored to their representation instead of changing the artwork to satisfy this validator.

- A single SVG canvas with unique IDs and finite positive dimensions. Embed image resources as PNG/JPEG/WebP data URLs; keep lettering self-contained and stationary.
- `path#fur-outline` holds a closed rest polygon in compact `M{x},{y}L{x},{y}...Z` syntax with no repeated closing vertex. `path#fur-still` holds identical rest geometry without children. Directory inputs omit generated animation; SVG inputs may contain one direct `animate` for `d`, whose sampled values will be refreshed from the controls.
- Refreshing an existing animation preserves its ID. New animations receive `fur-sway`, or the first unused `fur-sway-N` ID if that name is occupied. Other source IDs and references remain unchanged; consumers should locate the animation under `#fur-outline` rather than assume its generated ID.
- Exactly one element with ID `fur-motion-data` holds the rig JSON above in its direct text, omitting `points` and `samples`: these come from the path and requested output intervals. It can be the `metadata` element or a dedicated child within it. Unrelated child payloads are excluded; direct text and child tails are read together. Set `period` explicitly in seconds. Tuft interiors identify the vertices allowed to move; root boundaries and all other vertices stay fixed.
- `motion.json` contains `intervals` (integer, at least 8), `vertices` (unique moving vertex indices including every tuft tip), and `poses` (at least four equally spaced control frames, each with one `[x,y]` per listed vertex). Omit a repeated closing control. All coordinates are finite source units.
- Each moving leaf has a stationary placement parent, a `g.branch`, and exactly one direct `g.leaf` child, both using local origin `0 0`. A root stylesheet declares infinite `branch-wind` and `leaf-flutter` CSS animations. The browser check expects exactly these two CSS animations per leaf. Local periods and phase offsets may differ.
- Each clip, mask, or effect that switches contour has direct `use.motion-contour` and `use.still-contour` children in a shared parent, referencing `#fur-outline` and `#fur-still`. Their presentation attributes match; only ID, class, and href differ. The ordinary view shows the moving reference; reduced motion shows the static one and disables leaf CSS motion. Parent IDs, pair counts, transforms, and colors are artwork inputs.

Run from the skill directory, keeping the Python scripts adjacent:

```sh
python -B scripts/build_banner.py examples/minimal ../example.svg
python -B scripts/build_banner.py ../example.svg ../example.svg --motion examples/minimal/motion.json
python -B scripts/build_banner.py --self-test
```

For directory inputs, write output outside that directory. SVG input and output may be the same file: validation finishes before a temporary file is written beside the output and atomically replaces it. Keep the editable SVG under version control and retain its motion controls and build recipe; there is no need to maintain a second scene copy. Edit textures, lettering and effects directly in the SVG. Update motion controls when changing the rest contour or rig; generated animation values are replaced on refresh. Author comments and processing instructions are retained inside and outside the root; DTD-bearing inputs are rejected before writing. XML serialization may normalize formatting and namespace prefixes. The example needs Python 3.10+ with its standard library only. `--self-test` checks ID collisions, repeatable refresh, author notes and rejection of unrelated animation or DTDs in memory. Private inputs need not be published to make the generic workflow usable.

The checker reads rig metadata without authenticating provenance. The assembler rejects SVGs containing a C2PA manifest before writing: XML reserialization and geometry edits can invalidate signed bindings. Use an unsigned authoring source or a provenance-aware editing tool; do not strip credentials merely to pass assembly. See the [C2PA guidance](https://spec.c2pa.org/specifications/specifications/2.2/ux/UX_Recommendations.html) for the distinction between edited content and valid provenance.

## Stable lettering

When lettering is present, preserve readable text content separately from glyph geometry. A system font stack can substitute glyphs on another machine; `textLength` constrains spacing/length, not the glyph shapes. For fixed appearance, shape the actual font first (glyph selection, kerning, advances, and offsets), then export positioned outlines, or retain a suitable rendered text asset. Extracting each character's outline without shaping can lose ligatures and spacing. If live text is intentional, state the fallback behavior and inspect it without the preferred local font. Use a native style export when a complex glow or blend effect cannot be reproduced acceptably with simple SVG filters.

Record the actual font source, file/version, hash, and applicable license reference; record shaping/export settings when relevant. Include license files if distributing font software. A rendered wordmark and a redistributed font package are different outputs. Keep each work's identity and typography out of reusable examples. No particular typeface or shaping library is required.

## Reduced motion and image-host constraints

Default animation may be continuous while reduced-motion output is still. Cover both CSS and SMIL; `animation: none` does not disable an SVG `animate` element.

Choose a presentation supported by the host:

- Where an HTML picture/source arrangement and media conditions are retained, provide separate static and animated assets and select the static one for reduced motion. Verify the host's rendered markup; do not assume a sanitizer preserves it.
- For a single SVG image, a CSS media query can select a static painted scene instead of the animated one. Use a genuinely static contour for **all** references in that scene, including masks and shadows. Hiding the SMIL element itself is not a demonstrated way to stop its animation. A hidden animated scene may still incur work, so verify behavior and cost.
- Where the page is under the user's control, an external accessible motion control can offer an additional choice. A control or script embedded inside an image-mode SVG cannot be relied on.

Use separated-time image captures in the actual embedding mode to verify reduced-motion output. Local success is not proof of GitHub's published behavior. Publishing is a separate action, requiring the user's authorization.

Validate the test environment as well as the artwork. Page-level media emulation may not reach an embedded SVG in every browser configuration. The supplied harness launches a separate Chrome process with `--force-prefers-reduced-motion` and checks an independent image-mode control before interpreting captures. Verify that control on the installed browser; do not assume the launch flag alone proves the preference took effect.

## Reproducible handoff and validation

### Scene-contract checks

[check_fur_motion.py](../scripts/check_fur_motion.py) checks the assembled scene contract. It requires Python 3.10+, Pillow, and an explicit SVG path. From the skill directory, run after building the example:

```sh
python -B scripts/check_fur_motion.py ../example.svg --self-test
node scripts/check_banner_browser.cjs ../example.svg ../browser-check --self-test
```

The Python check verifies positional closure, fixed roots, moving tips, sampled geometry, linear interpolation, uniform timing, contour pairs, leaf animation declarations, ID uniqueness, href references, and embedded image decoding. It reports displacement and velocity changes without imposing one work's aesthetic thresholds on another. `--self-test` rejects missing leaf styles, discrete interpolation, and static tips in memory without changing the source. Run checks without Python's optimization flag, which disables assertions. Declaration checks do not prove effective playback, and this is not a full SVG sanitizer or a validator for arbitrary CSS.

When changing the checker, run `python -B scripts/test_check_fur_motion.py` as well. This Pillow-dependent regression builds the neutral example and runs the checker CLI with and without `--self-test` from a temporary working directory. It covers direct, tail, split, and nested rig JSON plus referenced metadata children, and verifies that input bytes remain unchanged. Test fixtures are temporary; no additional artwork or font is needed.

The browser check requires Node.js, an available `playwright` package, and installed Chrome. Use an existing runtime or a separate tool environment; no browser library is shipped inside the SVG. It serves the input over loopback and verifies ordinary/reduced-motion `<img>` captures at 1024 and 375 CSS pixels, with an independent image-mode control. In a directly opened SVG, it samples leaf CTMs, discovers contour pairs, and checks their effective selection in both media modes before pausing any animations. It then restores normal motion and freezes CSS foliage to isolate visible contour motion at zero, one-quarter, and one-half of its declared period. Changing a hidden definition alone cannot pass. `--self-test` rejects static contours selected during ordinary playback and running leaf CSS during reduced motion. The mutations use inline important declarations against higher-specificity blocking rules and confirm that contour display has switched or the named leaf animation is running before checking rejection. Their cleanup restores the exact original inline styles, including absent or empty attributes. Mutations remain in the browser DOM and are removed after each assertion.

The report's `fixedOrigins` counts stationary CTM origins; `movingLeafTransforms` and `minSamplePointMovement` describe the synthetic local point `(100, 0)` in SVG viewport units. They replace the former `fixedRoots`, `swayingLeaves`, and `minNonRootMovement` names. `attachmentVerified: false` is deliberate: no arbitrary drawn root is inferred. A self-test rotates a neutral shape whose root is offset from its origin to demonstrate that limitation. Use identified root coordinates and the [screen-space sampling example](inspection.md#fixed-time-rendering) for actual attachment checks.

Screenshots and result JSON are written under the specified output directory. Finite sampling can miss defects or require adjustment for unusually slow or symmetric motion. It does not establish every frame's correctness, source fidelity, hosted behavior, cross-browser compatibility, or performance. Visual review and work-specific thresholds remain necessary; layouts outside this contract require adapted checks.

Keep `check_banner_browser.cjs` beside `render_svg.cjs`, which supplies its shared clock helper; both require Node.js 20+.

### Checks for each work

Keep a small per-work build record for the elements that exist:

- Supplied input identities and hashes, canvas/viewBox mapping, and source resolution.
- Which regions are observed, extracted, inferred, substituted, or unavailable.
- Applicable alpha masks, identified attachment points, contours, deformation controls, and static presentation.
- Source effect parameters where available; fitted estimates where not.
- Font provenance, image encoding settings, dependency versions, and deterministic seeds.
- Durable assembly command and the visual/structural comparison used to accept a rebuild.

Name the authoritative editable input: either a directly edited SVG plus motion controls, or a generator plus its source inputs. Regeneration must not silently replace manual edits to another file presented as editable. Keep verification read-only; an explicit rebuild used for comparison writes to a separate candidate path, then compares it with the retained artifact. In-place refresh is an intentional authoring operation, not a prerequisite for inspecting a delivered file.

Keep required scripts and controls in durable storage. Resolve resource paths from the script or an explicit input, not the caller's working directory or one machine's home directory. Pass the selected interpreter/tool path and dependency environment to child commands too. Test documented commands from another working directory with outputs outside the package; a same-machine rebuild alone does not establish portability to a clean environment. Record unavailable dependencies rather than installing into or modifying the distributed skill.

Exact byte reproduction may be impossible with some native exports; define a visual and structural tolerance instead of silently claiming byte identity.

Test syntax and references, then select checks for the actual scene. Where applicable, exercise attached roots, moving tips, text appearance, shadow synchronization, exposed pixels, reduced motion, and the loop boundary. Establish detection with small temporary defects: remove expected motion, choose a static fallback during normal playback, detach an identified root, or introduce a known coverage gap. Retain the original unchanged. Isolate the feature under test; other moving elements cannot establish that a particular contour moves. Use an actual image element in addition to a direct diagnostic view.

An opaque background makes a full-image alpha check pass even when a subject or shadow misses the canvas edge. Inspect the required painted region in normal and reduced presentations at relevant extrema. Use isolated layers or work-specific color/mask comparisons with [fixed-time crops and image differences](inspection.md#raster-comparison); confirm a deliberately shortened subject or shadow fails that check. State sample times and thresholds. Pixel coverage does not prove source fidelity or natural motion.

Measure payload and responsive layout on the final artifact. For performance claims, record browser version, device, viewport, embedding mode, visibility, duration, and baseline. A parent page's requestAnimationFrame intervals measure scheduling, not the cost of rendering its SVG image. Use browser profiling evidence for CPU/rendering cost; describe unavailable GPU or device measurements as unmeasured. Validate image-mode reduced motion with an independent control before using it as a baseline. Compare under equivalent conditions; short desktop traces do not establish all-viewer performance.

Bind the final report and previews to the delivered SVG hash, input/control hashes, generator revision, commands, and capture settings. Recheck these after the last edit; superseded evidence stays labeled as such. Keep technical checks, visual review against the brief, and hosted verification as separate results.

## Primary references

- [Crysis vegetation detail bending](https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-16-vegetation-procedural-animation-and-shading-crysis): stiffness, phase variation, and local deformation.
- [AMD TressFX simulation](https://github.com/GPUOpen-Effects/TressFX/blob/master/src/Shaders/TressFXSimulation.hlsl): constrained roots and shape preservation as conceptual references.
- [W3C SVG paths](https://www.w3.org/TR/SVG2/paths.html) and [SVG animation](https://www.w3.org/TR/SVG11/animate.html): compatible path structure and interpolation.
- [SVG image restrictions](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image) and [reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion): embedding and presentation constraints.
- [psd-tools](https://psd-tools.readthedocs.io/en/latest/index.html): optional source inspection and compositor limitations.
- [OpenCV inpainting](https://docs.opencv.org/4.13.0/d7/d8b/group__photo__inpaint.html): one possible backing-field repair method, requiring visual inspection.
- [fontTools SVGPathPen](https://fonttools.readthedocs.io/en/latest/pens/svgPathPen.html) and [uharfbuzz](https://github.com/harfbuzz/uharfbuzz): shaping and stable glyph geometry.
