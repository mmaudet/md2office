"""AST element classes for intermediate representation."""

from __future__ import annotations

from typing import Literal

import msgspec


class TextSpan(msgspec.Struct, frozen=True):
    """A span of text with inline formatting.

    TextSpan represents the smallest unit of formatted text in the AST. Multiple
    formatting flags can be combined on a single span, and spans are typically
    grouped into lists to form paragraph or heading content.

    Attributes:
        text: The raw text content of this span. May contain newlines for soft/hard
            breaks. Never None, but can be empty string for zero-width spans.
        bold: Apply bold formatting (Markdown: **text** or __text__). Can combine
            with italic, strikethrough, code, and link.
        italic: Apply italic formatting (Markdown: *text* or _text_). Can combine
            with bold, strikethrough, code, and link.
        code: Apply inline code formatting (Markdown: `text`). Renders with monospace
            font. Can combine with other flags, though typically appears alone except
            when inside a link.
        strikethrough: Apply strikethrough formatting (Markdown: ~~text~~). Can
            combine with bold, italic, code, and link.
        link: Optional hyperlink URL. When set, the text becomes clickable. Link
            formatting can combine with all other formatting flags (bold, italic,
            code, strikethrough), allowing rich formatting of link text.

    Formatting Combination Rules:
        - All five formatting flags (bold, italic, code, strikethrough) can be
          combined in any combination on a single TextSpan.
        - The `link` field is orthogonal to text formatting - it specifies the
          hyperlink target and can be applied regardless of other formatting.
        - When multiple formatting flags are True, the renderer applies all of them
          cumulatively (e.g., bold + italic = bold italic text).
        - The most common combinations are:
            * bold + italic (***text***)
            * bold/italic with link (**[text](url)**)
            * code with link (`[code](url)`)

    Link and Code Interaction:
        - code=True with link="url" creates a clickable monospace span
        - The code flag affects visual rendering (font family, background)
        - The link flag affects behavior (hyperlink target)
        - These are independent: you can have code without link, link without code,
          or both together
        - Example Markdown: [`code link`](https://example.com) produces
          TextSpan(text="code link", code=True, link="https://example.com")

    Edge Cases:
        - Empty text (text=""): Valid, used for zero-width formatting boundaries
        - Newlines in text: Used for line breaks (linebreak and softbreak tokens)
        - link="" (empty string): Treated as no link (renderer may handle as None)
        - All flags False, link=None: Plain unformatted text
        - All flags True with link: Fully formatted hyperlink (rare but valid)

    Examples:
        Plain text:
            TextSpan(text="hello")

        Bold text:
            TextSpan(text="hello", bold=True)

        Bold italic text (Markdown: ***hello***):
            TextSpan(text="hello", bold=True, italic=True)

        Inline code (Markdown: `code`):
            TextSpan(text="code", code=True)

        Bold link (Markdown: **[text](url)**):
            TextSpan(text="text", bold=True, link="https://example.com")

        Code link (Markdown: [`code`](url)):
            TextSpan(text="code", code=True, link="https://example.com")

        Complex combination (bold + italic + strikethrough + link):
            TextSpan(
                text="fancy",
                bold=True,
                italic=True,
                strikethrough=True,
                link="https://example.com"
            )

    Usage:
        TextSpans are created by DocxRenderer during Markdown parsing and consumed
        by DocxBuilder when generating Word documents. They are immutable (frozen=True)
        and should not be modified after creation. To change formatting, create a new
        TextSpan with the desired attributes.
    """

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    strikethrough: bool = False
    link: str | None = None


class DocxElement(msgspec.Struct, frozen=True, tag=True):
    """Base class for all block-level elements in the DOCX AST.

    DocxElement is the root of the element hierarchy representing block-level
    Markdown constructs (paragraphs, headings, lists, tables, etc.). It uses
    msgspec's tagged union feature to enable efficient serialization and type-safe
    polymorphism across all element types.

    Tagged Union Architecture:
        The `tag=True` parameter enables msgspec tagged unions, which provide:
        - Type discrimination: Each subclass gets a unique tag field for runtime
          type identification (e.g., "heading", "paragraph", "table")
        - Efficient serialization: msgspec can serialize/deserialize the correct
          subclass based on the tag without custom logic
        - Type safety: Static type checkers can verify element types in lists
        - Pattern matching: Enables exhaustive type matching in Python 3.10+

        Subclasses specify their tag with `tag="name"`:
            class DocxHeading(DocxElement, frozen=True, tag="heading"):
                ...

        When serialized, elements include their tag:
            {"type": "heading", "level": 1, "content": [...]}

    Immutability:
        All elements are frozen (`frozen=True`), making them immutable after creation.
        This ensures:
        - Thread safety: Elements can be safely shared across threads
        - Hashability: Elements can be used as dict keys or in sets
        - Predictability: Once created, elements cannot be accidentally modified
        - Performance: msgspec optimizes frozen structs with __slots__

    Subclass Hierarchy:
        Block-level elements (inherit from DocxElement):
        - DocxHeading: H1-H6 headings with optional anchors
        - DocxParagraph: Text paragraphs with inline formatting
        - DocxCodeBlock: Fenced/indented code blocks with syntax highlighting
        - DocxBlockquote: Blockquotes containing nested elements
        - DocxList: Ordered/unordered lists with nested items
        - DocxTable: Tables with rows, cells, and formatting
        - DocxImage: Image references with alt text and titles
        - DocxHorizontalRule: Thematic breaks (---, ***, ___)
        - DocxAdmonition: Callout blocks (NOTE, WARNING, etc.)

        Helper structs (do NOT inherit from DocxElement):
        - TextSpan: Inline formatted text (not a block element)
        - DocxListItem: Individual list items (wrapped by DocxList)
        - DocxTableRow: Table rows (wrapped by DocxTable)
        - DocxTableCell: Table cells (wrapped by DocxTableRow)

    Usage in the Pipeline:
        1. DocxRenderer (parser/renderer.py) creates DocxElement instances from
           Markdown tokens during parsing
        2. Elements form an AST (Abstract Syntax Tree) representing document structure
        3. DocxBuilder (builder/docx_builder.py) consumes elements to generate
           Word documents using python-docx
        4. Elements can be serialized to JSON for caching or API responses

    Examples:
        Type discrimination in a list:
            elements: list[DocxElement] = [
                DocxHeading(level=1, content=[...]),
                DocxParagraph(content=[...]),
                DocxTable(rows=[...]),
            ]
            # msgspec knows each element's type from its tag

        Pattern matching (Python 3.10+):
            match element:
                case DocxHeading(level=1):
                    # Handle H1
                case DocxParagraph(content=spans):
                    # Handle paragraph
                case DocxTable(rows=rows):
                    # Handle table

        Serialization with msgspec:
            import msgspec
            elements = [DocxHeading(level=1, content=[...])]
            json_bytes = msgspec.json.encode(elements)
            decoded = msgspec.json.decode(json_bytes, type=list[DocxElement])
            # msgspec automatically deserializes to correct subclass

    Design Rationale:
        - msgspec over dataclasses: 10-100x faster serialization/deserialization
        - Tagged unions over manual type fields: Type-safe polymorphism
        - Frozen structs: Immutability prevents bugs and enables optimizations
        - No base fields: DocxElement is purely structural, subclasses define all data

    See Also:
        - TextSpan: Inline formatting elements (not block-level)
        - DocxRenderer: Creates DocxElement instances from Markdown
        - DocxBuilder: Consumes DocxElement instances to build Word documents
        - msgspec documentation: https://jcristharif.com/msgspec/structs.html#tagged-unions
    """

    pass


class DocxHeading(DocxElement, frozen=True, tag="heading"):
    """Heading element (H1-H6) with automatic anchor generation for internal linking.

    DocxHeading represents Markdown headings (# through ######) in the AST. Each heading
    has a level (1-6), formatted content (list of TextSpan objects), and an automatically
    generated anchor for internal cross-references. The anchor enables table of contents,
    cross-references, and internal navigation within Word documents.

    Attributes:
        level: Heading level from 1 (H1/#) to 6 (H6/######). Corresponds directly to
            the number of # symbols in Markdown. Level 1 is typically the document
            title, levels 2-3 are section headings, and levels 4-6 are subsections.
            Valid range: 1-6 inclusive. Values outside this range are not valid
            Markdown headings.
        content: List of TextSpan objects forming the heading text. Can include
            inline formatting (bold, italic, code, links, etc.). Multiple spans
            allow for mixed formatting within a single heading (e.g., "The **bold**
            title" would have 3 spans). Empty content is technically valid but
            uncommon in practice.
        anchor: URL-safe bookmark anchor automatically generated from the heading
            text by DocxRenderer._generate_anchor(). This field is ALWAYS populated
            for every heading during parsing - it is never None in practice, though
            the type signature allows None for backwards compatibility. The anchor
            follows GitHub-style slug generation rules: lowercase, spaces to hyphens,
            special characters removed, accents stripped. Used to create Word
            bookmarks that enable internal links (e.g., [See intro](#introduction)
            links to the heading with anchor "introduction").

    Anchor Generation:
        Anchors are automatically generated by DocxRenderer when parsing Markdown,
        following these rules (matching GitHub's anchor generation):
        - Extract plain text from all TextSpan content
        - Convert to lowercase
        - Replace spaces with hyphens
        - Remove special characters except hyphens and underscores
        - Strip accents from characters (é → e, ñ → n)

        Examples of anchor generation:
            "Introduction" → "introduction"
            "Getting Started" → "getting-started"
            "API Reference (v2.0)" → "api-reference-v20"
            "Café & Restaurant" → "cafe--restaurant"

        The anchor generation happens in DocxRenderer.heading() method, which calls
        _generate_anchor() with the concatenated text from all content spans.

    Internal Linking:
        The anchor field enables cross-references within the document via Word bookmarks:
        1. DocxRenderer generates anchor during parsing (renderer.py)
        2. DocxBuilder creates Word bookmark when building heading (docx_builder.py)
        3. Links with matching anchors (e.g., [text](#anchor)) become internal hyperlinks
        4. Word's navigation features (TOC, cross-references) use these bookmarks

        Example flow:
            Markdown: ## Getting Started
            Parsing: DocxHeading(level=2, content=[...], anchor="getting-started")
            Building: Creates Word bookmark named "getting-started" at heading paragraph
            Linking: [See here](#getting-started) → Word hyperlink to bookmark

        This enables features like:
        - Table of contents with clickable links
        - Cross-references between sections
        - Internal navigation in long documents
        - Consistent linking between Markdown and Word formats

    Level Semantics:
        - Level 1 (# heading): Document title or main heading
        - Level 2 (## heading): Major sections
        - Level 3 (### heading): Subsections
        - Level 4 (#### heading): Sub-subsections
        - Level 5 (##### heading): Detailed breakdowns
        - Level 6 (###### heading): Finest granularity

        Word styles typically map these to "Heading 1" through "Heading 6" styles,
        which control font size, weight, spacing, and outline level. The style
        mapping is configured in styles-mapping.yaml and applied by StyleMapper.

    Edge Cases:
        - Empty content (content=[]): Valid but renders as blank heading
        - Single span vs multiple spans: Both valid, depends on inline formatting
        - Duplicate anchors: Can occur if multiple headings have identical text;
          DocxBuilder handles this by using the same bookmark for all instances
        - anchor=None: Type allows None but DocxRenderer always sets it to a string
        - Special characters in text: Removed during anchor generation, so heading
          "C++ Programming" gets anchor "c-programming"

    Examples:
        Simple heading:
            DocxHeading(
                level=1,
                content=[TextSpan(text="Introduction")],
                anchor="introduction"
            )

        Heading with inline formatting (Markdown: ## The **Bold** Title):
            DocxHeading(
                level=2,
                content=[
                    TextSpan(text="The "),
                    TextSpan(text="Bold", bold=True),
                    TextSpan(text=" Title"),
                ],
                anchor="the-bold-title"
            )

        Heading with code and link (Markdown: ### Using `API` [docs](url)):
            DocxHeading(
                level=3,
                content=[
                    TextSpan(text="Using "),
                    TextSpan(text="API", code=True),
                    TextSpan(text=" "),
                    TextSpan(text="docs", link="url"),
                ],
                anchor="using-api-docs"
            )

        Deep nesting (H6):
            DocxHeading(
                level=6,
                content=[TextSpan(text="Implementation Details")],
                anchor="implementation-details"
            )

    Usage:
        DocxHeading instances are created by DocxRenderer.heading() when parsing
        Markdown heading tokens from mistune. The renderer:
        1. Extracts level from token attributes (1-6)
        2. Renders children tokens to get content spans
        3. Generates anchor from concatenated span text
        4. Returns DocxHeading with all three fields populated

        DocxBuilder.build_heading() consumes DocxHeading to create Word paragraphs:
        1. Applies "Heading N" style based on level
        2. Creates Word bookmark using anchor name (if anchor is set)
        3. Adds formatted text runs from content spans
        4. The bookmark enables internal hyperlinks to this heading

    See Also:
        - DocxRenderer.heading(): Creates DocxHeading from Markdown tokens
        - DocxRenderer._generate_anchor(): Generates GitHub-style anchor slugs
        - DocxBuilder._build_heading(): Builds Word heading with bookmark
        - DocxBuilder._add_bookmark_start/end(): Adds Word bookmark elements
        - TextSpan: Inline formatted text used in heading content
        - StyleMapper.heading_style(): Maps level to Word style name
    """

    level: int
    content: list[TextSpan]
    anchor: str | None = None  # Bookmark anchor for internal links


