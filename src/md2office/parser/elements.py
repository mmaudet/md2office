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
    """A single list item."""

    content: list[TextSpan]
    children: list[DocxElement] = msgspec.field(default_factory=list)


class DocxList(DocxElement, frozen=True, tag="list"):
    """Ordered or unordered list."""

    ordered: bool
    items: list[DocxListItem]
    start: int = 1


class DocxTableCell(msgspec.Struct, frozen=True):
    """Table cell."""

    content: list[TextSpan]
    is_header: bool = False
    colspan: int = 1
    rowspan: int = 1
    merge_up: bool = False  # Indicates cell should merge with cell above (^^)
    merge_left: bool = False  # Indicates cell should merge with cell to the left (>>)


class DocxTableRow(msgspec.Struct, frozen=True):
    """Table row."""

    cells: list[DocxTableCell]


class DocxTable(DocxElement, frozen=True, tag="table"):
    """Table element."""

    rows: list[DocxTableRow]
    has_header: bool = True


class DocxImage(DocxElement, frozen=True, tag="image"):
    """Image element."""

    src: str
    alt: str = ""
    title: str | None = None


class DocxHorizontalRule(DocxElement, frozen=True, tag="hr"):
    """Horizontal rule / thematic break."""

    pass


AdmonitionType = Literal["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]


class DocxAdmonition(DocxElement, frozen=True, tag="admonition"):
    """Admonition/callout block (NOTE, WARNING, etc.)."""

    admonition_type: AdmonitionType
    title: str | None = None
    children: list[DocxElement] = msgspec.field(default_factory=list)


# Type alias for document content
Document = list[DocxElement]
