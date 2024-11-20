"""
WCAG Alt Text Generator
A tool for generating accessible alt text for images on web pages.
"""

__version__ = "0.1.0"
__author__ = "Elizabeth Patrick"

from .alt_text_generator import WCAGAltTextGenerator

# What will be available when someone does: from src import *
__all__ = ['WCAGAltTextGenerator']