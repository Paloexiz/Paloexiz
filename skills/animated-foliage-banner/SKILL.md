---
name: animated-foliage-banner
description: Create or refine textured SVG banners with anchored leaf or fur motion and stationary lettering. Use when reproducing this style from an image or correcting its animation, masks, or shadows. Layered sources are optional.
license: MIT
---

# Animated Foliage Banner

Preserve the supplied artwork's composition, grain, leaf shapes, silhouette, and lettering while adding attached local motion. Adapt to the actual subject and palette; do not assume a particular identity, font, layer stack, or canvas size.

## Workflow

1. **Inspect the available input.** A flat PNG/JPG is sufficient. Use the matching [input route](references/production.md#input-routes); read the layered-source route only when one is supplied. Ask only for missing information that materially changes the result. Identify inferred hidden pixels, substituted fonts, and estimated effects.
2. **Separate paint from geometry.** Keep clean color fields, leaf alpha, silhouette masks, background shadows, inner shadows, and lettering effects distinct. Remove a moving leaf's stationary duplicate and fill its swept area. Follow [layer assembly](references/production.md#layer-assembly) when authoring masks or effects.
3. **Anchor motion.** Keep each stem and tuft root fixed; increase movement toward tips. Include small visible tufts. Share wind timing across the artwork and shared contour geometry across related clips, masks, and shadows. Use the [polygon helper and scene contract](references/production.md#motion-and-the-optional-fur-helper) only for compatible authored geometry.
4. **Compare the rendered result.** Use the [inspection tools](references/inspection.md) for source inventory, fixed-time crops, and image differences. Choose the check that answers the observed question; do not run every tool for every edit. Preserve stationary lettering and compare shadow scope, softness, crop coverage, and exposed texture at motion extremes.
5. **Verify the intended embedding and deliver.** Keep image-mode SVGs self-contained. When using the bundled scene contract, run its [structural and browser checks](references/production.md#scene-contract-checks). Default motion remains continuous when requested; the [reduced-motion presentation](references/production.md#reduced-motion-and-image-host-constraints) must cover CSS foliage and all SMIL-driven contour uses. Report the tested host and any approximations.

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
