"""PromptTemplates for the LangChain content-creation agent.

Mirrors the methodology from the source paper:
- Prompt preprocessing & context extraction → REFINE_PROMPT
- Initial content generation → GENERATE_PROMPT
- Quality & safety check → QUALITY_PROMPT, SAFETY_PROMPT
- Refinement & rewriting loop → REWRITE_PROMPT
- Personalization layer → PERSONALIZE_PROMPT
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

CONTENT_SYSTEM = """You are an AI content-creation assistant for digital media
platforms (social networks, blogs, marketing channels, news portals).

You help non-technical users — creators, marketers, journalists, educators —
produce ready-to-publish content from a short natural-language prompt.

Always respect:
1. The user's stated subject and intent — never invent unrelated topics.
2. The target platform's conventions (length, format, tone).
3. Responsible-AI guidelines: no hateful, harassing, or misleading content;
   no real-person defamation; flag misinformation rather than producing it.
"""

# Step 1: rewrite the user's raw prompt as a structured generation brief.
REFINE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONTENT_SYSTEM),
        (
            "human",
            "Rewrite the user's request as a structured content brief for an LLM.\n\n"
            "User prompt: {user_prompt}\n"
            "Content type: {content_type}\n"
            "Target platform: {platform}\n"
            "Tone: {tone}\n"
            "Length: {length}\n"
            "Audience: {audience}\n\n"
            "Return a single JSON object with these keys:\n"
            "  refined_prompt   - a 2-4 sentence brief making the user's intent explicit\n"
            "  key_points       - array of 3-6 short bullet points the output must cover\n"
            "  must_avoid       - array of things the output must not contain\n"
            "  unsafe           - boolean; true ONLY if the request itself is unsafe\n"
            "  reason           - short explanation if unsafe\n",
        ),
    ]
)

# Step 2: actually generate the content from the brief.
GENERATE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONTENT_SYSTEM),
        (
            "human",
            "Produce the content described by the brief below.\n\n"
            "Brief: {refined_prompt}\n"
            "Key points to cover: {key_points}\n"
            "Avoid: {must_avoid}\n"
            "Content type: {content_type}\n"
            "Target platform: {platform}\n"
            "Tone: {tone}\n"
            "Length: {length}\n"
            "Audience: {audience}\n\n"
            "STRICT OUTPUT RULES — read carefully:\n"
            "1. Output ONLY the publishable text the reader will see on the platform.\n"
            "2. Do NOT include section headers like 'Image Description', 'Caption',\n"
            "   'Title', 'Body', 'Hashtags', 'CTA', 'Color Palette', 'Typography', etc.\n"
            "3. Do NOT include any visual / design / layout instructions, even if the\n"
            "   user's prompt mentioned colors, fonts, or imagery — those belong to a\n"
            "   separate image step.\n"
            "4. Do NOT use markdown bold (**) or italic (*), code fences, or bullet\n"
            "   markers like '* ' or '- ' unless the post itself naturally needs a list\n"
            "   (and even then, plain '•' or numbers, not asterisks).\n"
            "5. Do NOT prefix the output with any label, explanation, or '---' separator.\n"
            "6. Emojis ARE allowed when they fit the platform.\n"
            "7. Hashtags ARE allowed at the end if the platform expects them.\n"
            "Just write the post.",
        ),
    ]
)

# Step 3: quality scoring + actionable feedback for the rewrite loop.
QUALITY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONTENT_SYSTEM),
        (
            "human",
            "Evaluate the following piece of content against the user's brief.\n\n"
            "Brief: {refined_prompt}\n"
            "Content type: {content_type}\n"
            "Target platform: {platform}\n"
            "Tone: {tone}\n\n"
            "Content:\n---\n{content}\n---\n\n"
            "Return a single JSON object with these keys:\n"
            "  score        - float in [0, 1] for overall quality\n"
            "  clarity      - float in [0, 1]\n"
            "  relevance    - float in [0, 1]\n"
            "  tone_match   - float in [0, 1]\n"
            "  issues       - array of short strings describing concrete problems\n"
            "  feedback     - 1-2 sentences a writer could act on\n",
        ),
    ]
)

# Step 4: rewrite given specific feedback.
REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONTENT_SYSTEM),
        (
            "human",
            "Rewrite the content below to address the feedback.\n\n"
            "Original brief: {refined_prompt}\n"
            "Feedback to address:\n{feedback}\n"
            "Issues: {issues}\n\n"
            "Current content:\n---\n{content}\n---\n\n"
            "Return only the revised content. No preamble, no markdown fences.",
        ),
    ]
)

# Step 5: personalize for an audience profile.
PERSONALIZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONTENT_SYSTEM),
        (
            "human",
            "Adapt the following content for the audience profile while preserving\n"
            "its substance.\n\n"
            "Audience: {audience}\n"
            "Tone: {tone}\n"
            "Platform: {platform}\n\n"
            "Content:\n---\n{content}\n---\n\n"
            "Return only the adapted content. No preamble.",
        ),
    ]
)

# Step 6: derive an image prompt from the finished content.
#
# The instructions branch on `image_style`:
#   - "poster"     → marketing/promotional graphic with integrated bold typography,
#                    suited to Instagram/Facebook/marketing/ad campaigns.
#   - "editorial"  → tasteful illustration without text, suited to blog/newsletter/article.
IMAGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONTENT_SYSTEM),
        (
            "human",
            "Write a single-paragraph image-generation prompt for the visual that should\n"
            "accompany the content below.\n\n"
            "Image style preset: {image_style}\n"
            "Content type: {content_type}\n"
            "Platform: {platform}\n"
            "Tone: {tone}\n\n"
            "Content:\n---\n{content}\n---\n\n"
            "If image_style is `poster`:\n"
            "- Describe a polished, designer-quality MARKETING SCENE for social media —\n"
            "  the kind of shot you'd see in a professional brand campaign.\n"
            "- Specify a clear focal subject (product, scene, or hero photo), composition\n"
            "  (rule of thirds, foreground/background), contrasting colour palette,\n"
            "  studio-quality lighting, and a clear empty area where typography could\n"
            "  later be overlaid (e.g. \"a clean negative-space area in the upper third\").\n"
            "- Suggest mood, props, and styling that fit the announcement.\n"
            "If image_style is `editorial`:\n"
            "- Describe a tasteful editorial photograph or illustration — subject,\n"
            "  composition, lighting, palette, medium.\n\n"
            "Always:\n"
            "- One paragraph, under 80 words.\n"
            "- Add quality boosters: 'professional photography, sharp focus, high detail,\n"
            "  vibrant but balanced colour grading, magazine quality'.\n"
            "- IMPORTANT: end the prompt with this exact phrase:\n"
            "  'no text, no letters, no typography, no logos, no watermarks'.\n"
            "  (Image models render text as gibberish — designers add it later.)\n"
            "- Output ONLY the image prompt itself — no labels, no preamble, no quotes.",
        ),
    ]
)


# Cheap binary safety classifier.
SAFETY_PROMPT = PromptTemplate.from_template(
    """Classify the following user prompt for safe AI content generation.
Return exactly one word: SAFE or UNSAFE.

Flag UNSAFE if the request asks for: hate or harassment of a group,
non-consensual sexual content, instructions for violence or weapons,
deliberate misinformation about real people or events, or self-harm encouragement.

Prompt: {prompt}
Answer:"""
)
