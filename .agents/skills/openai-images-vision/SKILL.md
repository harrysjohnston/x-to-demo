---
name: openai-images-vision
description: "Implement OpenAI image generation, image editing, and vision/image-input analysis. Use when building with the OpenAI Responses API or Images API for: analyzing one or more images, sending image URLs/base64 data URLs/file IDs, choosing between Responses and Images APIs, tuning image detail and output options, validating image input requirements, or handling known vision limitations."
---

# OpenAI Images and Vision

Implement OpenAI image generation and image-understanding flows without re-deriving request shape each time. Treat this skill as stable workflow guidance, then re-check current OpenAI docs for unstable details such as exact model support, pricing, and newly added parameters.

## Choose The API First

- Use the **Responses API** for multimodal prompts that mix text and image input, compare multiple images, or need conversational or structured-output behavior.
- Use the **Images API** for focused image generation, editing, or variation flows where image-specific controls are the primary concern.
- Use **Chat Completions** only for legacy compatibility. Prefer the Responses API for new work.

## Build Vision Flows

1. Choose the image transport:
   - Hosted URL when the server already has a stable image URL
   - Data URL when the image originates locally and must be inlined
   - `file_id` when the image is already uploaded or should be reused across requests
2. Start with `detail: auto` when supported by the target surface.
3. Raise detail only when the task needs it:
   - OCR, screenshots, dense documents, tiny labels, handwriting, or low-contrast scans
   - Keep cost and latency in mind before forcing higher detail
4. Send all relevant images in one request when comparison or cross-image reasoning matters.
5. Ask for the exact output shape you need. For extraction tasks, prefer structured output and explicit uncertainty handling over free-form captions.
6. Validate file type, count, and payload size on the server before calling OpenAI.

## Build Image Generation And Editing Flows

1. Default to the Images API when the product flow is a single prompt producing or editing a single image.
2. Expose output controls only when they materially affect UX:
   - `size`
   - `quality`
   - `format`
   - `compression`
   - `background`
   - moderation level
3. Keep defaults lean when the user does not need visual tuning controls.
4. Handle partial-image streaming only when the UX benefits from progressive rendering; otherwise wait for the final image.

## Handle Limits And Failure Modes Up Front

- Reject unsupported file types before upload.
- Reject requests that exceed image-count or payload-size limits before hitting the API.
- Do not send CAPTCHAs to vision models.
- Surface limitations in product logic when precision matters:
  - counts may be approximate
  - rotated text can fail
  - graphs and styled lines can confuse the model
  - panoramic or fisheye images can degrade results
  - specialized medical images are not a valid use case

## Coordinate With Other Skills

- Use `multimodal-inputs` when you touch upload, camera, or image preview UI.
- Use `demo-e2e` when you need this repo's baseline demo guidance for generated-media labeling or shared OpenAI config conventions.

## Read The Reference

Open [references/official-guide.md](references/official-guide.md) when you need:

- image input requirements
- API-selection rules
- detail and transport guidance
- output option summaries
- known limitations and implementation cautions