class DocxParagraph(DocxElement, frozen=True, tag="paragraph"):
    """Paragraph block element with inline formatted text content.

    DocxParagraph represents standard text paragraphs in the Markdown AST, corresponding
    to plain text blocks separated by blank lines. Paragraphs are the most common block
    element and can contain rich inline formatting via TextSpan objects (bold, italic,
    links, inline code, etc.). This class is the primary container for body text in
    documents.

    Attributes:
        content: List of TextSpan objects forming the paragraph text. Each span can have
            different formatting (bold, italic, code, links, etc.), allowing mixed
            formatting within a single paragraph. The list is never None but can be
            empty (though empty paragraphs are rare in practice). Spans are rendered
            sequentially to form the complete paragraph text.

            Common patterns:
            - Single span: Plain text paragraph with uniform formatting
            - Multiple spans: Mixed formatting (e.g., "This is **bold** text")
            - Empty list: Valid but uncommon, renders as blank paragraph

    Rendering to Word:
        When DocxBuilder processes a DocxParagraph, it:
        1. Creates a new Word paragraph object (python-docx Paragraph)
        2. Applies the "Normal" or custom paragraph style from styles-mapping.yaml
        3. Iterates through content spans, adding each as a Run with appropriate formatting
        4. Preserves all inline formatting (bold, italic, code, strikethrough, links)
        5. Handles soft breaks (spaces) and hard breaks (newlines) within spans

        The paragraph style controls:
        - Font family, size, and color
        - Line spacing and paragraph spacing
        - Alignment (left, center, right, justified)
        - Indentation and text direction

    Content Combination:
        Multiple TextSpans allow precise control over formatting boundaries:
        - Each span has independent formatting flags
        - Spans are concatenated without separators (no automatic spaces)
        - Soft breaks between words must be explicitly included as TextSpan(text=" ")
        - The renderer handles breaking inline tokens into separate spans

        Example breakdown:
            Markdown: "This is **bold** and *italic* text"
            content=[
                TextSpan(text="This is "),
                TextSpan(text="bold", bold=True),
                TextSpan(text=" and "),
                TextSpan(text="italic", italic=True),
                TextSpan(text=" text"),
            ]

    Edge Cases:
        - Empty content (content=[]): Valid, renders as blank paragraph (preserves spacing)
        - Single empty span (content=[TextSpan(text="")]): Also renders as blank
        - Only whitespace: Valid, preserves formatting spaces/indentation
        - Very long content: No hard limit, but Word has practical limits (~10,000 chars/para)
        - Newlines in spans: Hard line breaks within paragraph (from Markdown \\)
        - Mixed links and formatting: All combinations supported per TextSpan rules

    Examples:
        Plain text paragraph:
            DocxParagraph(content=[
                TextSpan(text="This is a simple paragraph.")
            ])

        Paragraph with inline formatting (Markdown: "This is **bold** text"):
            DocxParagraph(content=[
                TextSpan(text="This is "),
                TextSpan(text="bold", bold=True),
                TextSpan(text=" text"),
            ])

        Paragraph with link (Markdown: "Visit [our site](https://example.com) today"):
            DocxParagraph(content=[
                TextSpan(text="Visit "),
                TextSpan(text="our site", link="https://example.com"),
                TextSpan(text=" today"),
            ])

        Complex formatting (Markdown: "Use `code` and **bold** with *italic*"):
            DocxParagraph(content=[
                TextSpan(text="Use "),
                TextSpan(text="code", code=True),
                TextSpan(text=" and "),
                TextSpan(text="bold", bold=True),
                TextSpan(text=" with "),
                TextSpan(text="italic", italic=True),
            ])

        Empty paragraph (preserves blank line spacing):
            DocxParagraph(content=[])

    Usage:
        DocxParagraph instances are created by DocxRenderer.paragraph() when parsing
        Markdown paragraph blocks. The renderer:
        1. Receives paragraph token with children from mistune
        2. Renders children to get list of TextSpan objects
        3. Flattens nested inline structures (emphasis, strong, etc.)
        4. Returns DocxParagraph with all spans in content list

        DocxBuilder._build_paragraph() consumes DocxParagraph to create Word paragraphs:
        1. Creates new python-docx Paragraph object
        2. Applies paragraph style from StyleMapper (typically "Normal")
        3. Iterates through content spans, adding each as a Run
        4. Applies formatting to each Run (bold, italic, font, color, etc.)
        5. Handles hyperlinks by creating Word hyperlink elements for spans with link field

    See Also:
        - TextSpan: Inline formatted text units that comprise paragraph content
        - DocxHeading: Similar structure but for headings (includes level and anchor)
        - DocxRenderer.paragraph(): Creates DocxParagraph from Markdown tokens
        - DocxRenderer._flatten_inline(): Flattens inline elements to TextSpan list
        - DocxBuilder._build_paragraph(): Builds Word paragraph from DocxParagraph
        - StyleMapper.get_style(): Maps paragraph to Word style name
    """

    content: list[TextSpan]


class DocxCodeBlock(DocxElement, frozen=True, tag="code_block"):
    """Fenced or indented code block with optional syntax highlighting.

    DocxCodeBlock represents multi-line code blocks in Markdown, created either by
    fenced syntax (```language\\ncode\\n```) or indented blocks (4 spaces/1 tab).
    Code blocks preserve exact formatting, whitespace, and line breaks, making them
    ideal for displaying source code, command output, configuration files, or any
    preformatted text. The optional language field enables syntax-aware styling
    in Word documents.

    Attributes:
        code: The raw code content as a single string. Preserves all whitespace,
            indentation, and newlines exactly as written in the Markdown source.
            Trailing newlines are stripped by DocxRenderer to avoid extra blank
            lines in Word output. Never None, but can be empty string for zero-length
            code blocks (rare but valid). No maximum length enforced, but Word has
            practical limits on paragraph size (~10,000 characters).

            Whitespace handling:
            - Leading/trailing spaces on each line: Preserved exactly
            - Tab characters: Preserved (rendered with tab stops in Word)
            - Internal newlines (\\n): Preserved as line breaks
            - Trailing newline at end: Stripped by renderer.block_code()

        language: Optional language identifier for syntax highlighting, extracted
            from the info string after opening fence (```python -> "python").
            When present, enables language-specific styling in Word via custom
            paragraph styles (e.g., "Code Block Python"). When None, indicates
            no language specified (generic code block) or indented code block.

            Language handling:
            - Fenced block with language: ```python -> language="python"
            - Fenced block without language: ``` -> language=None
            - Indented block: (always) -> language=None
            - Case preserved: ```Python -> language="Python" (not normalized)
            - Multiple words: ```python repl -> language="python" (first word only)
            - Info string parsing: DocxRenderer uses info.split()[0] to extract language

            Common language values: "python", "javascript", "bash", "java", "go",
            "rust", "typescript", "sql", "yaml", "json", "markdown", etc. The exact
            set depends on what the document author specifies - there's no validation
            against a fixed list.

    Rendering to Word:
        When DocxBuilder processes a DocxCodeBlock, it:
        1. Creates a new Word paragraph with monospace font (Courier New or Consolas)
        2. Applies "Code Block" or "Code Block <Language>" style from styles-mapping.yaml
        3. Preserves all whitespace, indentation, and line breaks
        4. May apply language-specific styling (font color, background) if configured
        5. Disables spell check and grammar check for code content

        Code block styles control:
        - Font family (typically monospace: Courier New, Consolas, Fira Code)
        - Font size (often slightly smaller than body text)
        - Background color (light gray or themed for syntax highlighting)
        - Border or shading to distinguish from regular text
        - Line spacing (often tighter than prose)
        - Indentation (often left-indented for visual separation)

    Fenced vs Indented Code Blocks:
        Markdown supports two code block syntaxes:

        Fenced (triple backticks or tildes):
            ```python
            def hello():
                print("world")
            ```
            - Can specify language (```python, ```javascript, etc.)
            - More explicit and readable
            - Preferred for syntax highlighting
            - Results in: DocxCodeBlock(code="def hello():\\n    print(\\"world\\")", language="python")

        Indented (4 spaces or 1 tab):
                def hello():
                    print("world")
            - No language specification possible
            - Legacy syntax, less common in modern Markdown
            - Results in: DocxCodeBlock(code="def hello():\\n    print(\\"world\\")", language=None)

        Both syntaxes produce DocxCodeBlock, differing only in language field.

    Edge Cases:
        - Empty code (code=""): Valid, renders as empty code block (preserves structure)
        - Only whitespace: Valid, preserves spaces/tabs/newlines exactly
        - Very long code: No hard limit, but may hit Word paragraph size limits
        - language=None: Generic code block, no syntax-specific styling
        - language="" (empty string): Treated same as None by StyleMapper
        - Invalid language: Accepted as-is, may fall back to generic style
        - Mixed tabs/spaces: Preserved exactly (no normalization)
        - Windows (\\r\\n) vs Unix (\\n) line endings: Normalized by mistune/python-docx
        - Trailing newlines: Stripped by renderer to avoid extra spacing

    Examples:
        Python code with language (Markdown: ```python\\nprint("hi")\\n```):
            DocxCodeBlock(
                code='print("hi")',
                language="python"
            )

        Generic code without language (Markdown: ```\\ncode here\\n```):
            DocxCodeBlock(
                code="code here",
                language=None
            )

        Indented code block (4 spaces):
            DocxCodeBlock(
                code="    indented code\\n    more code",
                language=None
            )

        Multi-line bash script (Markdown: ```bash\\n#!/bin/bash\\necho "test"\\n```):
            DocxCodeBlock(
                code='#!/bin/bash\\necho "test"',
                language="bash"
            )

        Empty code block:
            DocxCodeBlock(
                code="",
                language=None
            )

        Code with preserved whitespace:
            DocxCodeBlock(
                code="    def indent():\\n        pass",
                language="python"
            )

    Usage:
        DocxCodeBlock instances are created by DocxRenderer.block_code() when parsing
        Markdown code block tokens from mistune. The renderer:
        1. Extracts raw code from token (token.get("raw", ""))
        2. Strips trailing newline from code (code.rstrip("\\n"))
        3. Extracts language from info string (token.get("attrs", {}).get("info", ""))
        4. Parses language as first word of info string (info.split()[0])
        5. Returns DocxCodeBlock with code and optional language

        DocxBuilder._build_code_block() consumes DocxCodeBlock to create Word code paragraphs:
        1. Creates new python-docx Paragraph object
        2. Applies "Code Block" or language-specific style from StyleMapper
        3. Sets monospace font (Courier New, Consolas, or custom)
        4. Adds code text as single Run, preserving all whitespace
        5. Disables spell/grammar checking (if supported by template)
        6. May apply syntax highlighting colors (if configured in styles)

    See Also:
        - TextSpan: For inline code (`code`), use TextSpan with code=True instead
        - DocxParagraph: Regular paragraph blocks (DocxCodeBlock is similar but preformatted)
        - DocxRenderer.block_code(): Creates DocxCodeBlock from Markdown tokens
        - DocxBuilder._build_code_block(): Builds Word paragraph from DocxCodeBlock
        - StyleMapper.code_block_style(): Maps language to Word style name
        - styles-mapping.yaml: Defines code block style settings
    """

    code: str
    language: str | None = None


