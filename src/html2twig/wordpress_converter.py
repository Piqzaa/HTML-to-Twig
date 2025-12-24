"""
HTML to WordPress PHP template converter module.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup, Tag, NavigableString


@dataclass
class WordPressConversionReport:
    """Stores all conversions and suggestions for WordPress conversion."""

    input_file: str
    output_file: str
    theme_name: str = "mytheme"
    asset_conversions: list = field(default_factory=list)
    template_parts: list = field(default_factory=list)
    loop_conversions: list = field(default_factory=list)
    manual_suggestions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_asset(self, original: str, converted: str, tag_type: str):
        self.asset_conversions.append(
            {"original": original, "converted": converted, "type": tag_type}
        )

    def add_template_part(self, name: str, reason: str):
        self.template_parts.append({"name": name, "reason": reason})

    def add_loop(self, element: str, loop_type: str):
        self.loop_conversions.append({"element": element, "loop_type": loop_type})

    def add_suggestion(self, suggestion: str):
        self.manual_suggestions.append(suggestion)

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def generate_text(self) -> str:
        """Generate a text report of all conversions."""
        lines = [
            "=" * 70,
            "HTML TO WORDPRESS CONVERSION REPORT",
            "=" * 70,
            "",
            f"Input:  {self.input_file}",
            f"Output: {self.output_file}",
            f"Theme:  {self.theme_name}",
            "",
            "-" * 70,
            "ASSET CONVERSIONS",
            "-" * 70,
        ]

        if self.asset_conversions:
            for conv in self.asset_conversions:
                lines.append(f"  [{conv['type'].upper()}]")
                lines.append(f"    Before: {conv['original']}")
                lines.append(f"    After:  {conv['converted']}")
                lines.append("")
        else:
            lines.append("  No asset conversions performed.")
            lines.append("")

        lines.extend(["-" * 70, "TEMPLATE PARTS SUGGESTIONS", "-" * 70])

        if self.template_parts:
            for part in self.template_parts:
                lines.append(f"  get_template_part('{part['name']}')")
                lines.append(f"    Reason: {part['reason']}")
                lines.append("")
        else:
            lines.append("  No template part suggestions.")
            lines.append("")

        lines.extend(["-" * 70, "LOOP CONVERSIONS", "-" * 70])

        if self.loop_conversions:
            for loop in self.loop_conversions:
                lines.append(f"  Element: {loop['element']}")
                lines.append(f"    Type: {loop['loop_type']}")
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


class HTMLToWordPressConverter:
    """Converts HTML templates to WordPress PHP templates."""

    # Patterns for detecting asset paths
    ASSET_PATTERNS = {
        "images": re.compile(r"^(?:\.\.?/)*(?:assets?/)?(?:img|images?)/(.+)$", re.IGNORECASE),
        "css": re.compile(r"^(?:\.\.?/)*(?:assets?/)?(?:css|styles?)/(.+)$", re.IGNORECASE),
        "js": re.compile(r"^(?:\.\.?/)*(?:assets?/)?(?:js|scripts?|javascript)/(.+)$", re.IGNORECASE),
        "fonts": re.compile(r"^(?:\.\.?/)*(?:assets?/)?fonts?/(.+)$", re.IGNORECASE),
    }

    # Navigation element patterns
    NAV_SELECTORS = ["nav", "ul.nav", "ul.menu", "ul.navbar-nav", ".navigation", ".main-menu"]

    # Template part patterns (similar to Twig blocks)
    TEMPLATE_PARTS = {
        "header": ["header", ".header", "#header", "[role='banner']"],
        "footer": ["footer", ".footer", "#footer", "[role='contentinfo']"],
        "sidebar": [".sidebar", "#sidebar", "aside", "[role='complementary']"],
        "content": ["main", ".content", "#content", ".main-content", "[role='main']"],
    }

    def __init__(self, theme_name: str = "mytheme"):
        """
        Initialize the WordPress converter.

        Args:
            theme_name: Name of the WordPress theme
        """
        self.theme_name = theme_name
        self.report: Optional[WordPressConversionReport] = None
        self.soup: Optional[BeautifulSoup] = None

    def convert_file(
        self, input_path: str, output_path: str, generate_report: bool = True
    ) -> tuple[str, Optional[WordPressConversionReport]]:
        """
        Convert an HTML file to WordPress PHP template.

        Args:
            input_path: Path to the input HTML file
            output_path: Path to the output PHP file

        Returns:
            Tuple of (converted content, report)
        """
        with open(input_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.report = WordPressConversionReport(
            input_file=input_path,
            output_file=output_path,
            theme_name=self.theme_name,
        )

        php_content = self.convert(html_content)

        # Save output
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(php_content)

        # Generate report
        if generate_report:
            report_path = str(output_path).rsplit(".", 1)[0] + "_report.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(self.report.generate_text())

        return php_content, self.report

    def convert(self, html_content: str) -> str:
        """
        Convert HTML content to WordPress PHP template.

        Args:
            html_content: The HTML content to convert

        Returns:
            Converted WordPress PHP template content
        """
        self.soup = BeautifulSoup(html_content, "lxml")

        # Convert assets
        self._convert_images()
        self._convert_stylesheets()
        self._convert_scripts()
        self._convert_other_assets()

        # Detect and convert navigation menus
        self._convert_navigation()

        # Detect template parts
        self._detect_template_parts()

        # Detect repetitive elements for The Loop
        self._detect_loop_elements()

        # Generate PHP output
        php_content = self._generate_php_output()

        return php_content

    def _convert_images(self):
        """Convert image src attributes to WordPress get_template_directory_uri()."""
        for img in self.soup.find_all("img"):
            src = img.get("src", "")
            if src and not src.startswith(("http://", "https://", "//", "data:", "<?php")):
                new_src = self._convert_asset_path(src, "images")
                if new_src != src:
                    self.report.add_asset(src, new_src, "img")
                    img["src"] = new_src

            # Handle srcset
            srcset = img.get("srcset", "")
            if srcset and not srcset.startswith("<?php"):
                new_srcset = self._convert_srcset(srcset)
                if new_srcset != srcset:
                    img["srcset"] = new_srcset

    def _convert_stylesheets(self):
        """Convert stylesheet href attributes to WordPress functions."""
        for link in self.soup.find_all("link", rel="stylesheet"):
            href = link.get("href", "")
            if href and not href.startswith(("http://", "https://", "//", "<?php")):
                new_href = self._convert_asset_path(href, "css")
                if new_href != href:
                    self.report.add_asset(href, new_href, "css")
                    link["href"] = new_href

    def _convert_scripts(self):
        """Convert script src attributes to WordPress functions."""
        for script in self.soup.find_all("script", src=True):
            src = script.get("src", "")
            if src and not src.startswith(("http://", "https://", "//", "<?php")):
                new_src = self._convert_asset_path(src, "js")
                if new_src != src:
                    self.report.add_asset(src, new_src, "js")
                    script["src"] = new_src

    def _convert_other_assets(self):
        """Convert other asset references."""
        # Favicons
        for link in self.soup.find_all("link", rel=lambda x: x and "icon" in x.lower()):
            href = link.get("href", "")
            if href and not href.startswith(("http://", "https://", "//", "<?php")):
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

    def _convert_asset_path(self, path: str, default_type: str = "images") -> str:
        """
        Convert a relative asset path to WordPress PHP function.

        Args:
            path: The original asset path
            default_type: Default asset type if pattern doesn't match

        Returns:
            WordPress PHP expression or original path if external
        """
        if not path or path.startswith(("http://", "https://", "//", "data:", "<?php")):
            return path

        # Clean the path
        clean_path = path.strip()

        # Try to match against known patterns
        for asset_type, pattern in self.ASSET_PATTERNS.items():
            match = pattern.match(clean_path)
            if match:
                filename = match.group(1)
                return f"<?php echo esc_url(get_template_directory_uri() . '/{asset_type}/{filename}'); ?>"

        # Fallback: use the path as-is
        clean_path = re.sub(r"^(?:\.\.?/)+", "", clean_path)

        # Determine asset type from extension
        ext = Path(clean_path).suffix.lower()
        if ext in [".css", ".scss", ".sass", ".less"]:
            return f"<?php echo esc_url(get_template_directory_uri() . '/css/{clean_path}'); ?>"
        elif ext in [".js", ".mjs", ".ts"]:
            return f"<?php echo esc_url(get_template_directory_uri() . '/js/{clean_path}'); ?>"
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".avif"]:
            return f"<?php echo esc_url(get_template_directory_uri() . '/images/{clean_path}'); ?>"
        elif ext in [".woff", ".woff2", ".ttf", ".otf", ".eot"]:
            return f"<?php echo esc_url(get_template_directory_uri() . '/fonts/{clean_path}'); ?>"
        else:
            return f"<?php echo esc_url(get_template_directory_uri() . '/{clean_path}'); ?>"

    def _convert_srcset(self, srcset: str) -> str:
        """Convert srcset attribute values to WordPress PHP."""
        parts = srcset.split(",")
        new_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
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

    def _convert_inline_style_urls(self, style: str) -> str:
        """Convert url() in inline styles to WordPress PHP."""
        url_pattern = re.compile(r'url\(["\']?([^"\')\s]+)["\']?\)', re.IGNORECASE)

        def replace_url(match):
            url = match.group(1)
            if url.startswith(("http://", "https://", "//", "data:")):
                return match.group(0)
            new_url = self._convert_asset_path(url, "images")
            return f"url('{new_url}')"

        return url_pattern.sub(replace_url, style)

    def _convert_navigation(self):
        """Detect and convert navigation menus to WordPress wp_nav_menu()."""
        for selector in self.NAV_SELECTORS:
            navs = self.soup.select(selector)
            for nav in navs:
                self._convert_nav_element(nav)

    def _convert_nav_element(self, nav: Tag):
        """Convert a navigation element to WordPress wp_nav_menu()."""
        # Find the list items
        items = nav.find_all("li", recursive=True)
        if len(items) < 2:
            return

        # Check if items have similar structure
        first_item = items[0]
        similar_count = sum(
            1 for item in items[1:] if self._elements_similar(first_item, item)
        )

        if similar_count >= len(items) // 2:
            menu_name = self._detect_menu_name(nav)
            menu_location = menu_name.lower().replace(" ", "_").replace("-", "_")

            # Find the parent ul
            parent_ul = nav.find("ul") if nav.name != "ul" else nav

            if parent_ul:
                # Get classes from the ul for container_class
                ul_classes = " ".join(parent_ul.get("class", []))

                # Create WordPress wp_nav_menu() call
                wp_menu = self.soup.new_tag("nav")
                wp_menu["class"] = nav.get("class", [])
                if nav.get("id"):
                    wp_menu["id"] = nav["id"]

                php_code = f"""<?php
