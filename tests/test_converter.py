"""Tests for the HTML to Twig converter."""

import pytest
from html2twig.converter import HTMLToTwigConverter, ConversionReport


class TestAssetConversion:
    """Test asset path conversions."""

    def test_convert_image_src(self):
        """Test that image src attributes are converted."""
        html = '<img src="../images/logo.png" alt="Logo">'
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "{{ asset('images/logo.png') }}" in result

    def test_convert_css_href(self):
        """Test that CSS href attributes are converted."""
        html = '<link rel="stylesheet" href="../css/styles.css">'
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "{{ asset('css/styles.css') }}" in result

    def test_convert_script_src(self):
        """Test that script src attributes are converted."""
        html = '<script src="../js/app.js"></script>'
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "{{ asset('js/app.js') }}" in result

    def test_skip_external_urls(self):
        """Test that external URLs are not converted."""
        html = '<img src="https://example.com/image.png">'
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "https://example.com/image.png" in result
        assert "asset(" not in result

    def test_skip_data_urls(self):
        """Test that data URLs are not converted."""
        html = '<img src="data:image/png;base64,abc123">'
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "data:image/png;base64,abc123" in result
        assert "asset(" not in result

    def test_convert_nested_asset_paths(self):
        """Test conversion of nested asset paths."""
        html = '<img src="../../assets/img/photo.jpg">'
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "{{ asset('images/photo.jpg') }}" in result


class TestNavigationConversion:
    """Test navigation menu conversions."""

    def test_detect_nav_element(self):
        """Test that nav elements are detected."""
        html = """
        <nav>
            <ul class="menu">
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
        """
        converter = HTMLToTwigConverter()
        converter.convert(html)
        assert len(converter.report.loop_conversions) > 0

    def test_nav_loop_generation(self):
        """Test that navigation loops are generated."""
        html = """
        <nav class="main-nav">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
        """
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "{% for item in" in result
        assert "{% endfor %}" in result


class TestBlockDetection:
    """Test block detection and suggestions."""

    def test_detect_header_block(self):
        """Test that header elements are detected."""
        html = "<header><h1>Title</h1></header>"
        converter = HTMLToTwigConverter()
        converter.convert(html)
        block_names = [b["name"] for b in converter.report.block_suggestions]
        assert "header" in block_names

    def test_detect_footer_block(self):
        """Test that footer elements are detected."""
        html = "<footer><p>Copyright</p></footer>"
        converter = HTMLToTwigConverter()
        converter.convert(html)
        block_names = [b["name"] for b in converter.report.block_suggestions]
        assert "footer" in block_names

    def test_detect_sidebar_block(self):
        """Test that sidebar elements are detected."""
        html = '<aside class="sidebar"><p>Sidebar</p></aside>'
        converter = HTMLToTwigConverter()
        converter.convert(html)
        block_names = [b["name"] for b in converter.report.block_suggestions]
        assert "sidebar" in block_names


class TestLayoutInheritance:
    """Test layout inheritance generation."""

    def test_extends_added_with_layout(self):
        """Test that extends is added when layout is specified."""
        html = "<html><body><p>Content</p></body></html>"
        converter = HTMLToTwigConverter(layout="base")
        result = converter.convert(html)
        assert "{% extends 'base.html.twig' %}" in result

    def test_no_extends_without_layout(self):
        """Test that extends is not added without layout."""
        html = "<html><body><p>Content</p></body></html>"
        converter = HTMLToTwigConverter()
        result = converter.convert(html)
        assert "{% extends" not in result


class TestConversionReport:
    """Test the conversion report generation."""

    def test_report_tracks_assets(self):
        """Test that asset conversions are tracked in the report."""
        html = '<img src="../images/logo.png"><link rel="stylesheet" href="../css/style.css">'
        converter = HTMLToTwigConverter()
        converter.convert(html)
        assert len(converter.report.asset_conversions) == 2

    def test_report_text_generation(self):
        """Test that the report text is generated correctly."""
        report = ConversionReport(
            input_file="input.html",
            output_file="output.twig",
            layout="base",
        )
        report.add_asset("../img/logo.png", "{{ asset('images/logo.png') }}", "img")
        report.add_block("header", "Detected <header>")
        report.add_suggestion("Review navigation structure")

        text = report.generate_text()
        assert "HTML TO TWIG CONVERSION REPORT" in text
        assert "input.html" in text
        assert "output.twig" in text
        assert "logo.png" in text
        assert "header" in text


class TestRepetitivePatterns:
    """Test detection of repetitive patterns."""

    def test_detect_card_pattern(self):
        """Test that repeated card-like elements are detected."""
        html = """
        <div class="cards">
            <div class="card"><h3>Card 1</h3><p>Content</p></div>
            <div class="card"><h3>Card 2</h3><p>Content</p></div>
            <div class="card"><h3>Card 3</h3><p>Content</p></div>
            <div class="card"><h3>Card 4</h3><p>Content</p></div>
        </div>
        """
        converter = HTMLToTwigConverter()
        converter.convert(html)
        assert len(converter.report.manual_suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