class DocxBlockquote(DocxElement, frozen=True, tag="blockquote"):
    """Blockquote element containing nested block-level elements.

    DocxBlockquote represents quoted text blocks in Markdown, created with leading
    greater-than symbols (> quote text). Unlike simple text containers, blockquotes
    can contain arbitrary nested block elements (paragraphs, headings, lists, code
    blocks, even other blockquotes), making them a recursive container structure.
    This enables complex quoted content like multi-paragraph citations, quoted code
    examples, or nested conversation threads.

    Note: GitHub-style admonitions (> [!NOTE], > [!WARNING], etc.) are NOT represented
    as DocxBlockquote - they are detected by DocxRenderer and converted to DocxAdmonition
    elements instead. Only standard blockquotes (without admonition markers) use this class.

    Attributes:
        children: List of nested DocxElement block elements contained within the blockquote.
            Can include any block-level element type: DocxParagraph, DocxHeading, DocxList,
            DocxCodeBlock, DocxTable, DocxImage, DocxHorizontalRule, even nested DocxBlockquote.
            Never None, but can be empty list (though empty blockquotes are rare).

            Common patterns:
            - Single paragraph: Most common case (> Simple quote)
            - Multiple paragraphs: Separated by blank lines within quote
            - Mixed content: Paragraphs + code blocks + lists
            - Nested blockquotes: Quotes within quotes (>> nested)
            - Empty children: Valid but uncommon, renders as empty quote block

    Nesting and Recursion:
        Blockquotes support arbitrary nesting depth:
        - Level 1: > quote
        - Level 2: >> nested quote
        - Level 3: >>> deeply nested
        - No hard limit on depth, though readability degrades beyond 2-3 levels

        Each nesting level creates a new DocxBlockquote wrapping the content:
            Markdown:
                > Level 1
                >> Level 2
                >>> Level 3

            AST:
                DocxBlockquote(children=[
                    DocxParagraph(content=[TextSpan(text="Level 1")]),
                    DocxBlockquote(children=[
                        DocxParagraph(content=[TextSpan(text="Level 2")]),
                        DocxBlockquote(children=[
                            DocxParagraph(content=[TextSpan(text="Level 3")]),
                        ])
                    ])
                ])

        The renderer handles nesting during parsing, and the builder applies
        increasing indentation for each level.

    Rendering to Word:
        When DocxBuilder processes a DocxBlockquote, it:
        1. Applies "Quote" or "Blockquote" paragraph style from styles-mapping.yaml
        2. Increases left indentation for all nested content
        3. May add vertical bar or border to left margin (style-dependent)
        4. Recursively builds all children elements with quote styling
        5. Restores indentation level after quote block ends

        Blockquote styles typically control:
        - Left indentation (0.5-1.0 inch to visually offset from body text)
        - Font style (often italic or different color for emphasis)
        - Border/shading (vertical bar on left, light gray background)
        - Spacing (extra space before/after quote block)

    Admonition Detection:
        The renderer detects GitHub-style admonitions and converts them to DocxAdmonition
        instead of DocxBlockquote:

        Standard blockquote (becomes DocxBlockquote):
            > This is a regular quote

        Admonition (becomes DocxAdmonition, NOT DocxBlockquote):
            > [!NOTE]
            > This is an admonition

        Detection logic in DocxRenderer.block_quote():
        1. Render children to get list of elements
        2. Check if first element is DocxParagraph
        3. Check if first paragraph starts with [!TYPE] pattern
        4. If match: extract type and create DocxAdmonition
        5. If no match: create DocxBlockquote with all children

        This means DocxBlockquote never contains admonition markers in practice -
        they're always converted before the DocxBlockquote is created.

    Edge Cases:
        - Empty children (children=[]): Valid, renders as empty quote block
        - Single paragraph: Most common, rendered with quote styling
        - Nested blockquotes: Each level increases indentation
        - Very deep nesting: No hard limit, but readability and indentation limits apply
        - Mixed element types: All valid, each rendered with appropriate quote offset
        - Blockquote containing table: Valid, table rendered with quote indentation
        - Blockquote containing code: Valid, code block rendered with quote styling

    Examples:
        Simple single-paragraph quote (Markdown: > Hello world):
            DocxBlockquote(children=[
                DocxParagraph(content=[TextSpan(text="Hello world")])
            ])

        Multi-paragraph quote (Markdown: > Para 1\\n>\\n> Para 2):
            DocxBlockquote(children=[
                DocxParagraph(content=[TextSpan(text="Para 1")]),
                DocxParagraph(content=[TextSpan(text="Para 2")]),
            ])

        Quote with formatted text (Markdown: > This is **bold** quote):
            DocxBlockquote(children=[
                DocxParagraph(content=[
                    TextSpan(text="This is "),
                    TextSpan(text="bold", bold=True),
                    TextSpan(text=" quote"),
                ])
            ])

        Nested blockquote (Markdown: > Outer\\n>> Inner):
            DocxBlockquote(children=[
                DocxParagraph(content=[TextSpan(text="Outer")]),
                DocxBlockquote(children=[
                    DocxParagraph(content=[TextSpan(text="Inner")]),
                ])
            ])

        Quote with code block (Markdown: > Quote\\n> ```\\n> code\\n> ```):
            DocxBlockquote(children=[
                DocxParagraph(content=[TextSpan(text="Quote")]),
                DocxCodeBlock(code="code", language=None),
            ])

        Empty blockquote:
            DocxBlockquote(children=[])

    Usage:
        DocxBlockquote instances are created by DocxRenderer.block_quote() when parsing
        Markdown blockquote tokens from mistune, but ONLY for standard blockquotes.
        The renderer:
        1. Receives blockquote token with children from mistune
        2. Recursively renders all children to get list of DocxElement objects
        3. Checks first element for admonition pattern [!TYPE]
        4. If admonition: creates DocxAdmonition instead (not DocxBlockquote)
        5. If standard quote: returns DocxBlockquote with all children

        DocxBuilder._build_blockquote() consumes DocxBlockquote to create Word quote blocks:
        1. Increases indentation level (tracking nesting depth)
        2. Iterates through children, recursively building each element
        3. Applies "Quote" style to paragraphs within blockquote
        4. Adds left border or shading (style-dependent)
        5. Decreases indentation level after quote ends

    See Also:
        - DocxAdmonition: GitHub-style callouts (> [!NOTE]) - NOT blockquotes
        - DocxParagraph: Most common child element of blockquotes
        - DocxRenderer.block_quote(): Creates DocxBlockquote or DocxAdmonition
        - DocxBuilder._build_blockquote(): Builds Word quote blocks with indentation
        - StyleMapper.get_quote_style(): Maps blockquote to Word style name
        - ADMONITION_PATTERN: Regex for detecting admonition markers
    """

    children: list[DocxElement]


class DocxListItem(msgspec.Struct, frozen=True):
    """Individual list item with content and optional nested elements.

    DocxListItem represents a single item within a DocxList (ordered or unordered).
    Each item has primary text content (list of TextSpan) and can optionally contain
    nested block-level elements (paragraphs, sublists, code blocks, etc.). This
    structure enables complex nested lists and mixed content within list items,
    matching Markdown's flexible list syntax.

    Note: DocxListItem is a helper struct and does NOT inherit from DocxElement.
    It is wrapped by DocxList, which is the actual block-level element in the AST.
    List items cannot exist independently - they must be contained within a parent
    DocxList.

    Attributes:
        content: List of TextSpan objects forming the primary text of this list item.
            Supports all inline formatting (bold, italic, links, code, strikethrough).
            This is the text that appears on the same line as the bullet/number marker.
            Never None, but can be empty list (though empty items are uncommon).
            Multiple spans allow mixed formatting within a single item.

            Examples of content:
            - Plain text: [TextSpan(text="Item text")]
            - Formatted: [TextSpan(text="Bold ", bold=True), TextSpan(text="item")]
            - With link: [TextSpan(text="See "), TextSpan(text="docs", link="url")]
            - Empty: [] (valid but rare, renders as blank list item)

        children: List of nested DocxElement blocks that appear after the primary
            content, indented under this list item. Enables complex nested structures
            like multi-paragraph list items, sublists, code blocks within items, etc.
            Defaults to empty list via msgspec.field(default_factory=list).

            Common nested elements:
            - DocxList: Nested sublists (ordered or unordered) for hierarchical structure
            - DocxParagraph: Additional paragraphs continuing the list item content
            - DocxCodeBlock: Code examples within a list item
            - DocxTable: Tables nested under a list item (rare but valid)
            - DocxImage: Images within list items
            - Any other DocxElement: Full nesting support for all block types

            Nesting behavior:
            - Children are rendered indented beneath the item's primary content
            - Each child element is built recursively by DocxBuilder
            - Nested DocxList items are rendered with increased indentation level
            - Empty children list (default): Simple list item with only content text
            - Non-empty children: Complex list item with nested blocks

    List Item Structure:
        Markdown list items can have two forms:

        Simple (no children):
            - Item text
            content=[TextSpan(text="Item text")]
            children=[]

        Complex (with nested elements):
            - Item text

              Additional paragraph

              ```
              code block
              ```

              - Nested item
            content=[TextSpan(text="Item text")]
            children=[
                DocxParagraph(content=[...]),
                DocxCodeBlock(code="code block", language=None),
                DocxList(ordered=False, items=[...]),
            ]

        The parser automatically handles blank lines and indentation to determine
        which elements are nested children vs. separate top-level elements.

    Nesting and Indentation:
        The children field is what enables Markdown's nested list syntax:

        Markdown:
            1. First item
            2. Second item
               - Nested bullet
               - Another nested bullet
            3. Third item

        AST:
            DocxList(ordered=True, items=[
                DocxListItem(content=[TextSpan(text="First item")], children=[]),
                DocxListItem(
                    content=[TextSpan(text="Second item")],
                    children=[
                        DocxList(ordered=False, items=[
                            DocxListItem(content=[TextSpan(text="Nested bullet")]),
                            DocxListItem(content=[TextSpan(text="Another nested bullet")]),
                        ])
                    ]
                ),
                DocxListItem(content=[TextSpan(text="Third item")], children=[]),
            ])

        When building Word documents, ListBuilder.build() recursively processes
        children lists, increasing the indentation level for each nesting depth.
        This creates the visual hierarchy that matches Markdown's structure.

    Rendering to Word:
        When ListBuilder processes a DocxListItem, it:
        1. Creates a Word paragraph for the item content with bullet/number prefix
        2. Applies indentation based on nesting level (0.35 inch per level)
        3. Adds TextSpan content as formatted runs
        4. Recursively builds all children elements with increased indentation
        5. Nested DocxList children are built with level+1 indentation

        Example rendering:
            Simple item:
                content=[TextSpan(text="Item")]
                children=[]
                → "- Item" (unordered) or "1. Item" (ordered)

            Item with nested list:
                content=[TextSpan(text="Parent")]
                children=[DocxList(ordered=False, items=[...])]
                → "1. Parent"
                  "    - Nested child"

    Edge Cases:
        - Empty content (content=[]): Valid, renders as bullet/number with no text
        - Empty children (children=[]): Default, simple list item with just content
        - Both empty: Valid but renders as blank list item (rare)
        - Very deep nesting: No hard limit, but readability degrades beyond 3-4 levels
        - Mixed children types: All valid, each rendered appropriately
        - Nested list as only child: Common pattern for hierarchical lists
        - Multiple nested lists: Valid, each rendered sequentially

    Examples:
        Simple list item:
            DocxListItem(
                content=[TextSpan(text="Simple item")],
                children=[]
            )

        Formatted list item (Markdown: - This is **bold** text):
            DocxListItem(
                content=[
                    TextSpan(text="This is "),
                    TextSpan(text="bold", bold=True),
                    TextSpan(text=" text"),
                ],
                children=[]
            )

        List item with nested sublist:
            DocxListItem(
                content=[TextSpan(text="Parent item")],
                children=[
                    DocxList(ordered=False, items=[
                        DocxListItem(content=[TextSpan(text="Nested 1")]),
                        DocxListItem(content=[TextSpan(text="Nested 2")]),
                    ])
                ]
            )

        List item with multiple nested elements:
            DocxListItem(
                content=[TextSpan(text="Main point")],
                children=[
                    DocxParagraph(content=[TextSpan(text="Explanation paragraph")]),
                    DocxCodeBlock(code="example code", language="python"),
                ]
            )

        Empty list item:
            DocxListItem(
                content=[],
                children=[]
            )

    Usage:
        DocxListItem instances are created by DocxRenderer.list_item() when parsing
        Markdown list item tokens from mistune. The renderer:
        1. Receives list item token with children from mistune
        2. Renders inline children to get content TextSpans
        3. Renders block children (if any) to get nested DocxElements
        4. Separates inline content from block children
        5. Returns DocxListItem with content and children populated

        ListBuilder._build_list_item() consumes DocxListItem to create Word paragraphs:
        1. Creates Word paragraph with bullet/number prefix based on parent list type
        2. Applies indentation based on nesting level
        3. Adds content TextSpans as formatted runs
        4. After the item paragraph, recursively builds children with increased level
        5. Returns the item paragraph (children are added separately to document)

    See Also:
        - DocxList: Parent container for list items (the actual block element)
        - TextSpan: Inline formatted text used in item content
        - DocxRenderer.list_item(): Creates DocxListItem from Markdown tokens
        - ListBuilder._build_list_item(): Builds Word paragraph from list item
        - ListBuilder.build(): Recursively builds lists with nesting support
    """

    content: list[TextSpan]
    children: list[DocxElement] = msgspec.field(default_factory=list)


