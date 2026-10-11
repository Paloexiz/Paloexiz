---
name: animated-foliage-banner
description: Technical production and validation for SVG banners containing anchored foliage or fur motion, from supplied artwork or an original brief. Use for animation, compositing, self-contained image delivery, and verification. Not an aesthetic guide or a general banner template; layered sources are optional.
license: MIT
---

# Animated Foliage Banner

This skill supplies technical methods. The brief or supplied artwork determines subject, composition, palette, typography, texture, and effects. For reproduction, preserve observed visual features and identify approximations. For original work, make those creative decisions independently; the example and script contracts are test inputs, not design targets.

## Workflow

1. **Choose the input route.** Use the matching [route](references/production.md#input-routes), including an original brief with no assets. Ask only for missing information that materially changes the result. Record what is supplied, inferred, or newly authored.
2. **Implement the chosen scene.** Read [layer assembly](references/production.md#layer-assembly) when separating extracted pixels, masks, or effects. Build only the components present in the work. For extracted moving leaves, remove stationary duplicates and fill their swept areas.
3. **Anchor the motion that needs attachment.** Identify actual stem and tuft roots, then vary movement toward the tips. Related clips, masks, and shadows must follow the same geometry. The [polygon helper and scene contract](references/production.md#motion-and-the-optional-fur-helper) apply only to compatible geometry; choose another implementation when they constrain the intended shape.
4. **Compare the rendered result.** Use the [inspection tools](references/inspection.md) for the observed question. Check relevant motion extremes, effects, coverage, and text against the brief or reference. Technical passes do not establish visual quality; review that separately.
5. **Verify the intended embedding and deliver.** Keep image-mode SVGs self-contained. Use [scene-contract checks](references/production.md#scene-contract-checks) only for that contract; otherwise adapt verification to the authored scene. Continuous motion and [reduced-motion output](references/production.md#reduced-motion-and-image-host-constraints) must satisfy the brief and cover every visible animation. Report exactly what was tested and what remains uncertain.

## Choose a tool

Commands, dependencies, output interpretation, and recovery steps are in the linked guides. Run scripts from this skill directory, or use its absolute path from another workspace. Use `python -B`, including for ad-hoc checks that import helpers, to prevent bytecode writes into the package; see [package hygiene](references/inspection.md#checks-and-retention) when validating or distributing the skill.

| Need | Tool | Read when needed |
| --- | --- | --- |
| Inspect an available PSD's hierarchy, effects, cached pixels, or masks | [inspect_psd.py](scripts/inspect_psd.py) | [Optional PSD inspection](references/inspection.md#optional-psd-inspection) |
| Freeze a self-contained SVG at a known time; crop or enlarge a detail | [render_svg.cjs](scripts/render_svg.cjs) | [Fixed-time rendering](references/inspection.md#fixed-time-rendering) |
| Quantify a same-size reference/candidate difference | [compare_images.py](scripts/compare_images.py) | [Raster comparison](references/inspection.md#raster-comparison) |
| Generate poses from an authored polygon rig | [build_fur_poses.py](scripts/build_fur_poses.py) | [Rig inputs](references/production.md#motion-and-the-optional-fur-helper) |
| Assemble authored scene and motion files | [build_banner.py](scripts/build_banner.py) | [Scene contract and example](references/production.md#scene-contract-and-minimal-example) |
| Check a scene-contract SVG's geometry or actual playback | [check_fur_motion.py](scripts/check_fur_motion.py), [check_banner_browser.cjs](scripts/check_banner_browser.cjs) | [Check coverage](references/production.md#scene-contract-checks) |

## Keep the package reusable

- `references/production.md` holds authoring decisions and the scene contract. `references/inspection.md` holds runnable diagnostic workflows. Load only the section needed for the task.
- `scripts/` holds reusable operations; keep the directory together because scripts import adjacent helpers. `examples/minimal/` supplies neutral scene and motion inputs that work without a PSD, fonts, or private artwork.
- Retain each work's [authoring recipe](references/production.md#checks-for-each-work) in durable storage. Private paths, source images, layer inventories, font choices, and per-work thresholds stay outside the distributed skill.
- Preserve copyright notices in distributed licenses; anonymizing examples does not authorize changing attribution.
- Before cleaning disposable previews, retain reusable code here and work-specific inputs with their authoring recipe. Promote a temporary helper only when repeated use or a concrete validation need justifies it; document inputs, outputs, dependencies, and limits alongside the command.

The scripts do not segment arbitrary pictures, recover missing original layers, certify visual fidelity, or establish hosted performance. If a tool is unavailable, continue the independent authoring work and state the specific unverified step.
