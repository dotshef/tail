---
name: tail-image
description: Tail Story Pipeline image workflow. Use when planning, generating, or reviewing `tail-image/` assets from `tail-raw/*.md`, including `theme.yaml`, `prompts.json`, cover images, cut images, image prompt design, image generation handoff, and image QC for Tail story books.
---

# Tail Image

## Purpose

Use this as the single entry point for Tail story image work. The workflow converts `tail-raw/{story}.md` into a complete `tail-image/{story}/` package for the existing bookform and PDF pipeline.

Do not read `img-reference/` during normal runs. The house style below is the fixed extraction from those references. Reopen `img-reference/` only when the user explicitly asks to revise the style.

## Output Contract

Create or verify this exact structure:

```text
tail-image/{story}/
  theme.yaml
  prompts.json
  cover.png
  cuts/
    컷1.jpeg
    컷2.jpeg
    ...
```

The cut count must exactly match the `**[컷 N] ...**` markers in `tail-raw/{story}.md`. Keep Korean filenames such as `컷1.jpeg`; the PDF/bookform pipeline already expects this convention.

## Fixed Style

Use this style prompt for every story and every cut:

```text
classic vintage children's storybook illustration, mid-century fairy tale book art, gouache and watercolor texture, visible painterly brush strokes, subtle pencil underdrawing, warm cream paper grain, slightly aged printed-book colors, expressive rounded characters, soft rosy faces, clear emotional poses, rich hand-painted backgrounds, bold but natural composition, warm nostalgic atmosphere, no text, no letters, no captions, no speech bubbles, no watermark
```

Use this negative style:

```text
photorealistic, 3d render, anime, manga, comic panel, flat vector, plastic texture, glossy digital art, overly modern clothing, neon colors, dark horror mood, text, letters, captions, speech bubbles, logo, watermark, signature
```

## Workflow

For a full image task, use the role sequence below. Spawn subagents only when the user asks for subagents, parallel agents, or a full delegated workflow. For small planning-only requests, do the planner work locally.

1. `tail_image_planner`
   - Read `tail-raw/{story}.md`.
   - Extract title, chapters, pages, cut numbers, cut labels, and page text.
   - Create a character bible and setting bible for the story.
   - Write `tail-image/{story}/theme.yaml`.
   - Write `tail-image/{story}/prompts.json`.
   - Do not generate images.

2. `tail_image_generator`
   - Read `tail-image/{story}/prompts.json`.
   - Generate `cover.png` and all `cuts/컷N.jpeg`.
   - Preserve prompt semantics and output filenames.
   - If image generation is unavailable, report the exact files that must be generated and do not fabricate placeholders.

3. `tail_image_qc`
   - Verify file existence, cut count, image readability, and path conventions.
   - Review style consistency against the fixed style prompt.
   - Flag text, captions, speech bubbles, logos, watermarks, horror tone, modern digital style, or character drift.
   - Return a concise regeneration list by cut number.

## `prompts.json` Shape

Match the existing `tail-image/여우와 두루미/prompts.json` pattern:

```json
{
  "story": "이야기 제목",
  "style_hint": "fixed style prompt plus story-specific notes",
  "negative_prompt": "fixed negative style",
  "characters": {
    "캐릭터": "stable visual description"
  },
  "aspect_ratio": "4:3",
  "cover": {
    "prompt": "cover scene prompt",
    "mood": "cover mood",
    "key_details": ["detail"]
  },
  "cuts": [
    {
      "cut": 1,
      "scene_label": "컷 설명",
      "prompt": "image prompt with setting, action, emotion, composition",
      "mood": "scene mood",
      "key_details": ["detail"]
    }
  ]
}
```

If older files omit `negative_prompt` or `cover`, preserve compatibility but add them for new work.

## Planning Rules

- Derive scene content from the cut marker and the page body, not from memory of the folktale alone.
- Keep character descriptions stable across all cuts.
- Make each cut a single illustration, not a comic panel.
- Exclude visible text in the image even when the story contains dialogue.
- Prefer warm, readable, PDF-friendly compositions with clear foreground action.
- Keep potentially scary scenes child-friendly and non-graphic.
- Choose `theme.yaml` colors that harmonize with the generated cover and work on the PDF cover.

Example `theme.yaml`:

```yaml
# Per-book theme for {story}
# primary: cover decoration color (line, title accents)
# background: cover background color
primary: "#8B0000"
background: "#FAF3E0"
```