class DocxList(DocxElement, frozen=True, tag="list"):
    """Ordered (numbered) or unordered (bulleted) list with optional start number.

    DocxList represents both ordered and unordered lists in the Markdown AST. It
    contains a sequence of DocxListItem elements and supports nested sublists through
    the children field of each item. Lists can start at any number (for ordered lists)
    and support arbitrary nesting depth, enabling complex hierarchical structures.

    Attributes:
        ordered: Boolean flag distinguishing ordered from unordered lists.
            - True: Ordered list (numbered) - Markdown: 1. item, 2. item, etc.
            - False: Unordered list (bulleted) - Markdown: - item, * item, + item

            Ordered vs Unordered:
            Ordered lists (ordered=True):
                - Display sequential numbers: 1., 2., 3., etc.
                - Numbers increment automatically for each item
                - Start number controlled by `start` attribute
                - Markdown syntax: "1. item" or "1) item"
                - Common for steps, procedures, rankings, sequences

            Unordered lists (ordered=False):
                - Display bullet markers: -, *, or • (depends on Word style)
                - All items use same marker (no numbering)
                - `start` attribute ignored for unordered lists
                - Markdown syntax: "- item", "* item", or "+ item"
                - Common for feature lists, bullet points, non-sequential items

            The `ordered` flag is extracted from mistune's token.get("attrs", {}).get("ordered")
            during parsing and determines which list style is applied in Word.

        items: List of DocxListItem objects representing the individual list entries.
            Each item has its own content (TextSpans) and optional nested children
            (including nested sublists). Never None, but can be empty list (though
            empty lists are rare in practice). The order of items in this list
            determines their rendering order in the Word document.

            Item structure:
            - Simple items: Just content text, no children
            - Complex items: Content text plus nested elements (paragraphs, sublists, code)
            - Mixed: Some items simple, others complex within same list

            Nested sublists:
            Items can contain nested DocxList objects in their children field, creating
            hierarchical list structures with arbitrary nesting depth. Each nesting
            level increases indentation in the rendered Word document.

        start: Starting number for ordered lists (defaults to 1). This attribute
            controls the first number displayed in an ordered list sequence. Subsequent
            items increment automatically: start=5 produces 5., 6., 7., etc.

            Behavior by list type:
            - Ordered lists (ordered=True): `start` sets the initial number
                * start=1 (default): 1., 2., 3., ... (standard numbering)
                * start=5: 5., 6., 7., ... (continue from previous section)
                * start=0: 0., 1., 2., ... (zero-indexed lists)
                * Any positive integer: Starts from that number
            - Unordered lists (ordered=False): `start` is ignored
                * Value has no effect on rendering (always bullets)
                * Typically left at default value of 1

            Common use cases:
            - start=1 (default): Standard numbering from 1
            - start>1: Continue numbering from previous list (split by paragraphs)
            - start=0: Zero-indexed numbering (programming contexts)

            Markdown support:
            GitHub-flavored Markdown allows specifying start numbers:
                5. First item    → start=5, renders as "5. First item"
                6. Second item   → renders as "6. Second item"
                1. Restart       → start=1, renders as "1. Restart"

            The mistune parser extracts start from token.get("attrs", {}).get("start", 1)
            and DocxRenderer passes it through to DocxList. ListBuilder uses it to
            calculate item numbers: number = idx + start for item at index idx.

    List Types and Markdown Syntax:
        Markdown supports multiple syntaxes that all map to ordered/unordered:

        Unordered (ordered=False):
            - Dash syntax:   - item
            - Star syntax:   * item
            - Plus syntax:   + item
            All produce: DocxList(ordered=False, items=[...], start=1)

        Ordered (ordered=True):
            - Number syntax: 1. item
            - Paren syntax:  1) item
            Both produce: DocxList(ordered=True, items=[...], start=1)

        The specific marker (-, *, +) or number format (., )) doesn't affect the AST -
        only the ordered flag matters. Word rendering uses configured list styles.

    Nesting and Hierarchy:
        Lists support arbitrary nesting through DocxListItem.children:

        Markdown:
            1. First item
            2. Second item
               - Nested bullet
               - Another bullet
                 1. Deeply nested
            3. Third item

        AST:
            DocxList(ordered=True, start=1, items=[
                DocxListItem(content=[TextSpan(text="First item")]),
                DocxListItem(
                    content=[TextSpan(text="Second item")],
                    children=[
                        DocxList(ordered=False, items=[
                            DocxListItem(
                                content=[TextSpan(text="Nested bullet")],
                            ),
                            DocxListItem(
                                content=[TextSpan(text="Another bullet")],
                                children=[
                                    DocxList(ordered=True, start=1, items=[
                                        DocxListItem(content=[TextSpan(text="Deeply nested")]),
                                    ])
                                ]
                            ),
                        ])
                    ]
                ),
                DocxListItem(content=[TextSpan(text="Third item")]),
            ])

        ListBuilder.build() recursively processes nested lists, increasing indentation
        level for each nesting depth (0.35 inch per level).

    Rendering to Word:
        When ListBuilder processes a DocxList, it:
        1. Determines list style based on ordered flag (List Number vs List Bullet)
        2. Iterates through items, creating Word paragraph for each
        3. Applies manual prefix (number/bullet) and indentation based on level
        4. For ordered lists, calculates item number as: idx + start
        5. Recursively builds nested children lists with increased level
        6. Returns list of all created paragraphs (flat list, indentation via formatting)

        Example rendering:
            Ordered list with start=1:
                ordered=True, start=1, items=[Item("A"), Item("B")]
                → "1. A"
                  "2. B"

            Ordered list with start=5:
                ordered=True, start=5, items=[Item("X"), Item("Y")]
                → "5. X"
                  "6. Y"

            Unordered list:
                ordered=False, items=[Item("A"), Item("B")]
                → "- A"
                  "- B"

            Nested list:
                ordered=True, items=[
                    Item("Parent", children=[
                        DocxList(ordered=False, items=[Item("Child")])
                    ])
                ]
                → "1. Parent"
                  "    - Child"

    Edge Cases:
        - Empty items (items=[]): Valid but renders as empty list (rare)
        - Single item: Common, valid for simple lists
        - start=0: Valid, renders 0., 1., 2., ... (uncommon but allowed)
        - start>1 with unordered: Valid but start ignored (still renders bullets)
        - Very large start: Valid, e.g., start=1000 → 1000., 1001., ...
        - Deep nesting: No hard limit, but readability degrades beyond 3-4 levels
        - Mixed ordered/unordered nesting: Fully supported and common
        - List items with empty content: Valid, renders marker with no text
        - Consecutive lists: Separate DocxList elements (not merged)

    Examples:
        Simple unordered list (Markdown: - A\\n- B):
            DocxList(
                ordered=False,
                items=[
                    DocxListItem(content=[TextSpan(text="A")]),
                    DocxListItem(content=[TextSpan(text="B")]),
                ],
                start=1  # Ignored for unordered
            )

        Simple ordered list (Markdown: 1. First\\n2. Second):
            DocxList(
                ordered=True,
                items=[
                    DocxListItem(content=[TextSpan(text="First")]),
                    DocxListItem(content=[TextSpan(text="Second")]),
                ],
                start=1
            )

        Ordered list starting at 5 (Markdown: 5. Item\\n6. Item):
            DocxList(
                ordered=True,
                items=[
                    DocxListItem(content=[TextSpan(text="Item")]),
                    DocxListItem(content=[TextSpan(text="Item")]),
                ],
                start=5  # First item displays as "5."
            )

        Nested list (Markdown: 1. Parent\\n   - Child):
            DocxList(
                ordered=True,
                items=[
                    DocxListItem(
                        content=[TextSpan(text="Parent")],
                        children=[
                            DocxList(
                                ordered=False,
                                items=[
                                    DocxListItem(content=[TextSpan(text="Child")]),
                                ]
                            )
                        ]
                    )
                ],
                start=1
            )

        Formatted list items (Markdown: 1. **Bold** item):
            DocxList(
                ordered=True,
                items=[
                    DocxListItem(content=[
                        TextSpan(text="Bold", bold=True),
                        TextSpan(text=" item"),
                    ]),
                ],
                start=1
            )

        Empty list:
            DocxList(
                ordered=False,
                items=[],
                start=1
            )

    Usage:
        DocxList instances are created by DocxRenderer.list() when parsing Markdown
        list tokens from mistune. The renderer:
        1. Extracts ordered flag from token.get("attrs", {}).get("ordered", False)
        2. Extracts start number from token.get("attrs", {}).get("start", 1)
        3. Iterates through list children, rendering each as DocxListItem
        4. Returns DocxList with ordered, items, and start populated

        ListBuilder.build() consumes DocxList to create Word list paragraphs:
        1. Gets appropriate list style based on ordered flag (via StyleMapper)
        2. Iterates through items with enumerate to track index
        3. Calls _build_list_item() for each item, passing:
           - item: The DocxListItem to render
           - ordered: Boolean for prefix style (number vs bullet)
           - level: Current nesting depth (for indentation)
           - style_name: Word style to apply
           - number: idx + start (for ordered lists)
        4. Recursively processes nested children lists with level+1
        5. Returns flat list of all Word paragraphs

    See Also:
        - DocxListItem: Individual list entries (helper struct, not block element)
        - TextSpan: Inline formatted text used in list item content
        - DocxRenderer.list(): Creates DocxList from Markdown tokens
        - DocxRenderer.list_item(): Creates DocxListItem from Markdown tokens
        - ListBuilder.build(): Builds Word paragraphs from DocxList with nesting
        - ListBuilder._build_list_item(): Builds single Word paragraph from item
        - StyleMapper.list_style(): Maps ordered flag to Word list style name
    """

    ordered: bool
    items: list[DocxListItem]
    start: int = 1


