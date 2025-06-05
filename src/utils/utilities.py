"""
utilities.py

This module aims to provide several functionalities that are broader on scope than the rest of the source code.
The functions are written in a functional programming style, with lazy evaluation and performance complaince in mind.
"""
import sys
import logging
from pathlib import Path
from typing import Generator, Callable, Union, List

def setup_logging(log_file_path: str)-> None:
    """
    Small utility function to set up logging using the python module logging.
    :param log_file_path: The path in which the log will be saved.
    :return: None
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_markdown(markdown_file_name: str, directory_path: str) -> Generator[str, None, None]:
    """
    Generator that yields the content of a markdown file as a string.

    :param markdown_file_name: The name of the markdown file (without extension).
    :param directory_path: The directory where the markdown file is located.
    :yield: The markdown content as a string.
    """
    path = Path(directory_path) / f"{markdown_file_name}.md"
    logging.info(f"Loading markdown from: {path.resolve()}")

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found at: {path.resolve()}")

    yield path.read_text(encoding="utf-8")


def replace_markdown_placeholders(markdown: str, placeholder_tags: List[str], replacements: List[str]) -> str:
    """
    Replaces all occurrences of a placeholder tag in a markdown markdown with the given replacement text.

    :param markdown: The markdown string containing placeholder tags.
    :param placeholder_tags: The exact tag string to replace (e.g., "{{variable}}").
    :param replacements: The string to replace the tag with.
    :return: The resulting string with placeholders replaced.
    """
    if not all(isinstance(arg, list) for arg in [placeholder_tags, replacements]):
        raise TypeError("All arguments must be strings or lists of strings.")

    all_strings_replacements = all(isinstance(string, str)for string in replacements)
    all_strings_tags = all(isinstance(string, str) for string in placeholder_tags)

    if not all_strings_replacements and all_strings_tags:
        raise TypeError("All arguments must be strings or lists of strings.")

    for tag, replacement in zip(placeholder_tags, replacements):
        markdown = markdown.replace(tag, replacement)

    return markdown


def prepare_markdown(
        load_fn: Callable[..., Generator[str, None, None]],
        replace_fn: Callable[[str, str, str], str],
        markdown_file_name: str,
        directory_path: str,
        placeholder_tags: List[str],
        replacements: List[str]
) -> Generator[str, None, None]:
    """
    Higher order function that prepares a markdown by loading and replacing placeholders.

    :param load_fn: A function that loads the markdown (e.g., load_markdown).
    :param replace_fn: A function that replaces placeholders in a markdown (e.g., replace_markdown_placeholders).
    :param markdown_file_name: Name of the markdown file (without .md).
    :param directory_path: Directory where the markdown file lives.
    :param placeholder_tags: The placeholder tag to replace.
    :param replacements: The replacement value for the tag.
    :yield: The final markdown with placeholders replaced.
    """
    
    for markdown in load_fn(markdown_file_name=markdown_file_name, directory_path=directory_path):
        yield replace_fn(markdown, placeholder_tags, replacements)


