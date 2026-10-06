# Banner production references

Useful primary sources and reusable production techniques for animated foliage artwork. A citation explains a method; it does not establish that an output implements or passes every recommendation. Execution records and private source details are kept outside public documentation.

## Wind and anchored deformation

| Source | Useful idea | Application and boundary |
| --- | --- | --- |
| [Tiago Sousa, GPU Gems 3, Chapter 16: Vegetation Procedural Animation and Shading in Crysis](https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-16-vegetation-procedural-animation-and-shading-crysis) | Separate large-scale bending from leaf detail; vary stiffness and phase; combine smooth periodic signals. The chapter also discusses applying detail bending to hair. | Adapt stiffness and phase to local two-dimensional motion. Authored SVG deformation is an approximation, not this GPU shader or a physical simulation. |
| [Renaldas Zioma, GPU Gems 3, Chapter 6: GPU-Generated Procedural Wind Animations for Trees](https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-6-gpu-generated-procedural-wind-animations-trees) | A shared wind field can drive different branch responses through approximate periodic motion. | Supports a coherent wind direction with spatial phase differences instead of unrelated random movements. |
| [AMD TressFX simulation source](https://github.com/GPUOpen-Effects/TressFX/blob/master/src/Shaders/TressFXSimulation.hlsl) and [TressFX 4.x developer guide](https://raw.githubusercontent.com/GPUOpen-Effects/TressFX/master/doc/TressFX4xDeveloperGuide.pdf) | Hair simulation distinguishes constrained particles, local shape preservation, and freely moving portions. | Reference for keeping roots attached while allowing more movement toward tips. No TressFX runtime or solver is included in the SVG. |
| [GPU Gems, Chapter 7: Rendering Countless Blades of Waving Grass](https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-7-rendering-countless-blades-waving-grass) | Efficient repeated vegetation and differentiated motion. | Supplemental research for lightweight motion; not a prescription to translate the entire banner. |
| [GPU Gems 2, Chapter 1: Toward Photorealism in Virtual Botany](https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-1-toward-photorealism-virtual-botany) and [GPU Gems 3, Chapter 4: Next-Generation SpeedTree Rendering](https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-4-next-generation-speedtree-rendering) | Hierarchical vegetation and controllable visual detail. | Supporting concepts; two-dimensional textured work does not require adopting a three-dimensional rendering system. |

Fixed roots are an attachment and stiffness constraint. They should not be explained as a universal claim that a leaf's root is its heaviest part. A two-dimensional rotation around a stationary stem already produces larger displacement farther from the pivot; additional bending should preserve that attachment.

## SVG geometry, animation, and compositing

| Source | Production use |
| --- | --- |
| [W3C SVG 2: Paths](https://www.w3.org/TR/SVG2/paths.html) | Morph poses must retain compatible path-command structure. Preserve vertex identity across poses instead of tracing each frame independently. |
| [Python ElementTree and TreeBuilder](https://github.com/python/cpython/blob/main/Doc/library/xml.etree.elementtree.rst) | Default parsing discards comments and processing instructions. An editable SVG refresh must retain author notes, including nodes outside the root, or reject unsupported constructs before replacing the source. |
| [W3C SVG 1.1: Animation](https://www.w3.org/TR/SVG11/animate.html) | Declarative animation timing and interpolation. Indefinite repetition does not itself guarantee a smooth seam. |
| [MDN: keySplines](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/keySplines) and [repeatCount](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/repeatCount) | Timing-curve and repetition syntax consulted through Context7. Check that the selected interpolation mode actually uses the supplied timing attributes. |
| [MDN: clipPathUnits](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/clipPathUnits), [clipPath](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/clipPath), and [mask](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/mask) | Keep source-space coordinates explicit. Distinguish alpha clipping, luminance masking, and the artwork painted beneath either one. |
| [MDN: feComposite](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feComposite) and [feGaussianBlur](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feGaussianBlur) | Construct an inner shadow from the moving contour's alpha instead of baking it into leaf colors. Limit filter bounds and verify the blur at the final display scale. |
| [MDN: feDisplacementMap](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDisplacementMap) | Distortion alternative. A full-frame displacement filter does not by itself preserve leaf attachment points; evaluate both fidelity and rendering cost. |
| [MDN: SVG as an image](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image) | An SVG loaded through an image element has different restrictions from an inline SVG document. Test the actual embedding mode and keep resources self-contained. |
| [MDN: prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion) | CSS and SMIL need separate attention; turning off CSS leaf animations alone does not stop an animated path. Verify the entire reduced-motion presentation. |
| [MDN: display in SVG](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/display) | Select static or animated `use` elements inside the clip, mask, and shadow. An element with `display: none` does not contribute to clip geometry; hiding the animation element itself does not stop SMIL. |
| [MDN: getComputedStyle](https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle) | Inspect the resolved display, visibility, and opacity of the contour references after CSS and media rules apply. Confirm visible output separately; a referenced definition can animate while its rendered uses select a static fallback. |
| [Playwright browser launch](https://playwright.dev/docs/api/class-browsertype#browser-type-launch), [media emulation](https://playwright.dev/docs/api/class-page#page-emulate-media), and [screenshots](https://playwright.dev/docs/api/class-locator#locator-screenshot) | Local browser validation with an existing Chrome installation. Use an independent image-mode control to verify that a preference reaches the embedded SVG. |
| [MDN: SVGSVGElement](https://developer.mozilla.org/en-US/docs/Web/API/SVGSVGElement) and [Animation.pause()](https://developer.mozilla.org/en-US/docs/Web/API/Animation/pause) | Freeze the SMIL clock with `pauseAnimations()`/`setCurrentTime()` and CSS animations through the Web Animations API for fixed-time diagnostic renders. Direct SVG screenshots must also set the actual rendered size; a viewport alone does not override intrinsic SVG dimensions. |
| [MDN: SVGAnimationElement.getSimpleDuration()](https://developer.mozilla.org/en-US/docs/Web/API/SVGAnimationElement/getSimpleDuration) | Read a declared animation's simple duration in seconds to select proportional sample times. Reject undefined or non-finite timing. |
| [GitHub: images and relative links](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#images) | Reference a repository image directly by a relative path from the README. Keep one real asset and avoid making Profile rendering depend on symbolic-link resolution. |
| [Git: core.symlinks](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coresymlinks) and [a public symbolic-link Raw response](https://raw.githubusercontent.com/git/git/master/RelNotes) | Git can check out symbolic links as small text files when `core.symlinks` is false. The inspected Raw response contains a target path rather than target contents; a repository link is not a portable image-serving alias. |

A silhouette-shaped background mask and an inner shadow can be distinct effects. Inspect their actual compositing roles. Drive both from shared geometry where appropriate, while keeping their colors out of extracted leaf sprites.

Canvas cropping is not a physical silhouette edge. Extend a shared contour beyond a touched canvas boundary far enough to cover mask offsets and filter support; preserve its in-view shape and keep added closure vertices fixed across all poses. Check the last visible rows in both animated and static presentations.

Inspect text-layer effects and parent-group effects separately. A parent shadow operates on the layer's composed appearance, whereas a layer shadow can use the bare glyph alpha. Apply canvas-pixel shadow offsets outside glyph scaling, and avoid adding a parent effect twice when a native export already contains it. [MDN's drop-shadow reference](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDropShadow) describes the equivalent alpha, blur, offset, color, and merge operations.

## PSD inspection and native rendering

| Source | Production use and limitation |
| --- | --- |
| [psd-tools overview](https://psd-tools.readthedocs.io/en/latest/index.html) and [usage guide](https://psd-tools.readthedocs.io/en/latest/usage.html) | Read the document hierarchy, cached pixels, and source metadata. Treat cached merged pixels and newly composited layers as different evidence. |
| [psd-tools layer API](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.layers.html) | Inspect bounding boxes, visibility, clipping relationships, blend modes, masks, type layers, and raw pixel export. |
| [psd-tools PSD image API](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.psd_image.html) and [Pillow decoding implementation](https://psd-tools.readthedocs.io/en/latest/_modules/psd_tools/api/pil_io.html) | Both document and layer `topil()` default to applying ICC conversion. Use `apply_icc=False` for decoded channel diagnostics and disclose that source ICC metadata is not copied. This does not bypass the decoder's bit-depth reduction or cached-preview alpha handling. |
| [psd-tools effects API](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.effects.html) | Read actual shadow and glow descriptors, including enabled state, color, opacity, size, distance, angle, and global-light behavior. |
| [psd-tools compositor](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.composite.html) | Understand the reconstruction path. Rendering coverage depends on the installed version, optional dependencies, and the PSD's features; metadata access does not establish native Photoshop fidelity. Dissolve and complex styles require particular care. |
| [Adobe Photoshop scripting](https://helpx.adobe.com/photoshop/using/scripting.html), [Photoshop scripting guide](https://www.adobe.com/content/dam/acom/en/devnet/photoshop/pdfs/photoshop-cc-scripting-guide-2019.pdf), and [JavaScript reference](https://www.adobe.com/content/dam/acom/en/devnet/photoshop/pdfs/photoshop-cc-javascript-ref-2019.pdf) | Native layer visibility, document copies, PNG export, and document cleanup. These historical ExtendScript references are not interchangeable with the newer UXP API. |
| [Adobe PNGSaveOptions for UXP](https://developer.adobe.com/photoshop/uxp/2022/ps-reference/objects/saveoptions/pngsaveoptions) | A consulted alternative API reference. Do not copy its calls into an ExtendScript/COM workflow without adaptation. |

Use `psd-tools` for inspection and, when available, Photoshop for native style exports where comparisons show a mismatch. Export from a byte-for-byte copy and verify that the source remains unchanged. A native editor and layered source are optional in the reusable skill; flat-image reconstruction must identify inferred content and effects.

Use the evidence actually supplied. A flattened PNG cannot establish editable layer relationships, while an available layered source may resolve them. Keep private source paths and per-work metadata out of public examples.

## Typography and font provenance

| Source | Role |
| --- | --- |
| [fontTools SVGPathPen](https://fonttools.readthedocs.io/en/latest/pens/svgPathPen.html), [TransformPen](https://fonttools.readthedocs.io/en/latest/pens/transformPen.html), and [TTFont](https://fonttools.readthedocs.io/en/latest/ttLib/ttFont.html) | Convert positioned glyph outlines into stable SVG geometry and apply the intended text transform. Outlining alone does not perform text shaping. |
| [uharfbuzz](https://github.com/harfbuzz/uharfbuzz) | Shape text with glyph advances, offsets, kerning, and ligatures before exporting outlines where needed. |

Record each chosen font's upstream source, actual file/version, and applicable license in the work's own record. Shape before outlining; retain a suitable native render when effects require it. Font software redistribution and rendered artwork are distinct deliverables. Do not infer permissions from a typeface name or publish a user's font-selection history as generic guidance.

## Texture extraction and evaluated alternatives

| Source | Production use and lesson |
| --- | --- |
| [OpenCV inpainting](https://docs.opencv.org/4.13.0/d7/d8b/group__photo__inpaint.html) | Remove an extracted moving leaf from its static backing texture to avoid a second stationary copy. Inspect exposed regions at motion extremes: inpainting can leave visible smears. |
| [OpenCV distance transform](https://docs.opencv.org/4.13.0/d2/dbd/tutorial_distance_transform.html) and [image filtering](https://docs.opencv.org/4.13.0/d4/d86/group__imgproc__filter.html) | Alpha-edge extension, mask morphology, and blur fitting. Extend from a clean unmasked color field; extending a contaminated crop can spread the wrong background color into moving edges. |
| [VTracer](https://github.com/visioncortex/vtracer/blob/master/README.md) | A tracing route for suitable shapes. Compare geometry size and visual fidelity with embedded textures; dense grain can become excessive path geometry. |

## Reusable production decisions

- Keep clean color fields, masks, and effects separate. Palette-specific contamination thresholds belong to the work's own checks.
- For an effect stack verified to obey `C(B) = K + B*T`, black/white-backdrop decomposition can encode Multiply `M = T/(1-K)` followed by Screen `K`. Handle channels where `K = 1` and verify intermediate backdrops before assuming this affine model applies.
- Fit shadow width, offset, and softness against rendered evidence. Photoshop effect size is not automatically an SVG Gaussian deviation.
- Choose pose density against displayed smoothness and payload size; positional loop closure does not prove continuous velocity.
- Validate actual image embedding, fixed animation times, isolated layers, and reduced motion. Compare performance under equivalent viewport, visibility, and hardware conditions; finite local checks do not prove hosted or cross-device behavior.

The [assembly workflow](banner-build.md) and bundled neutral example describe reusable inputs and verification. Retain each work's authoring recipe without publishing private source material as a prerequisite for using the skill.

## Skill authoring and maintenance

Python helper commands use `-B` to suppress bytecode writes when importing modules. It does not remove existing caches, so verify the actual skill distribution separately from Git ignore rules. The [Python command-line reference](https://github.com/python/cpython/blob/main/Doc/using/cmdline.rst) documents `-B`, its `PYTHONDONTWRITEBYTECODE` equivalent, and the alternative `PYTHONPYCACHEPREFIX` location; no global interpreter setting is required.

| Source | Adopted guidance and boundary |
| --- | --- |
| [OpenAI: Build skills](https://developers.openai.com/codex/build-skills) | Keep a precise trigger and one coherent job. Use scripts for deterministic operations or external tooling, with explicit inputs and outputs. |
| [OpenAI: Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | Keep the entry point a small router; load conditional detail only when needed. Avoid turning accumulated fixes into an elaborate mandatory itinerary. |
| [Agent Skills: Best practices for skill creators](https://agentskills.io/skill-creation/best-practices) | Moderate detail, working examples, and clear conditions for reading references. Size guidance is a ceiling, not a target to fill. |
| [Community discussion: I was wrong about Agent Skills and how I refactor them](https://www.reddit.com/r/ClaudeAI/comments/1opxgq4/i_was_wrong_about_agent_skills_and_how_i_refactor/) | A practitioner reports reducing unnecessary initial context through references and cold-start testing. Treat the reported gains and strict 200-line rule as anecdotal, not a specification or a guaranteed outcome. |

Apply these principles by separating routing, authoring decisions, executable diagnostics, and neutral inputs. Keep each command's dependency, units, output, and failure guidance beside its usage. Validate the documented path from an independently installed copy; do not make every task load every reference or run every check. Keep private work records and temporary outputs outside the package.