class DocxTableCell(msgspec.Struct, frozen=True):
    """Table cell with content and merge directives.

    DocxTableCell represents a single cell in a Markdown table, including its text
    content, header status, and merge instructions for creating colspan/rowspan
    effects in the final Word document.

    Cell Merging Mechanism:
        Markdown tables don't natively support merged cells, but extended Markdown
        parsers use special markers to indicate cell merging:
        - `^^` marker: Merge this cell with the cell directly above (vertical merge)
        - `>>` marker: Merge this cell with the cell to the left (horizontal merge)

        These markers are parsed into boolean flags (merge_up, merge_left) that
        TableBuilder._process_cell_merges() converts to Word cell merges:

        1. **Vertical Merges (merge_up=True)**:
           - Indicates this cell should merge with the cell above it
           - TableBuilder scans each column top-to-bottom
           - When a cell with merge_up=False is followed by cells with merge_up=True,
             those cells are merged into the first cell using Word's vertical merge
           - The origin cell retains its content; merged cells are marked as merged
             and skipped during cell filling
           - Example:
               | Header |
               | Cell 1 |  ← origin cell (merge_up=False)
               | ^^     |  ← merged cell (merge_up=True)
               | ^^     |  ← merged cell (merge_up=True)
             Results in a single cell spanning 3 rows

        2. **Horizontal Merges (merge_left=True)**:
           - Indicates this cell should merge with the cell to its left
           - TableBuilder scans each row left-to-right
           - When a cell with merge_left=False is followed by cells with merge_left=True,
             those cells are merged into the first cell using Word's horizontal merge
           - The origin cell retains its content; merged cells are marked and skipped
           - Example:
               | Cell 1 | >>     | >>     |
                 ↑        ↑        ↑
                 origin   merged   merged
             Results in a single cell spanning 3 columns

        3. **Two-Pass Merge Processing**:
           TableBuilder._process_cell_merges() uses a two-pass algorithm:
           - First pass: Process vertical merges (merge_up) column by column
           - Second pass: Process horizontal merges (merge_left) row by row
           - Merged cell positions are tracked in a set to skip during content filling
           - This order ensures that complex merges (both horizontal and vertical)
             are handled correctly

        4. **Word Document Integration**:
           - python-docx Cell.merge() method combines cells in the Word table
           - For vertical merge: merge(start_cell, end_cell) where cells are in same column
           - For horizontal merge: merge(start_cell, end_cell) where cells are in same row
           - Merged cells appear as a single cell in Word with unified borders and content
           - The content from the origin cell is preserved; merged cell content is ignored

    Relationship to colspan/rowspan Fields:
        The colspan and rowspan fields are currently present but NOT actively used by
        TableBuilder. They represent an alternative merging approach:
        - colspan: Number of columns this cell should span (1 = no span, 2+ = merge right)
        - rowspan: Number of rows this cell should span (1 = no span, 2+ = merge down)

        Why merge_up/merge_left instead of colspan/rowspan?
        - Markdown table parsers (like mistune) naturally detect `^^` and `>>` markers
        - merge_up/merge_left explicitly mark which cells to merge, making the algorithm
          simpler (scan and merge consecutive merge-marked cells)
        - colspan/rowspan require tracking span counts and calculating ranges, which is
          more complex for irregular table structures
        - Future refactoring may switch to colspan/rowspan and remove merge flags

        Current behavior:
        - merge_up/merge_left: Actively used by TableBuilder for Word merges
        - colspan/rowspan: Parsed and stored but ignored during building
        - Both are preserved in the AST for potential future use

    Attributes:
        content: List of TextSpan objects representing the cell's formatted text.
            May be empty for cells that only serve as merge targets or placeholders.
            Merged cells (merge_up=True or merge_left=True) typically have empty
            content since they're absorbed into the origin cell.
        is_header: Whether this cell is a header cell (first row in Markdown tables).
            Header cells receive special styling (bold, background color, centered text)
            via table_config in StyleMapper. Note: this is a cell-level flag, though
            typically the entire first row has is_header=True.
        colspan: Number of columns this cell spans (default 1). Currently parsed but
            not used by TableBuilder. Reserved for future colspan/rowspan-based merging.
        rowspan: Number of rows this cell spans (default 1). Currently parsed but not
            used by TableBuilder. Reserved for future colspan/rowspan-based merging.
        merge_up: If True, this cell merges with the cell directly above it (Markdown: ^^).
            Actively used by TableBuilder._process_cell_merges() for vertical merging.
            The cell is marked as part of a merged region and its content is ignored.
            Origin cell (the cell being merged into) has merge_up=False.
        merge_left: If True, this cell merges with the cell to its left (Markdown: >>).
            Actively used by TableBuilder._process_cell_merges() for horizontal merging.
            The cell is marked as part of a merged region and its content is ignored.
            Origin cell (the cell being merged into) has merge_left=False.

    Merge Processing Algorithm (TableBuilder._process_cell_merges):
        ```python
        # Vertical merges: scan each column top to bottom
        for col_idx in range(num_cols):
            for row_idx in range(num_rows):
                cell = table_element.rows[row_idx].cells[col_idx]
                if not cell.merge_up:
                    # Count consecutive merge_up cells below
                    merge_count = 0
                    for check_row in range(row_idx + 1, num_rows):
                        if table_element.rows[check_row].cells[col_idx].merge_up:
                            merge_count += 1
                        else:
                            break
                    # Perform Word merge if any merge_up cells found
                    if merge_count > 0:
                        start_cell = table.rows[row_idx].cells[col_idx]
                        end_cell = table.rows[row_idx + merge_count].cells[col_idx]
                        start_cell.merge(end_cell)

        # Horizontal merges: scan each row left to right
        for row_idx in range(num_rows):
            for col_idx in range(num_cols):
                cell = table_element.rows[row_idx].cells[col_idx]
                if not cell.merge_left:
                    # Count consecutive merge_left cells to the right
                    merge_count = 0
                    for check_col in range(col_idx + 1, num_cols):
                        if table_element.rows[row_idx].cells[check_col].merge_left:
                            merge_count += 1
                        else:
                            break
                    # Perform Word merge if any merge_left cells found
                    if merge_count > 0:
                        start_cell = table.rows[row_idx].cells[col_idx]
                        end_cell = table.rows[row_idx].cells[col_idx + merge_count]
                        start_cell.merge(end_cell)
        ```

    Edge Cases:
        - Empty content (content=[]): Valid for placeholder cells or cells marked for merging
        - merge_up on first row: Invalid (no cell above to merge with), parser should prevent
        - merge_left on first column: Invalid (no cell to the left), parser should prevent
        - Both merge_up and merge_left True: Unclear semantics, parser should prevent
        - colspan/rowspan > 1 with merge flags: Conflicting merge directives, parser should prevent
        - Consecutive origin cells with no merge markers: Normal non-merged cells
        - Long merge chains: Valid (e.g., 5 cells with merge_up=True merging into one origin)

    Examples:
        Simple text cell:
            DocxTableCell(
                content=[TextSpan(text="Hello")],
                is_header=False
            )

        Header cell with formatting:
            DocxTableCell(
                content=[TextSpan(text="Name", bold=True)],
                is_header=True
            )

        Cell with vertical merge (Markdown: ^^):
            DocxTableCell(
                content=[],  # Empty, will be merged into cell above
                merge_up=True
            )

        Cell with horizontal merge (Markdown: >>):
            DocxTableCell(
                content=[],  # Empty, will be merged into cell to left
                merge_left=True
            )

        Origin cell for vertical merge (content is preserved):
            DocxTableCell(
                content=[TextSpan(text="Spans multiple rows")],
                merge_up=False,  # This is the origin cell
            )

        Empty cell (valid in sparse tables):
            DocxTableCell(
                content=[],
                is_header=False
            )

    Usage:
        DocxTableCell instances are created by DocxRenderer._process_table() when
        parsing Markdown table tokens from mistune. The renderer:
        1. Iterates through each cell token in the table
        2. Detects ^^ and >> markers in cell text
        3. Creates DocxTableCell with appropriate merge flags set
        4. Sets is_header=True for cells in the first row (if table has header)
        5. Parses inline formatting into TextSpan list for content

        TableBuilder.build() consumes DocxTableCell to create Word tables:
        1. Calls _process_cell_merges() to perform vertical and horizontal merges
        2. Skips merged cells during content filling (tracked in merged_cells set)
        3. Calls _fill_cell() to add content spans to origin cells only
        4. Applies header styling (bold, background) if is_header=True
        5. Results in a Word table with properly merged cells and formatted content

    See Also:
        - TableBuilder._process_cell_merges(): Implements merge algorithm
        - TableBuilder._fill_cell(): Populates cell content and applies styling
        - DocxTableRow: Container for cells in a table row
        - DocxTable: Container for rows forming a complete table
        - TextSpan: Formatted text content within cells
        - StyleMapper.table_config(): Provides header/border/color configuration
    """

    content: list[TextSpan]
    is_header: bool = False
    colspan: int = 1
    rowspan: int = 1
    merge_up: bool = False
    merge_left: bool = False