wp_nav_menu(array(
    'theme_location' => '{menu_location}',
    'menu_class'     => '{ul_classes}',
    'container'      => false,
    'fallback_cb'    => false,
));
?>"""
                wp_menu.append(BeautifulSoup(php_code, "html.parser"))

                # Replace the original nav
                nav.replace_with(wp_menu)

                self.report.add_loop(f"Navigation menu: {menu_name}", "wp_nav_menu()")
                self.report.add_suggestion(
                    f"Register menu location '{menu_location}' in functions.php:\n"
                    f"    register_nav_menus(array('{menu_location}' => __('{menu_name}', '{self.theme_name}')));"
                )

    def _detect_menu_name(self, nav: Tag) -> str:
        """Detect a suitable name for the navigation menu."""
        if nav.get("id"):
            return nav["id"].replace("-", " ").replace("_", " ").title()
        classes = nav.get("class", [])
        for cls in classes:
            if "nav" in cls.lower() or "menu" in cls.lower():
                return cls.replace("-", " ").replace("_", " ").title()
        if nav.get("aria-label"):
            return nav["aria-label"]
        return "Primary Menu"

    def _elements_similar(self, elem1: Tag, elem2: Tag) -> bool:
        """Check if two elements have similar structure."""
        if elem1.name != elem2.name:
            return False
        children1 = [c.name for c in elem1.children if isinstance(c, Tag)]
        children2 = [c.name for c in elem2.children if isinstance(c, Tag)]
        return children1 == children2

    def _detect_template_parts(self):
        """Detect common template parts and suggest get_template_part() calls."""
        for part_name, selectors in self.TEMPLATE_PARTS.items():
            for selector in selectors:
                try:
                    elements = self.soup.select(selector)
                    if elements:
                        self.report.add_template_part(
                            part_name, f"Detected {selector} element(s)"
                        )
                        self.report.add_suggestion(
                            f"Consider extracting {selector} to template-parts/{part_name}.php"
                        )
                        break
                except Exception:
                    continue

    def _detect_loop_elements(self):
        """Detect repetitive patterns that might use The Loop."""
        # Look for repeated similar elements (posts, cards, etc.)
        containers = self.soup.find_all(["div", "section", "article"])

        for container in containers:
            children = [c for c in container.children if isinstance(c, Tag)]
            if len(children) < 3:
                continue

            first_child = children[0]
            similar_count = sum(
                1 for c in children[1:] if self._elements_similar(first_child, c)
            )

            if similar_count >= 2:
                container_id = (
                    container.get("id")
                    or (container.get("class", ["container"])[0] if container.get("class") else "container")
                )

                # Check if it looks like a post list
                if first_child.name == "article" or "post" in str(first_child.get("class", [])).lower():
                    self.report.add_loop(
                        f"Post list in '{container_id}'",
                        "WordPress The Loop (while have_posts())"
                    )
                    self.report.add_suggestion(
                        f"Replace repeated articles in '{container_id}' with WordPress The Loop:\n"
                        f"    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>\n"
                        f"        <?php get_template_part('template-parts/content', get_post_type()); ?>\n"
                        f"    <?php endwhile; endif; ?>"
                    )
                else:
                    self.report.add_suggestion(
                        f"Consider using a loop for repeated elements in '{container_id}' "
                        f"({similar_count + 1} similar children found)"
                    )

    def _generate_php_output(self) -> str:
        """Generate the final WordPress PHP template output."""
        # Get the HTML output
        html = str(self.soup)

        # Add PHP header
        php_header = """<?php
