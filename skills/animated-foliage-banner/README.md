# Animated Foliage Banner

English | [简体中文](README.zh-cn.md)

This skill helps an AI agent make SVG banners with moving plants or fur. Use it to animate artwork you already have, create a banner from a description, or check an existing animation.

It covers the practical work of assembling layers and adding motion: leaves and tufts can sway while their roots stay in place, with related shadows, masks, and clips following along. The finished banner can include its assets in a single SVG file, ready to display as an image in places such as a GitHub README.

## Start with what you have

An existing SVG, a flat image, a PSD, or a description can all be starting points. With a PSD, the agent can inspect available layers and masks. With a flat image, the moving parts need to be extracted or rebuilt; the scripts do not automatically separate an arbitrary picture into layers. With no assets, the agent can create an original scene from your brief.

The look of the banner comes from your references and preferences. You can also leave the composition, colors, and other design choices to the agent. The skill provides production methods, with no prescribed visual style or layout.

## Ask your agent

Once the skill is available to your agent, ask it to use `animated-foliage-banner`. Tell it the banner size, where you plan to display it, any text to include, and what should move. Attach reference artwork if you have it, and say which details need to stay the same.

For example:

> Use animated-foliage-banner to make a 1600×400 SVG banner for a GitHub README. The title is “Field Notes”. Keep the text still and let the surrounding plants sway continuously. I have no artwork, so choose the composition and colors. Show a still image when reduced motion is enabled.

During production, the agent can capture the animation at specific times, compare it with a reference, and check continuous playback and reduced-motion behavior. These checks help find problems, but visual quality and fidelity still need to be judged by looking at the result. Loading and playback performance need testing where the banner will actually be displayed.

## Further reading

- [Skill instructions](SKILL.md) — the workflow for your agent.
- [Production guide](references/production.md) — how to assemble and animate the artwork.
- [Inspection guide](references/inspection.md) — how to inspect sources and check the result.

The reusable skill is distributed under the [MIT License](LICENSE).