class DocxTableRow(msgspec.Struct, frozen=True):
    """Single row in a table containing an ordered sequence of cells.

    DocxTableRow represents one horizontal row within a DocxTable. It is a simple
    container structure that holds an ordered list of DocxTableCell objects. Rows
    do not have row-level attributes like height or styling - these are determined
    during Word document building based on cell content and table configuration.

    Note: DocxTableRow is a helper struct and does NOT inherit from DocxElement.
    It is always wrapped by DocxTable, which is the actual block-level element in
    the AST. Rows cannot exist independently - they must be contained within a
    parent DocxTable.

    Attributes:
        cells: Ordered list of DocxTableCell objects forming this row's columns.
            The number of cells determines the column count for this row, though
            rows within the same table may have different cell counts (irregular
            tables). Never None, but can be empty list for zero-width rows (rare).

            Cell ordering:
            - Index 0: Leftmost cell (first column)
            - Index 1: Second column
            - Index N: Rightmost cell (last column)
            - The order in this list directly determines left-to-right column order

            Variable cell counts:
            When rows in the same table have different lengths, TableBuilder
            normalizes to the maximum column count by treating missing cells as
            empty. Example:
                Row 1: [Cell A, Cell B, Cell C]  → 3 cells
                Row 2: [Cell X, Cell Y]          → 2 cells (normalized to 3)
                num_cols = max(3, 2) = 3
                Word table: Row 2 gets empty third cell automatically

    Relationship to Table Structure:
        DocxTable contains rows, rows contain cells:
            DocxTable
            ├── DocxTableRow (row 0)
            │   ├── DocxTableCell (0,0)
            │   ├── DocxTableCell (0,1)
            │   └── DocxTableCell (0,2)
            ├── DocxTableRow (row 1)
            │   ├── DocxTableCell (1,0)
            │   ├── DocxTableCell (1,1)
            │   └── DocxTableCell (1,2)
            └── DocxTableRow (row 2)
                └── ...

        Each row is independent - cells in one row don't directly reference cells
        in other rows (except via merge_up flags for vertical merging).

    Header Row Semantics:
        The first row (index 0) in a table is typically the header row when
        DocxTable.has_header=True. Header rows receive special styling:
        - Cells have is_header=True flag set
        - Bold font, background color, centered alignment
        - Applied by TableBuilder._fill_cell() when is_header_row=True

        Example:
            DocxTable(
                rows=[
                    DocxTableRow(cells=[...]),  ← Header row if has_header=True
                    DocxTableRow(cells=[...]),  ← Data row
                    DocxTableRow(cells=[...]),  ← Data row
                ],
                has_header=True
            )

        The row itself doesn't know it's a header - this is determined by:
            is_header_row = (row_idx == 0) and table.has_header

    Cell Merging Across Rows:
        While rows are structurally independent, cell merging creates logical
        dependencies between rows:
        - Vertical merges (merge_up=True): Cell merges with cell in previous row
        - Horizontal merges (merge_left=True): Cell merges with previous cell in same row

        Example vertical merge across rows:
            Row 0: [Cell A (merge_up=False), Cell B]
            Row 1: [Cell ^^ (merge_up=True), Cell C]
            Row 2: [Cell ^^ (merge_up=True), Cell D]

        The merge_up flags in rows 1 and 2 reference the cell in row 0, creating
        a multi-row merged cell. TableBuilder._process_cell_merges() scans rows
        top-to-bottom to detect and execute these merges.

    Edge Cases:
        - Empty cells (cells=[]): Valid, renders as empty row (rare)
        - Single cell: Valid, creates one-column table
        - Variable cell counts: Handled by TableBuilder (pads to max columns)
        - All cells marked merge_left: Invalid (no origin cell), parser should prevent
        - First row with merge_up cells: Invalid (no row above), parser should prevent

    Examples:
        Simple row with plain text cells:
            DocxTableRow(cells=[
                DocxTableCell(content=[TextSpan(text="Name")]),
                DocxTableCell(content=[TextSpan(text="Age")]),
                DocxTableCell(content=[TextSpan(text="City")]),
            ])

        Header row (is_header flags set on cells):
            DocxTableRow(cells=[
                DocxTableCell(content=[TextSpan(text="Header 1")], is_header=True),
                DocxTableCell(content=[TextSpan(text="Header 2")], is_header=True),
            ])

        Row with merged cells (horizontal merge):
            DocxTableRow(cells=[
                DocxTableCell(content=[TextSpan(text="Spans 2 columns")]),
                DocxTableCell(content=[], merge_left=True),  # Merged into previous
                DocxTableCell(content=[TextSpan(text="Separate cell")]),
            ])

        Row with formatted content:
            DocxTableRow(cells=[
                DocxTableCell(content=[
                    TextSpan(text="Bold", bold=True),
                    TextSpan(text=" text"),
                ]),
                DocxTableCell(content=[
                    TextSpan(text="link", link="https://example.com"),
                ]),
            ])

        Empty row:
            DocxTableRow(cells=[])

    Usage:
        DocxTableRow instances are created by DocxRenderer._process_table() when
        parsing Markdown table tokens from mistune. The renderer:
        1. Iterates through row tokens in the table
        2. For each row, iterates through cell tokens
        3. Creates DocxTableCell for each cell (with merge flags if applicable)
        4. Wraps cells list in DocxTableRow
        5. Collects all rows into DocxTable.rows list

        TableBuilder.build() consumes DocxTableRow to create Word table rows:
        1. Iterates through table_element.rows with enumerate to get row_idx
        2. Determines if row is header: is_header_row = (row_idx == 0) and has_header
        3. Gets corresponding Word table row: word_row = table.rows[row_idx]
        4. Sets minimum row height (400 twips = 20pt)
        5. Iterates through cells, filling each with content and styling
        6. Applies alternating row background colors if configured (non-header rows)

    See Also:
        - DocxTable: Parent container for rows (the actual block element)
        - DocxTableCell: Individual cells within a row (contains content and merge flags)
        - TableBuilder.build(): Builds Word tables from DocxTable, processing rows sequentially
        - TableBuilder._fill_cell(): Populates individual cell content and applies styling
        - TableBuilder._process_cell_merges(): Handles vertical/horizontal cell merging
        - StyleMapper.table_config(): Provides table formatting configuration
    """

    cells: list[DocxTableCell]


class DocxTable(DocxElement, frozen=True, tag="table"):
    """Table block element with rows, cells, and optional header row.

    DocxTable represents Markdown tables in the AST, including both simple and complex
    table structures with cell merging, header rows, and formatted content. Tables are
    block-level elements that contain rows (DocxTableRow), which in turn contain cells
    (DocxTableCell). The has_header flag controls whether the first row receives special
    header styling (bold, background color, centered text).

    Attributes:
        rows: List of DocxTableRow objects forming the table structure. Each row
            contains cells (columns), and rows are rendered top-to-bottom in the
            order they appear in this list. Never None, but can be empty for
            zero-row tables (rare but valid).

            Table dimensions:
            - Row count: len(rows)
            - Column count: max(len(row.cells) for row in rows)
            - Irregular tables (rows with different cell counts) are normalized
              to the maximum column count by TableBuilder, padding short rows
              with empty cells

            Row ordering:
            - Index 0: First row (header row if has_header=True)
            - Index 1: Second row (first data row if has_header=True)
            - Index N: Last row

        has_header: Boolean flag indicating whether the first row (rows[0]) should
            receive header cell styling. When True, cells in the first row are
            treated as header cells and rendered with bold font, background color,
            and centered alignment as configured in StyleMapper.table_config().

            Header Row Behavior:
            - has_header=True (default):
                * First row (rows[0]) is the header row
                * TableBuilder sets is_header_row=True for row 0
                * Header cells get special styling: bold, background, centered
                * Remaining rows (1+) are data rows with normal styling
                * Common for tables with column headers (Name | Age | City)
                * Markdown tables always have headers (pipe tables)

            - has_header=False:
                * No row receives header styling
                * All rows (including row 0) are treated as data rows
                * Cells in row 0 are styled the same as other rows
                * Uncommon in Markdown but supported for data-only tables
                * Used for tables without column headers (grid tables)

            Implementation in TableBuilder.build():
                ```python
                for row_idx, row in enumerate(table_element.rows):
                    is_header_row = row_idx == 0 and table_element.has_header
                    # is_header_row determines cell styling in _fill_cell()
                ```

            The has_header flag does NOT affect the AST structure (rows list is
            identical either way) - it only affects rendering/styling. The flag
            is parsed from Markdown table syntax and preserved through to Word
            document building.

    Markdown Table Syntax:
        Markdown tables use pipe (|) delimiters with optional header separator:

        Standard table (has_header=True):
            | Name  | Age | City      |
            |-------|-----|-----------|
            | Alice | 30  | New York  |
            | Bob   | 25  | London    |

        This produces:
            DocxTable(
                rows=[
                    DocxTableRow(cells=[  # Header row (row 0)
                        DocxTableCell(content=[TextSpan(text="Name")], is_header=True),
                        DocxTableCell(content=[TextSpan(text="Age")], is_header=True),
                        DocxTableCell(content=[TextSpan(text="City")], is_header=True),
                    ]),
                    DocxTableRow(cells=[  # Data row (row 1)
                        DocxTableCell(content=[TextSpan(text="Alice")]),
                        DocxTableCell(content=[TextSpan(text="30")]),
                        DocxTableCell(content=[TextSpan(text="New York")]),
                    ]),
                    DocxTableRow(cells=[  # Data row (row 2)
                        DocxTableCell(content=[TextSpan(text="Bob")]),
                        DocxTableCell(content=[TextSpan(text="25")]),
                        DocxTableCell(content=[TextSpan(text="London")]),
                    ]),
                ],
                has_header=True
            )

        The |---|---| separator line is not stored in the AST - it only signals
        that the first row is a header. All content rows become DocxTableRow objects.

    Cell Merging Support:
        DocxTable supports both vertical and horizontal cell merging via special
        Markdown markers (extended Markdown syntax):
        - `^^` marker: Merge cell with cell directly above (vertical merge)
        - `>>` marker: Merge cell with cell to the left (horizontal merge)

        Example with vertical merge:
            | Name  | Details           |
            |-------|-------------------|
            | Alice | Smart             |
            | ^^    | Hard-working      |
            | Bob   | Funny             |

        Produces merged cell spanning rows 1-2 in column 0 (Alice spans 2 rows).

        Example with horizontal merge:
            | Name  | Age | City      |
            |-------|-----|-----------|
            | Alice | 30  | New York  |
            | Bob   | >>  | >>        |

        Produces merged cell spanning all 3 columns in row 2 (Bob's row spans full width).

        Merging is handled by TableBuilder._process_cell_merges(), which:
        1. Scans cells for merge_up and merge_left flags
        2. Groups consecutive merge-flagged cells with their origin cells
        3. Calls Word's cell.merge() to create merged cells
        4. Tracks merged positions to skip during content filling

    Header Styling Configuration:
        Header cell styling is controlled by StyleMapper.table_config(), which
        returns a dictionary with formatting options:
        - header_bg: Background color for header cells (e.g., "4472C4" = blue)
        - header_bold: Whether header text is bold (default True)
        - header_alignment: Text alignment for headers (default center)
        - border_style: Table border style (single, double, none)
        - alternating_rows: Whether to alternate data row colors
        - alt_row_bg: Background color for alternating rows (e.g., "D9E2F3")

        Example table config:
            {
                "header_bg": "4472C4",      # Blue header background
                "header_bold": true,         # Bold header text
                "header_alignment": "center", # Center header text
                "border_style": "single",    # Single-line borders
                "alternating_rows": true,    # Alternate row colors
                "alt_row_bg": "D9E2F3"      # Light blue alt rows
            }

        When has_header=True, row 0 cells receive header styling. When has_header=False,
        no cells receive header styling (all cells use normal data cell formatting).

    Rendering to Word:
        When TableBuilder processes a DocxTable, it:
        1. Creates Word table with dimensions: len(rows) × max(len(row.cells))
        2. Applies table style from StyleMapper (e.g., "Table Grid")
        3. Sets table alignment (typically center)
        4. Calls _process_cell_merges() to handle vertical/horizontal cell merging
        5. Iterates through rows, setting is_header_row = (idx == 0) and has_header
        6. For each cell, calls _fill_cell() with header flag to apply styling:
            - Header cells: bold, background color, centered alignment
            - Data cells: normal font, no background (or alternating row color)
        7. Applies alternating row background colors to non-header rows (if configured)
        8. Sets minimum row height (400 twips = 20pt) for visible vertical centering

        Example Word rendering:
            has_header=True:
                ┌─────────┬─────┬──────────┐
                │ Name    │ Age │ City     │  ← Bold, blue background (header)
                ├─────────┼─────┼──────────┤
                │ Alice   │ 30  │ New York │  ← Normal formatting
                │ Bob     │ 25  │ London   │  ← Light blue bg (alternating)
                └─────────┴─────┴──────────┘

            has_header=False:
                ┌─────────┬─────┬──────────┐
                │ Alice   │ 30  │ New York │  ← Normal formatting (no header)
                │ Bob     │ 25  │ London   │  ← Light blue bg (alternating)
                └─────────┴─────┴──────────┘

    Edge Cases:
        - Empty rows (rows=[]): Valid, renders as empty table (rare)
        - Single row with has_header=True: Entire table is a header row (unusual)
        - Single row with has_header=False: Single data row, no header
        - Irregular row lengths: Normalized to max column count by TableBuilder
        - All cells empty: Valid, renders as empty cells with borders
        - has_header=True with empty rows: No row to be header (renders empty table)
        - Very wide tables: No hard column limit, but readability degrades beyond ~10 columns
        - Very tall tables: No hard row limit, but may span multiple Word pages

    Examples:
        Simple 2×2 table with header:
            DocxTable(
                rows=[
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="Name")], is_header=True),
                        DocxTableCell(content=[TextSpan(text="Age")], is_header=True),
                    ]),
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="Alice")]),
                        DocxTableCell(content=[TextSpan(text="30")]),
                    ]),
                ],
                has_header=True
            )

        Table without header row:
            DocxTable(
                rows=[
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="Data 1")]),
                        DocxTableCell(content=[TextSpan(text="Data 2")]),
                    ]),
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="Data 3")]),
                        DocxTableCell(content=[TextSpan(text="Data 4")]),
                    ]),
                ],
                has_header=False
            )

        Table with cell merging (vertical merge):
            DocxTable(
                rows=[
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="Name")], is_header=True),
                        DocxTableCell(content=[TextSpan(text="Info")], is_header=True),
                    ]),
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="Alice")]),
                        DocxTableCell(content=[TextSpan(text="Smart")]),
                    ]),
                    DocxTableRow(cells=[
                        DocxTableCell(content=[], merge_up=True),  # Merges with "Alice"
                        DocxTableCell(content=[TextSpan(text="Kind")]),
                    ]),
                ],
                has_header=True
            )

        Table with formatted cell content:
            DocxTable(
                rows=[
                    DocxTableRow(cells=[
                        DocxTableCell(content=[
                            TextSpan(text="Name", bold=True)
                        ], is_header=True),
                    ]),
                    DocxTableRow(cells=[
                        DocxTableCell(content=[
                            TextSpan(text="Visit "),
                            TextSpan(text="site", link="https://example.com"),
                        ]),
                    ]),
                ],
                has_header=True
            )

        Empty table:
            DocxTable(rows=[], has_header=True)

    Usage:
        DocxTable instances are created by DocxRenderer.table() when parsing
        Markdown table tokens from mistune. The renderer:
        1. Receives table token with header and body rows from mistune
        2. Extracts header row cells, setting is_header=True on each cell
        3. Wraps header cells in DocxTableRow and adds to rows list
        4. Extracts body row cells, setting is_header=False on each cell
        5. Wraps each body row cells in DocxTableRow and adds to rows list
        6. Detects cell merge markers (^^, >>) and sets merge flags
        7. Returns DocxTable with all rows and has_header=True (Markdown tables always have headers)

        TableBuilder.build() consumes DocxTable to create Word tables:
        1. Validates rows list (empty table → create 0×0 table and return)
        2. Calculates dimensions: num_rows, num_cols (max cell count across rows)
        3. Creates Word table with calculated dimensions
        4. Applies table style and alignment (center)
        5. Calls _process_cell_merges() to execute merge operations
        6. Iterates through rows with row_idx:
            - Sets is_header_row = (row_idx == 0) and has_header
            - Sets minimum row height (400 twips)
            - Iterates through cells, calling _fill_cell() with header flag
            - Applies alternating row colors (if configured and not header)
        7. Returns completed Word Table object

    See Also:
        - DocxTableRow: Individual rows within the table (helper struct)
        - DocxTableCell: Individual cells within rows (contains content and merge flags)
        - TableBuilder.build(): Builds Word tables from DocxTable elements
        - TableBuilder._process_cell_merges(): Handles cell merging (^^, >> markers)
        - TableBuilder._fill_cell(): Populates cells with content and applies styling
        - StyleMapper.table_config(): Provides header and border formatting config
        - StyleMapper.table_style(): Returns Word table style name
        - TextSpan: Formatted text content within table cells
    """

    rows: list[DocxTableRow]
    has_header: bool = True