/**
 * Template Name: Custom Page Template
 *
 * @package {theme_name}
 */

get_header();
?>

""".format(theme_name=self.theme_name)

        php_footer = """

<?php
get_sidebar();
get_footer();
"""

        # Extract body content only
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_content = body_match.group(1)
        else:
            body_content = html

        # Clean up the content
        body_content = self._cleanup_php_output(body_content)

        return php_header + body_content + php_footer

    def _cleanup_php_output(self, content: str) -> str:
        """Clean up the PHP output."""
        # Remove empty PHP tags
        content = re.sub(r"<\?php\s*\?>", "", content)

        # Fix any broken PHP
        content = content.replace("&lt;?php", "<?php")
        content = content.replace("?&gt;", "?>")

        return content

    def generate_functions_php(self) -> str:
        """Generate a basic functions.php with menu registrations."""
        menus = []
        for loop in self.report.loop_conversions:
            if loop["loop_type"] == "wp_nav_menu()":
                menu_name = loop["element"].replace("Navigation menu: ", "")
                menu_location = menu_name.lower().replace(" ", "_")
                menus.append(f"        '{menu_location}' => __('{menu_name}', '{self.theme_name}'),")

        menu_registration = "\n".join(menus) if menus else "        'primary' => __('Primary Menu', '{theme_name}'),".format(theme_name=self.theme_name)

        return f"""<?php
