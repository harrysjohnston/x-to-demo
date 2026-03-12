# OpenAI Images and Vision Reference

Source pages:

- `https://developers.openai.com/api/docs/guides/images-vision/`
- `https://developers.openai.com/api/docs/guides/image-generation/`
- `https://developers.openai.com/api/reference/resources/images/methods/generate/`
- `https://developers.openai.com/api/reference/resources/images/methods/edit/`

Use MCP OpenAI docs tools to re-check current model support, pricing, and endpoint-specific parameter changes before shipping.

## API Selection

### Responses API

Use for:

- mixed text + image prompts
- analyzing one or more images
- comparing multiple images in one request
- conversational image workflows
- structured output from image understanding

### Images API

Use for:

- single-purpose image generation
- single-purpose image editing
- image variation flows
- image-specific option tuning where the payload should stay focused on generation/edit parameters

From the OpenAI image generation guide: if the product only needs to generate or edit a single image from one prompt, the Images API is the best fit; conversational or editable image experiences fit the Responses API better.

## Vision Input Methods

Prefer one of these transports:

- Hosted URL: best when the backend already has a durable or signed URL
- Data URL: best when the image starts as local bytes and must be sent inline
- `file_id`: best when the same uploaded image will be reused or referenced later

For image editing endpoints that accept image references, provide either `image_url` or `file_id` per image reference, not both.

## Image Input Requirements

OpenAI documents these supported image input types:

- PNG (`.png`)
- JPEG (`.jpeg`, `.jpg`)
- WEBP (`.webp`)
- non-animated GIF (`.gif`)

Documented request limits for image analysis:

- up to 50 MB total payload size per request
- up to 500 individual image inputs per request

Other documented requirements:

- no watermarks or logos
- no NSFW content
- image must be clear enough for a human to understand

## Detail Guidance

Default behavior:

- Start with `detail: auto` where supported.

Raise detail only when needed:

- small text
- dense documents
- screenshots with fine labels
- handwriting
- low-contrast scans

If OCR-like accuracy is still weak after prompt cleanup, raise image detail before adding more prompt complexity. Current OpenAI docs and cookbooks indicate that higher-detail modes such as `high` or `original` can help on dense pages, but support varies by API surface and model; verify before hardcoding.

## Multiple Images

When the task depends on comparison, chronology, or cross-image reasoning, pass all relevant images in one request and explicitly tell the model how to use them.

Examples:

- compare the defect in image A vs image B
- identify which screenshot contains the regression
- summarize what changed between two UI states

## Image Generation And Editing Options

The OpenAI image generation docs and API reference describe these common output controls:

- `size`
- `quality`
- `format`
- `compression`
- `background`
- moderation level

Useful details from the current docs:

- GPT image models support output formats such as `png`, `jpeg`, and `webp`.
- Transparent backgrounds require a transparency-capable format such as `png` or `webp`.
- GPT image models support `auto` quality selection, with explicit quality levels such as `low`, `medium`, and `high`.
- GPT image model outputs are base64-encoded image data.
- Older DALL-E models can return `url` or `b64_json`, and returned URLs are temporary.
- The generation endpoint allows `n` between 1 and 10, but DALL-E 3 only supports `n = 1`.
- GPT image generation/editing endpoints support streaming partial-image events when the product wants progressive rendering.
- GPT image editing currently allows up to 16 input images.

## Implementation Advice

For image understanding:

- ask for the exact fields you need
- require explicit uncertainty when the image is ambiguous
- prefer structured output for extraction, classification, and comparison tasks
- keep prompts concrete about which region, object, or image index matters

For image generation/editing:

- avoid exposing every tuning knob unless the user benefits from direct control
- keep server-side validation aligned with the formats the chosen endpoint accepts
- store or transform base64 outputs immediately if the rest of the app expects file URLs or blobs

## Known Vision Limitations

OpenAI documents the following limitations for vision-capable models:

- Specialized medical images are not suitable inputs for diagnosis or medical advice.
- Non-Latin text can perform worse than Latin-script text.
- Small text can be missed unless the image is enlarged or processed at higher detail.
- Rotated or upside-down text and images can be misread.
- Graphs, charts, and styled line differences can be misinterpreted.
- Precise spatial localization is weak.
- Descriptions and captions can still be wrong.
- Panoramic and fisheye images are harder to interpret.
- Original file names and metadata are not used.
- Images may be resized before analysis depending on size and detail settings.
- Object counts may be approximate.
- CAPTCHAs are blocked.

Plan product behavior around these limits instead of assuming prompt wording alone will remove them.

## Cost And Throughput

OpenAI notes that images are processed at the token level, so image analysis contributes to token-based rate limits such as TPM. Re-check current pricing and image-processing estimates in the official pricing tools before committing to a production architecture.
