"""
HTML2Twig - Convert HTML templates to Twig (Symfony) or WordPress PHP templates.
"""

__version__ = "1.0.0"
__author__ = "HTML2Twig Contributors"

from .converter import HTMLToTwigConverter
from .wordpress_converter import HTMLToWordPressConverter

__all__ = ["HTMLToTwigConverter", "HTMLToWordPressConverter", "__version__"]