class DocxImage(DocxElement, frozen=True, tag="image"):
    """Image element with source URL, alternative text, and optional title.

    DocxImage represents embedded images from Markdown image syntax (![alt](url "title")).
    Images can reference external URLs, local file paths, or data URIs. The alt text
    provides accessibility support and fallback content when images cannot be displayed.
    The optional title attribute adds tooltip text in Word documents.

    Attributes:
        src: The image source URL or file path. Can be:
            - HTTP/HTTPS URL: https://example.com/image.png (external image)
            - File path: ./images/diagram.png (relative to document location)
            - Absolute path: /Users/name/Pictures/photo.jpg (local file system)
            - Data URI: data:image/png;base64,... (embedded inline image)

            The src field is never None but can be empty string if Markdown has
            malformed image syntax. When rendering to Word, DocxBuilder validates
            that the image source is accessible and readable before attempting to
            insert it into the document.

        alt: Alternative text for accessibility and fallback display. This text:
            - Appears when the image cannot be loaded or displayed
            - Provides screen reader description for visually impaired users
            - Shows in Word's alt text property for accessibility compliance
            - Defaults to empty string if not specified in Markdown

            While technically optional in Markdown syntax (![](url)), best practice
            is to always provide meaningful alt text describing the image content
            and purpose. Empty alt text is valid but reduces accessibility.

        title: Optional tooltip/title text that appears on hover in Word. Extracted
            from Markdown image syntax after the URL: ![alt](url "hover title").
            When None, no tooltip is set. When present, Word displays this text when
            users hover over the image. Common uses include:
            - Image credits or attribution
            - Additional context or explanation
            - Figure numbers or captions (e.g., "Figure 1: Architecture diagram")

            The title is distinct from alt text: alt text is for accessibility and
            describes what the image shows, while title text provides supplementary
            information for sighted users.

    Markdown Syntax Examples:
        Basic image:
            ![Logo](logo.png) → DocxImage(src="logo.png", alt="Logo", title=None)

        Image with title:
            ![Chart](chart.png "Sales by Quarter")
            → DocxImage(src="chart.png", alt="Chart", title="Sales by Quarter")

        External image:
            ![Photo](https://example.com/photo.jpg)
            → DocxImage(src="https://example.com/photo.jpg", alt="Photo", title=None)

        Empty alt text (valid but not recommended):
            ![](diagram.png) → DocxImage(src="diagram.png", alt="", title=None)

    Rendering to Word:
        When DocxBuilder processes a DocxImage, it:
        1. Validates that the image source exists and is readable
        2. Creates a new Word paragraph to contain the image
        3. Inserts the image using python-docx's add_picture() method
        4. Sets the alt text property for accessibility (if alt is non-empty)
        5. Sets the title/tooltip property (if title is not None)
        6. Optionally resizes the image to fit page width while preserving aspect ratio
        7. Centers the image paragraph (configurable via styles-mapping.yaml)

        Image sizing follows these rules:
        - Preserves original aspect ratio (no distortion)
        - Scales down large images to fit page width (typically 6.5 inches)
        - Leaves small images at original size (no upscaling)
        - Respects maximum dimensions from configuration

    Supported Image Formats:
        Word documents support common image formats via python-docx:
        - PNG (.png): Recommended for diagrams, logos, screenshots
        - JPEG (.jpg, .jpeg): Recommended for photos
        - GIF (.gif): Supported but may lose animation
        - BMP (.bmp): Supported but creates large file sizes
        - TIFF (.tiff): Supported for high-quality images
        - SVG (.svg): NOT supported by python-docx (must be converted to PNG/JPEG)

        Data URIs (base64-encoded images) are supported but increase document
        file size significantly and should be used sparingly.

    Edge Cases:
        - src="" (empty): Valid but image won't render; DocxBuilder may skip or warn
        - alt="" (empty): Valid but reduces accessibility; image has no description
        - title="" (empty string): Treated as None (no tooltip)
        - Missing file: DocxBuilder logs warning and skips image to avoid crashing
        - Invalid URL: DocxBuilder handles gracefully (may skip or use placeholder)
        - Very large images: Automatically scaled down to fit page width
        - Unsupported format (SVG): DocxBuilder may skip or attempt conversion

    Examples:
        Simple diagram:
            DocxImage(
                src="./diagrams/architecture.png",
                alt="System architecture diagram showing three-tier design",
                title=None
            )

        External photo with title:
            DocxImage(
                src="https://example.com/team-photo.jpg",
                alt="Engineering team at 2024 offsite",
                title="Photo credit: Jane Smith"
            )

        Data URI for small icon:
            DocxImage(
                src="data:image/png;base64,iVBORw0KGgoAAAANS...",
                alt="Success checkmark icon",
                title="Indicates successful completion"
            )

        Markdown screenshot (common in technical docs):
            DocxImage(
                src="./screenshots/login-screen.png",
                alt="Application login screen with username and password fields",
                title="Figure 1: Login interface"
            )

    Usage:
        DocxImage instances are created by DocxRenderer.image() when parsing Markdown
        image syntax. The renderer extracts src, alt, and title from the mistune token
        attributes and constructs the DocxImage element. DocxBuilder then processes
        these elements to insert actual images into the Word document using python-docx.

    See Also:
        - DocxParagraph: Images are inserted as their own paragraphs
        - DocxBuilder._build_image(): Handles Word document image insertion
        - python-docx add_picture(): Underlying Word image API
    """

    src: str
    alt: str = ""
    title: str | None = None


class DocxHorizontalRule(DocxElement, frozen=True, tag="hr"):
    """Horizontal rule element representing a thematic break or section divider.

    DocxHorizontalRule represents Markdown horizontal rules (also called thematic
    breaks), created by three or more hyphens (---), asterisks (***), or underscores
    (___) on a line by themselves. These elements visually separate document sections
    and indicate a thematic shift in content, similar to an HTML <hr> tag or a scene
    break in fiction writing.

    This element has no attributes - it's a simple marker indicating "insert horizontal
    line here". The visual appearance (line style, thickness, color, spacing) is
    controlled entirely by Word document styling configured in styles-mapping.yaml
    and applied by DocxBuilder.

    Markdown Syntax:
        All of these produce DocxHorizontalRule:

        Three hyphens:
            ---

        Three asterisks:
            ***

        Three underscores:
            ___

        More than three (any of the above):
            -----
            *****
            _____

        With spaces between:
            - - -
            * * *
            _ _ _

        All variations are equivalent and produce the same DocxHorizontalRule
        element. The choice of character (-, *, _) and quantity (3+) is purely
        stylistic in Markdown - they all render identically in Word documents.

    Rendering to Word:
        When DocxBuilder processes a DocxHorizontalRule, it:
        1. Creates a new Word paragraph
        2. Applies the "Horizontal Rule" style from styles-mapping.yaml
        3. Inserts a horizontal line using one of these methods:
           - Border on paragraph (top or bottom border styled as line)
           - Special character (em dash or horizontal line Unicode character)
           - Shape object (actual line drawing, if supported)

        The exact rendering method depends on DocxBuilder implementation and
        style configuration. Common approaches:
        - Single-line paragraph border: Lightweight, clean, adjusts to page width
        - Repeated characters (e.g., em dashes): Simple but less elegant
        - Word shape: Most flexible but more complex

        Styling options (configured in styles-mapping.yaml):
        - Line thickness (border width)
        - Line color (border color or font color)
        - Line style (solid, dashed, dotted, double)
        - Spacing above and below (paragraph spacing)
        - Alignment (left, center, right, full width)
        - Width (full page width vs. partial width)

    Common Use Cases:
        1. Section dividers: Separate major sections in long documents
            Example:
                # Chapter 1
                Content here...
                ---
                # Chapter 2
                More content...

        2. Topic transitions: Signal shift in topic within a section
            Example:
                Discussing feature A...
                ***
                Now discussing feature B...

        3. Visual breaks: Add visual breathing room in dense content
            Example:
                Technical explanation...
                ___
                Related example...

        4. Signature lines: Separate signature blocks in formal documents
            Example:
                Sincerely,
                ---
                John Doe

    Edge Cases:
        - Multiple consecutive horizontal rules: Each renders as separate line
          (though this is unusual and may indicate formatting mistake)
        - Horizontal rule at start/end of document: Valid, renders normally
        - Inside blockquotes or lists: Valid in Markdown, but some parsers
          may handle differently (mistune treats as thematic break regardless)
        - Very narrow page: Line adjusts to available width automatically

    Semantic Meaning:
        Unlike a simple blank line (which adds vertical space), a horizontal rule
        carries semantic meaning: it indicates a thematic break or transition in
        content. This is important for:
        - Document structure: Signals topic boundaries to readers
        - Screen readers: May announce "horizontal rule" or "section break"
        - Accessibility: Provides structural landmark for navigation
        - Conversion: Preserves semantic meaning when converting between formats

    Examples:
        Section divider in chapter:
            Markdown:
                ## Introduction
                This chapter covers...
                ---
                ## Getting Started
                First, install...

            AST:
                [
                    DocxHeading(level=2, content=[...], anchor="introduction"),
                    DocxParagraph(content=[...]),
                    DocxHorizontalRule(),
                    DocxHeading(level=2, content=[...], anchor="getting-started"),
                    DocxParagraph(content=[...]),
                ]

        Separating related sections:
            Markdown:
                API v1 is deprecated.
                ***
                API v2 is recommended for new projects.

            AST:
                [
                    DocxParagraph(content=[TextSpan(text="API v1 is deprecated.")]),
                    DocxHorizontalRule(),
                    DocxParagraph(content=[TextSpan(text="API v2 is recommended...")]),
                ]

    Usage:
        DocxHorizontalRule instances are created by DocxRenderer.thematic_break()
        when parsing Markdown thematic break syntax (---, ***, ___). Since the
        element has no attributes, creation is trivial: simply return a new
        DocxHorizontalRule() instance. DocxBuilder._build_horizontal_rule() then
        handles inserting the visual line into the Word document.

    See Also:
        - DocxParagraph: Horizontal rules are distinct from empty paragraphs
        - DocxBuilder._build_horizontal_rule(): Word document rendering logic
        - styles-mapping.yaml: Configuration for horizontal rule visual styling
    """

    pass