/**
 * {self.theme_name} functions and definitions
 *
 * @package {self.theme_name}
 */

if (!defined('ABSPATH')) {{
    exit;
}}

/**
 * Theme setup
 */
function {self.theme_name.lower().replace(' ', '_')}_setup() {{
    // Add theme support
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ));

    // Register navigation menus
    register_nav_menus(array(
{menu_registration}
    ));
}}
add_action('after_setup_theme', '{self.theme_name.lower().replace(' ', '_')}_setup');

/**
 * Enqueue scripts and styles
 */
function {self.theme_name.lower().replace(' ', '_')}_scripts() {{
    wp_enqueue_style('{self.theme_name.lower().replace(' ', '_')}-style', get_stylesheet_uri(), array(), '1.0.0');

    // Add your custom CSS files here
    // wp_enqueue_style('custom-css', get_template_directory_uri() . '/css/custom.css', array(), '1.0.0');

    // Add your custom JS files here
    // wp_enqueue_script('custom-js', get_template_directory_uri() . '/js/custom.js', array('jquery'), '1.0.0', true);
}}
add_action('wp_enqueue_scripts', '{self.theme_name.lower().replace(' ', '_')}_scripts');
"""

    def generate_header_php(self) -> str:
        """Generate a basic header.php template."""
        return f"""<?php
/**
 * Header template
 *
 * @package {self.theme_name}
 */

if (!defined('ABSPATH')) {{
    exit;
}}
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<header id="masthead" class="site-header">
    <div class="site-branding">
        <?php if (has_custom_logo()) : ?>
            <?php the_custom_logo(); ?>
        <?php else : ?>
            <h1 class="site-title"><a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a></h1>
        <?php endif; ?>
    </div>

    <nav id="site-navigation" class="main-navigation">
        <?php
        wp_nav_menu(array(
            'theme_location' => 'primary',
            'menu_class'     => 'primary-menu',
            'container'      => false,
        ));
        ?>
    </nav>
</header>

<main id="primary" class="site-main">
"""

    def generate_footer_php(self) -> str:
        """Generate a basic footer.php template."""
        return f"""<?php
/**
 * Footer template
 *
 * @package {self.theme_name}
 */

if (!defined('ABSPATH')) {{
    exit;
}}
?>
</main>

<footer id="colophon" class="site-footer">
    <div class="site-info">
        <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>. All rights reserved.</p>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
"""
