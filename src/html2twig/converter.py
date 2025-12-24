"""
Core HTML to Twig converter module.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup, Tag, NavigableString


@dataclass
class ConversionReport:
    """Stores all conversions and suggestions made during the conversion process."""

    input_file: str
    output_file: str
    layout: Optional[str] = None
    asset_conversions: list = field(default_factory=list)
    block_suggestions: list = field(default_factory=list)
    loop_conversions: list = field(default_factory=list)
    manual_suggestions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_asset(self, original: str, converted: str, tag_type: str):
        self.asset_conversions.append(
            {"original": original, "converted": converted, "type": tag_type}
        )

    def add_block(self, name: str, reason: str):
        self.block_suggestions.append({"name": name, "reason": reason})

    def add_loop(self, element: str, items_var: str, item_var: str):
        self.loop_conversions.append(
            {"element": element, "items_var": items_var, "item_var": item_var}
        )

    def add_suggestion(self, suggestion: str):
        self.manual_suggestions.append(suggestion)

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def generate_text(self) -> str:
        """Generate a text report of all conversions."""
        lines = [
            "=" * 70,
            "HTML TO TWIG CONVERSION REPORT",
            "=" * 70,
            "",
            f"Input:  {self.input_file}",
            f"Output: {self.output_file}",
        ]

        if self.layout:
            lines.append(f"Layout: {self.layout}")

        lines.extend(["", "-" * 70, "ASSET CONVERSIONS", "-" * 70])

        if self.asset_conversions:
            for conv in self.asset_conversions:
                lines.append(f"  [{conv['type'].upper()}]")
                lines.append(f"    Before: {conv['original']}")
                lines.append(f"    After:  {conv['converted']}")
                lines.append("")
        else:
            lines.append("  No asset conversions performed.")
            lines.append("")

        lines.extend(["-" * 70, "BLOCK SUGGESTIONS", "-" * 70])

        if self.block_suggestions:
            for block in self.block_suggestions:
                lines.append(f"  {{% block {block['name']} %}}")
                lines.append(f"    Reason: {block['reason']}")
                lines.append("")
        else:
            lines.append("  No block suggestions.")
            lines.append("")

        lines.extend(["-" * 70, "LOOP CONVERSIONS", "-" * 70])

        if self.loop_conversions:
            for loop in self.loop_conversions:
                lines.append(f"  Element: {loop['element']}")
                lines.append(f"    {{% for {loop['item_var']} in {loop['items_var']} %}}")
                lines.append("")
        else:
            lines.append("  No loop conversions performed.")
            lines.append("")

        lines.extend(["-" * 70, "MANUAL REVIEW SUGGESTIONS", "-" * 70])

        if self.manual_suggestions:
            for i, suggestion in enumerate(self.manual_suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
            lines.append("")
        else:
            lines.append("  No manual review needed.")
            lines.append("")

        if self.warnings:
            lines.extend(["-" * 70, "WARNINGS", "-" * 70])
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")

        lines.extend(["=" * 70, "END OF REPORT", "=" * 70])

        return "\n".join(lines)


class HTMLToTwigConverter:
    """Converts HTML templates to Twig templates for Symfony."""

    # Patterns for detecting asset paths
    ASSET_PATTERNS = {
        "images": re.compile(r"^(?:\.\.?/)*(?:assets?/)?(?:img|images?)/(.+)$", re.IGNORECASE),
        "css": re.compile(r"^(?:\.\.?/)*(?:assets?/)?(?:css|styles?)/(.+)$", re.IGNORECASE),
        "js": re.compile(r"^(?:\.\.?/)*(?:assets?/)?(?:js|scripts?|javascript)/(.+)$", re.IGNORECASE),
        "fonts": re.compile(r"^(?:\.\.?/)*(?:assets?/)?fonts?/(.+)$", re.IGNORECASE),
    }

    # Navigation element patterns
    NAV_SELECTORS = ["nav", "ul.nav", "ul.menu", "ul.navbar-nav", ".navigation", ".main-menu"]

    # Common block patterns
    BLOCK_PATTERNS = {
        "header": ["header", ".header", "#header", "[role='banner']"],
        "footer": ["footer", ".footer", "#footer", "[role='contentinfo']"],
        "sidebar": [".sidebar", "#sidebar", "aside", "[role='complementary']"],
        "content": ["main", ".content", "#content", ".main-content", "[role='main']"],
        "title": ["title"],
        "stylesheets": ["head"],
        "javascripts": ["body"],
    }

    def __init__(self, layout: Optional[str] = None):
        """
        Initialize the converter.

        Args:
            layout: Name of the base layout to extend (e.g., 'base' for base.html.twig)
        """
        self.layout = layout
        self.report: Optional[ConversionReport] = None
        self.soup: Optional[BeautifulSoup] = None

    def convert_file(
        self, input_path: str, output_path: str, generate_report: bool = True
    ) -> tuple[str, Optional[ConversionReport]]:
        """
        Convert an HTML file to Twig.

        Args:
            input_path: Path to the input HTML file
            output_path: Path to the output Twig file

        Returns:
            Tuple of (converted content, report)
        """
        with open(input_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.report = ConversionReport(
            input_file=input_path, output_file=output_path, layout=self.layout
        )

        twig_content = self.convert(html_content)

        # Save output
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(twig_content)

        # Generate report
        if generate_report:
            report_path = str(output_path).rsplit(".", 1)[0] + "_report.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(self.report.generate_text())

        return twig_content, self.report

    def convert(self, html_content: str) -> str:
        """
        Convert HTML content to Twig.

        Args:
            html_content: The HTML content to convert

        Returns:
            Converted Twig template content
        """
        self.soup = BeautifulSoup(html_content, "lxml")

        # Convert assets
        self._convert_images()
        self._convert_stylesheets()
        self._convert_scripts()
        self._convert_other_assets()

        # Detect and convert navigation menus
        self._convert_navigation()

        # Detect repetitive patterns
        self._detect_blocks()

        # Detect other repetitive elements
        self._detect_repetitive_elements()

        # Generate Twig output
        twig_content = self._generate_twig_output()

        return twig_content

    def _convert_images(self):
        """Convert image src attributes to Twig asset() calls."""
        for img in self.soup.find_all("img"):
            src = img.get("src", "")
            if src and not src.startswith(("http://", "https://", "//", "data:", "{{")):
                new_src = self._convert_asset_path(src, "images")
                if new_src != src:
                    self.report.add_asset(src, new_src, "img")
                    img["src"] = new_src

            # Also handle srcset
            srcset = img.get("srcset", "")
            if srcset and not srcset.startswith("{{"):
                new_srcset = self._convert_srcset(srcset)
                if new_srcset != srcset:
                    img["srcset"] = new_srcset

    def _convert_stylesheets(self):
        """Convert stylesheet href attributes to Twig asset() calls."""
        for link in self.soup.find_all("link", rel="stylesheet"):
            href = link.get("href", "")
            if href and not href.startswith(("http://", "https://", "//", "{{")):
                new_href = self._convert_asset_path(href, "css")
                if new_href != href:
                    self.report.add_asset(href, new_href, "css")
                    link["href"] = new_href

        # Also handle <style> with @import
        for style in self.soup.find_all("style"):
            if style.string:
                new_content = self._convert_css_imports(style.string)
                if new_content != style.string:
                    style.string = new_content

    def _convert_scripts(self):
        """Convert script src attributes to Twig asset() calls."""
        for script in self.soup.find_all("script", src=True):
            src = script.get("src", "")
            if src and not src.startswith(("http://", "https://", "//", "{{")):
                new_src = self._convert_asset_path(src, "js")
                if new_src != src:
                    self.report.add_asset(src, new_src, "js")
                    script["src"] = new_src

    def _convert_other_assets(self):
        """Convert other asset references (fonts, favicons, etc.)."""
        # Favicons and icons
        for link in self.soup.find_all("link", rel=lambda x: x and "icon" in x.lower()):
            href = link.get("href", "")
            if href and not href.startswith(("http://", "https://", "//", "{{")):
                new_href = self._convert_asset_path(href, "images")
                if new_href != href:
                    self.report.add_asset(href, new_href, "favicon")
                    link["href"] = new_href

        # Background images in inline styles
        for elem in self.soup.find_all(style=True):
            style = elem["style"]
            new_style = self._convert_inline_style_urls(style)
            if new_style != style:
                elem["style"] = new_style

        # Source elements (for picture, video, audio)
        for source in self.soup.find_all("source"):
            src = source.get("src", "")
            srcset = source.get("srcset", "")
            if src and not src.startswith(("http://", "https://", "//", "{{")):
                new_src = self._convert_asset_path(src, "images")
                if new_src != src:
                    self.report.add_asset(src, new_src, "source")
                    source["src"] = new_src
            if srcset and not srcset.startswith("{{"):
                new_srcset = self._convert_srcset(srcset)
                if new_srcset != srcset:
                    source["srcset"] = new_srcset

        # Video poster attributes
        for video in self.soup.find_all("video"):
            poster = video.get("poster", "")
            if poster and not poster.startswith(("http://", "https://", "//", "{{")):
                new_poster = self._convert_asset_path(poster, "images")
                if new_poster != poster:
                    self.report.add_asset(poster, new_poster, "video-poster")
                    video["poster"] = new_poster

    def _convert_asset_path(self, path: str, default_type: str = "images") -> str:
        """
        Convert a relative asset path to a Twig asset() call.

        Args:
            path: The original asset path
            default_type: Default asset type if pattern doesn't match

        Returns:
            Twig asset() expression or original path if external
        """
        if not path or path.startswith(("http://", "https://", "//", "data:", "{{")):
            return path

        # Clean the path
        clean_path = path.strip()

        # Try to match against known patterns
        for asset_type, pattern in self.ASSET_PATTERNS.items():
            match = pattern.match(clean_path)
            if match:
                filename = match.group(1)
                return f"{{{{ asset('{asset_type}/{filename}') }}}}"

        # Fallback: use the path as-is with default type
        # Remove leading ./ or ../
        clean_path = re.sub(r"^(?:\.\.?/)+", "", clean_path)

        # Determine asset type from extension
        ext = Path(clean_path).suffix.lower()
        if ext in [".css", ".scss", ".sass", ".less"]:
            return f"{{{{ asset('css/{clean_path}') }}}}"
        elif ext in [".js", ".mjs", ".ts"]:
            return f"{{{{ asset('js/{clean_path}') }}}}"
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".avif"]:
            return f"{{{{ asset('images/{clean_path}') }}}}"
        elif ext in [".woff", ".woff2", ".ttf", ".otf", ".eot"]:
            return f"{{{{ asset('fonts/{clean_path}') }}}}"
        else:
            return f"{{{{ asset('{clean_path}') }}}}"

    def _convert_srcset(self, srcset: str) -> str:
        """Convert srcset attribute values to Twig asset() calls."""
        parts = srcset.split(",")
        new_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Split into URL and descriptor
            tokens = part.split()
            if tokens:
                url = tokens[0]
                descriptor = " ".join(tokens[1:]) if len(tokens) > 1 else ""
                new_url = self._convert_asset_path(url, "images")
                if descriptor:
                    new_parts.append(f"{new_url} {descriptor}")
                else:
                    new_parts.append(new_url)
        return ", ".join(new_parts)

    def _convert_css_imports(self, css_content: str) -> str:
        """Convert @import url() in CSS to Twig asset() calls."""
        import_pattern = re.compile(r'@import\s+url\(["\']?([^"\')\s]+)["\']?\)', re.IGNORECASE)

        def replace_import(match):
            url = match.group(1)
            if url.startswith(("http://", "https://", "//")):
                return match.group(0)
            new_url = self._convert_asset_path(url, "css")
            return f"@import url('{new_url}')"

        return import_pattern.sub(replace_import, css_content)

    def _convert_inline_style_urls(self, style: str) -> str:
        """Convert url() in inline styles to Twig asset() calls."""
        url_pattern = re.compile(r'url\(["\']?([^"\')\s]+)["\']?\)', re.IGNORECASE)

        def replace_url(match):
            url = match.group(1)
            if url.startswith(("http://", "https://", "//", "data:")):
                return match.group(0)
            new_url = self._convert_asset_path(url, "images")
            # Remove the outer {{ }} for use inside url()
            if new_url.startswith("{{ ") and new_url.endswith(" }}"):
                inner = new_url[3:-3]
                return f"url('{inner}')"
            return f"url('{new_url}')"

        return url_pattern.sub(replace_url, style)

    def _convert_navigation(self):
        """Detect and convert navigation menus to Twig for loops."""
        for selector in self.NAV_SELECTORS:
            navs = self.soup.select(selector)
            for nav in navs:
                self._convert_nav_element(nav)

    def _convert_nav_element(self, nav: Tag):
        """Convert a navigation element to use Twig for loops."""
        # Find the list items
        items = nav.find_all("li", recursive=True)
        if len(items) < 2:
            return

        # Check if items have similar structure (likely a menu)
        first_item = items[0]
        similar_count = 0
        for item in items[1:]:
            if self._elements_similar(first_item, item):
                similar_count += 1

        # If more than half are similar, suggest a loop
        if similar_count >= len(items) // 2:
            # Find the parent ul
            parent_ul = nav.find("ul") if nav.name != "ul" else nav
            if parent_ul:
                menu_name = self._detect_menu_name(nav)
                self._wrap_nav_items(parent_ul, items, menu_name)
                self.report.add_loop(
                    f"<nav> / <ul> menu", f"{menu_name}_items", "item"
                )
                self.report.add_suggestion(
                    f"Review the '{menu_name}' navigation loop and adjust variable names as needed."
                )

    def _detect_menu_name(self, nav: Tag) -> str:
        """Detect a suitable name for the navigation menu."""
        # Try to get from id or class
        if nav.get("id"):
            return nav["id"].replace("-", "_")
        classes = nav.get("class", [])
        for cls in classes:
            if "nav" in cls.lower() or "menu" in cls.lower():
                return cls.replace("-", "_")
        # Check for aria-label
        if nav.get("aria-label"):
            return nav["aria-label"].lower().replace(" ", "_").replace("-", "_")
        return "menu"

    def _elements_similar(self, elem1: Tag, elem2: Tag) -> bool:
        """Check if two elements have similar structure."""
        if elem1.name != elem2.name:
            return False
        # Check if they have similar child structure
        children1 = [c.name for c in elem1.children if isinstance(c, Tag)]
        children2 = [c.name for c in elem2.children if isinstance(c, Tag)]
        return children1 == children2

    def _wrap_nav_items(self, parent_ul: Tag, items: list, menu_name: str):
        """Wrap navigation items in a Twig for loop."""
        if not items:
            return

        # Create the loop template based on the first item
        first_item = items[0]

        # Build the loop item template
        link = first_item.find("a")
        if link:
            # Create Twig variable placeholders
            original_href = link.get("href", "#")
            original_text = link.get_text(strip=True)

            # Replace with Twig variables
            link["href"] = "{{ item.url }}"

            # Replace text content
            if link.string:
                link.string = "{{ item.label }}"
            else:
                # More complex content, add a comment
                for child in link.children:
                    if isinstance(child, NavigableString) and child.strip():
                        child.replace_with("{{ item.label }}")
                        break

        # Add class handling for active state
        item_classes = first_item.get("class", [])
        if item_classes:
            class_str = " ".join(item_classes)
            first_item["class"] = f"{class_str} {{{{ item.active ? 'active' : '' }}}}"
        else:
            first_item["class"] = "{{ item.active ? 'active' : '' }}"

        # Create the for loop wrapper
        loop_start = self.soup.new_string(f"{{% for item in {menu_name}_items %}}\n")
        loop_end = self.soup.new_string("\n{% endfor %}")

        # Insert loop markers
        first_item.insert_before(loop_start)

        # Remove other items and add endfor after first
        for item in items[1:]:
            item.decompose()

        first_item.insert_after(loop_end)

    def _detect_blocks(self):
        """Detect common block patterns and suggest Twig blocks."""
        for block_name, selectors in self.BLOCK_PATTERNS.items():
            for selector in selectors:
                try:
                    elements = self.soup.select(selector)
                    if elements:
                        self.report.add_block(
                            block_name, f"Detected {selector} element(s)"
                        )
                        break
                except Exception:
                    continue

    def _detect_repetitive_elements(self):
        """Detect repetitive patterns that might need loops."""
        # Look for repeated similar elements (cards, list items, etc.)
        containers = self.soup.find_all(["div", "section", "article"])

        for container in containers:
            children = [c for c in container.children if isinstance(c, Tag)]
            if len(children) < 3:
                continue

            # Check for similar children
            first_child = children[0]
            similar_count = sum(
                1 for c in children[1:] if self._elements_similar(first_child, c)
            )

            if similar_count >= 2:
                container_id = container.get("id", container.get("class", ["container"])[0] if container.get("class") else "container")
                self.report.add_suggestion(
                    f"Consider using a for loop for repeated elements in '{container_id}' "
                    f"({similar_count + 1} similar children found)"
                )

    def _generate_twig_output(self) -> str:
        """Generate the final Twig template output."""
        # Get the HTML output
        html_output = str(self.soup)

        # Clean up the output
        html_output = self._cleanup_html_output(html_output)

        # Add extends and blocks if layout is specified
        if self.layout:
            html_output = self._add_layout_structure(html_output)

        return html_output

    def _cleanup_html_output(self, html: str) -> str:
        """Clean up the HTML output for better Twig formatting."""
        # Fix double-escaped Twig syntax
        html = html.replace("&lt;%", "{%")
        html = html.replace("%&gt;", "%}")
        html = html.replace("&lt;{", "{{")
        html = html.replace("}&gt;", "}}")

        # Ensure proper newlines around Twig tags
        html = re.sub(r"(\{%[^%]+%\})", r"\n\1\n", html)
        html = re.sub(r"\n{3,}", "\n\n", html)

        return html

    def _add_layout_structure(self, html: str) -> str:
        """Add Twig extends and block structure for layout inheritance."""
        # Parse the HTML to extract parts
        soup = BeautifulSoup(html, "lxml")

        lines = [f"{{% extends '{self.layout}.html.twig' %}}\n"]

        # Extract title
        title = soup.find("title")
        if title:
            title_text = title.get_text(strip=True)
            lines.append(f"{{% block title %}}{title_text}{{% endblock %}}\n")

        # Extract head content (stylesheets, meta)
        head = soup.find("head")
        if head:
            stylesheets = []
            metas = []
            for child in head.children:
                if isinstance(child, Tag):
                    if child.name == "link" and child.get("rel") == ["stylesheet"]:
                        stylesheets.append(str(child))
                    elif child.name == "meta" and child.get("name"):
                        metas.append(str(child))
                    elif child.name == "style":
                        stylesheets.append(str(child))

            if stylesheets:
                lines.append("\n{% block stylesheets %}")
                lines.append("    {{ parent() }}")
                lines.extend(f"    {s}" for s in stylesheets)
                lines.append("{% endblock %}\n")

        # Extract body content
        body = soup.find("body")
        if body:
            # Try to detect main content areas
            main_content = body.find(["main", "article"]) or body.find(
                class_=re.compile(r"content|main", re.IGNORECASE)
            )

            if main_content:
                lines.append("\n{% block body %}")
                lines.append(str(main_content))
                lines.append("{% endblock %}\n")
            else:
                # Use entire body
                body_content = "".join(str(c) for c in body.children)
                lines.append("\n{% block body %}")
                lines.append(body_content)
                lines.append("{% endblock %}\n")

            # Extract scripts
            scripts = body.find_all("script")
            if scripts:
                lines.append("\n{% block javascripts %}")
                lines.append("    {{ parent() }}")
                for script in scripts:
                    lines.append(f"    {script}")
                lines.append("{% endblock %}\n")

        return "\n".join(lines)