AdmonitionType = Literal["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]


class DocxAdmonition(DocxElement, frozen=True, tag="admonition"):
    """Admonition/callout block for highlighted notes, warnings, and tips.

    DocxAdmonition represents GitHub-style admonition/callout blocks that highlight
    important information with visual styling. These are created using Markdown
    blockquote syntax with special markers like `> [!NOTE]`, `> [!WARNING]`, etc.
    Admonitions render as styled tables in Word documents with colored borders,
    backgrounds, and icons to draw attention to critical information.

    Admonitions are commonly used in technical documentation to:
    - Highlight important warnings or cautions
    - Provide helpful tips or best practices
    - Emphasize critical notes or prerequisites
    - Call out important information that shouldn't be missed

    Attributes:
        admonition_type: The type of admonition, which determines visual styling
            (color, icon, semantic meaning). Must be one of five predefined types:

            - "NOTE": General information, neutral tone. Blue styling (default).
              Use for supplementary information, clarifications, or context that
              readers should be aware of but isn't critical.
              Example: "Note: This feature requires Python 3.11 or higher."

            - "TIP": Helpful suggestions or best practices. Green styling.
              Use for optional optimizations, shortcuts, or recommendations that
              improve the user experience but aren't strictly necessary.
              Example: "Tip: Enable caching to improve performance by 50%."

            - "IMPORTANT": Critical information that must not be ignored. Purple styling.
              Use for essential information that significantly affects outcomes,
              key prerequisites, or important concepts that are easy to overlook.
              Example: "Important: Back up your data before upgrading."

            - "WARNING": Alerts about potential problems or risks. Orange styling.
              Use for actions that might cause issues, limitations, or situations
              where users need to proceed with caution.
              Example: "Warning: This operation cannot be undone."

            - "CAUTION": Severe warnings about dangerous or destructive actions. Red styling.
              Use for operations that could cause data loss, security vulnerabilities,
              or system damage if performed incorrectly.
              Example: "Caution: Running this command will delete all user data."

            The type is case-insensitive in Markdown ([!note], [!NOTE], [!Note] all
            work) but normalized to uppercase by DocxRenderer. Visual styling (colors,
            icons, background) is configured in styles-mapping.yaml under the
            "admonitions" section and applied by AdmonitionBuilder.

        title: Optional custom title text for the admonition. When specified, appears
            as bold text at the start of the admonition content. When None, no explicit
            title is shown (only the admonition type is indicated by icon and styling).

            Title extraction from Markdown:
            - `> [!NOTE]` → title=None (no custom title)
            - `> [!NOTE] Custom Title` → title="Custom Title"
            - `> [!WARNING] Database Migration` → title="Database Migration"

            The title is extracted by DocxRenderer from text following the admonition
            marker on the same line. If present, it's stored separately from the
            content and typically rendered with bold or emphasized styling.

            When title is None, some rendering implementations may use the admonition
            type as a default title (e.g., showing "Note:" or "Warning:"), but this
            behavior is controlled by AdmonitionBuilder, not the AST element itself.

        children: List of block-level elements contained within the admonition.
            Can include paragraphs, lists, code blocks, or other block elements.
            The children list is never None but can be empty (though empty admonitions
            are rare and may indicate malformed Markdown).

            Typical patterns:
            - Single paragraph: Most common, simple note with one sentence
            - Multiple paragraphs: Longer explanation or multi-part warning
            - List inside admonition: Enumerated steps or multiple points
            - Code block inside admonition: Example or command to note
            - Mixed content: Paragraphs, lists, and code combined

            All children are rendered within the admonition's styled container
            (typically a colored table cell in Word), inheriting the admonition's
            visual styling (background color, text color, border).

    GitHub-Style Markdown Syntax:
        Admonitions use blockquote syntax with special markers:

        Basic admonition (no custom title):
            > [!NOTE]
            > This is important information to note.

        Admonition with custom title:
            > [!WARNING] Database Changes
            > This operation will modify the database schema.

        Multi-paragraph admonition:
            > [!TIP]
            > First paragraph of the tip.
            >
            > Second paragraph with more details.

        Admonition with list:
            > [!IMPORTANT]
            > Before proceeding, ensure:
            > - You have admin access
            > - The database is backed up
            > - All users are logged out

        Admonition with code block:
            > [!CAUTION]
            > Do not run this command in production:
            > ```bash
            > rm -rf /
            > ```

        The `> ` prefix on each line is standard blockquote syntax. The `[!TYPE]`
        marker on the first line signals an admonition. Text after the marker
        becomes the custom title (if present).

    Rendering to Word:
        When DocxBuilder processes a DocxAdmonition, it delegates to AdmonitionBuilder,
        which:
        1. Creates a two-column table (icon column + content column)
        2. Applies background color based on admonition type (from styles-mapping.yaml)
        3. Inserts a colored left border (3pt thick, type-specific color)
        4. Adds an icon in the left cell (e.g., "i" for NOTE, "!" for WARNING)
        5. Renders children elements in the right cell with appropriate styling
        6. Centers icon vertically and horizontally in its cell
        7. Applies text color matching the admonition type

        Color scheme (default, configurable in styles-mapping.yaml):
        - NOTE: Blue (#0969DA background, #DDF4FF border)
        - TIP: Green (#1F883D background, #D1F4DD border)
        - IMPORTANT: Purple (#8250DF background, #EAD9FF border)
        - WARNING: Orange (#9A6700 background, #FFF8C5 border)
        - CAUTION: Red (#CF222E background, #FFDBDB border)

        The table structure ensures:
        - Icon and content are visually aligned
        - Background color fills entire admonition area
        - Border clearly marks admonition boundaries
        - Content can wrap and flow naturally

    Comparison with DocxBlockquote:
        Both admonitions and blockquotes use Markdown blockquote syntax (`> `), but
        they are semantically and visually different:

        DocxBlockquote:
        - Plain quotation or indented content
        - No special markers (`[!TYPE]`)
        - Simple indentation styling in Word
        - Used for citations, quotes, or generic indentation

        DocxAdmonition:
        - Highlighted callout with semantic type
        - Requires `[!TYPE]` marker
        - Rich visual styling (colors, icons, borders)
        - Used for warnings, tips, important notes

        DocxRenderer distinguishes between them by checking for the `[!TYPE]` pattern
        in the first paragraph of a blockquote. If found, it creates a DocxAdmonition;
        otherwise, it creates a DocxBlockquote.

    Edge Cases:
        - Empty children list: Valid but unusual, renders as empty styled box
        - title="" (empty string): Treated as None (no custom title)
        - Invalid admonition type: Not possible due to Literal type constraint,
          but renderer validation ensures only valid types are used
        - Nested admonitions: Markdown doesn't support this well; typically results
          in nested blockquote content rather than nested admonitions
        - Admonition as first/last element: Valid, renders normally
        - Very long content: Table cell expands vertically to accommodate all children

    Examples:
        Simple note:
            Markdown:
                > [!NOTE]
                > Remember to save your work frequently.

            AST:
                DocxAdmonition(
                    admonition_type="NOTE",
                    title=None,
                    children=[
                        DocxParagraph(content=[
                            TextSpan(text="Remember to save your work frequently.")
                        ])
                    ]
                )

        Warning with custom title:
            Markdown:
                > [!WARNING] Breaking Change
                > Version 2.0 removes deprecated APIs.

            AST:
                DocxAdmonition(
                    admonition_type="WARNING",
                    title="Breaking Change",
                    children=[
                        DocxParagraph(content=[
                            TextSpan(text="Version 2.0 removes deprecated APIs.")
                        ])
                    ]
                )

        Multi-paragraph tip:
            Markdown:
                > [!TIP]
                > Use keyboard shortcuts to work faster.
                >
                > Press Ctrl+S to save, Ctrl+Z to undo.

            AST:
                DocxAdmonition(
                    admonition_type="TIP",
                    title=None,
                    children=[
                        DocxParagraph(content=[
                            TextSpan(text="Use keyboard shortcuts to work faster.")
                        ]),
                        DocxParagraph(content=[
                            TextSpan(text="Press Ctrl+S to save, Ctrl+Z to undo.")
                        ])
                    ]
                )

        Important note with list:
            Markdown:
                > [!IMPORTANT] Prerequisites
                > - Python 3.11+
                > - 2GB free disk space
                > - Admin permissions

            AST:
                DocxAdmonition(
                    admonition_type="IMPORTANT",
                    title="Prerequisites",
                    children=[
                        DocxList(
                            ordered=False,
                            items=[
                                DocxListItem(content=[...]),
                                DocxListItem(content=[...]),
                                DocxListItem(content=[...]),
                            ]
                        )
                    ]
                )

    Usage:
        DocxAdmonition instances are created by DocxRenderer.block_quote() when
        parsing Markdown blockquotes that start with the `[!TYPE]` pattern. The
        renderer:
        1. Parses blockquote children to get list of elements
        2. Checks if first paragraph starts with ADMONITION_PATTERN regex
        3. Extracts admonition type and optional title from the match
        4. Removes the `[!TYPE]` marker from content
        5. Returns DocxAdmonition with type, title, and children
        6. If no match, returns DocxBlockquote instead

        AdmonitionBuilder.build() then processes DocxAdmonition elements to create
        styled tables in Word documents with appropriate colors, icons, and formatting.

    See Also:
        - DocxBlockquote: Plain blockquotes without admonition markers
        - AdmonitionBuilder: Handles Word document rendering for admonitions
        - DocxRenderer.block_quote(): Creates admonitions from Markdown
        - styles-mapping.yaml: Configures admonition colors and styling
    """

    admonition_type: AdmonitionType
    title: str | None = None
    children: list[DocxElement] = msgspec.field(default_factory=list)


# Type alias for document content
Document = list[DocxElement]
