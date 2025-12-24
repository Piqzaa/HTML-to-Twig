"""
CLI interface for HTML2Twig converter.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .converter import HTMLToTwigConverter
from .wordpress_converter import HTMLToWordPressConverter

console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
╦ ╦╔╦╗╔╦╗╦  ┌─┐  ╔╦╗┬ ┬┬┌─┐
╠═╣ ║ ║║║║  ┌─┘   ║ ││││├─┐
╩ ╩ ╩ ╩ ╩╩═╝└─┘   ╩ └┴┘┴└─┘
    HTML to Twig/WordPress Converter
    """
    console.print(Panel(banner, style="bold blue"))


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version information")
@click.pass_context
def main(ctx, version):
    """
    HTML2Twig - Convert HTML templates to Twig (Symfony) or WordPress PHP templates.

    \b
    Examples:
        html2twig convert input.html output.twig
        html2twig convert input.html output.twig --layout base
        html2twig convert input.html output.php --wordpress
        html2twig init --symfony
    """
    if version:
        from . import __version__
        console.print(f"html2twig version {__version__}")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(ctx.get_help())


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option(
    "--layout", "-l",
    type=str,
    default=None,
    help="Base layout to extend (e.g., 'base' for base.html.twig)"
)
@click.option(
    "--wordpress", "-w",
    is_flag=True,
    help="Convert to WordPress PHP template instead of Twig"
)
@click.option(
    "--theme-name", "-t",
    type=str,
    default="mytheme",
    help="WordPress theme name (only used with --wordpress)"
)
@click.option(
    "--no-report",
    is_flag=True,
    help="Skip generating the conversion report"
)
@click.option(
    "--verbose", "-V",
    is_flag=True,
    help="Show detailed conversion information"
)
def convert(
    input_file: str,
    output_file: str,
    layout: Optional[str],
    wordpress: bool,
    theme_name: str,
    no_report: bool,
    verbose: bool,
):
    """
    Convert an HTML file to Twig or WordPress PHP template.

    \b
    Arguments:
        INPUT_FILE  Path to the HTML file to convert
        OUTPUT_FILE Path for the output template file
    """
    print_banner()

    input_path = Path(input_file)
    output_path = Path(output_file)

    # Validate input
    if not input_path.exists():
        console.print(f"[red]Error:[/red] Input file '{input_file}' not found")
        sys.exit(1)

    # Auto-detect output type if not specified
    if wordpress:
        if not output_path.suffix:
            output_path = output_path.with_suffix(".php")
        converter_type = "WordPress"
    else:
        if not output_path.suffix:
            output_path = output_path.with_suffix(".twig")
        converter_type = "Twig"

    console.print(f"\n[bold]Converting:[/bold] {input_path}")
    console.print(f"[bold]Output:[/bold] {output_path}")
    console.print(f"[bold]Type:[/bold] {converter_type}")
    if layout and not wordpress:
        console.print(f"[bold]Layout:[/bold] {layout}.html.twig")
    if wordpress:
        console.print(f"[bold]Theme:[/bold] {theme_name}")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Converting...", total=None)

        try:
            if wordpress:
                converter = HTMLToWordPressConverter(theme_name=theme_name)
            else:
                converter = HTMLToTwigConverter(layout=layout)

            content, report = converter.convert_file(
                str(input_path),
                str(output_path),
                generate_report=not no_report,
            )

            progress.update(task, description="[green]Conversion complete!")

        except Exception as e:
            progress.update(task, description="[red]Conversion failed!")
            console.print(f"\n[red]Error:[/red] {str(e)}")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            sys.exit(1)

    # Display summary
    console.print()
    _display_summary(report, verbose, wordpress)

    # Show report location
    if not no_report:
        report_path = str(output_path).rsplit(".", 1)[0] + "_report.txt"
        console.print(f"\n[bold]Report saved to:[/bold] {report_path}")

    console.print("\n[green]✓[/green] Conversion completed successfully!")


def _display_summary(report, verbose: bool, is_wordpress: bool):
    """Display a summary of the conversion."""
    # Asset conversions table
    if report.asset_conversions:
        table = Table(title="Asset Conversions", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("Original", style="dim")
        table.add_column("Converted", style="green")

        for conv in report.asset_conversions[:10 if not verbose else None]:
            table.add_row(
                conv["type"].upper(),
                conv["original"][:40] + "..." if len(conv["original"]) > 40 else conv["original"],
                conv["converted"][:50] + "..." if len(conv["converted"]) > 50 else conv["converted"],
            )

        if not verbose and len(report.asset_conversions) > 10:
            table.add_row("...", f"({len(report.asset_conversions) - 10} more)", "...")

        console.print(table)
        console.print()

    # Block/Template Part suggestions
    if is_wordpress:
        if report.template_parts:
            console.print("[bold]Template Parts Detected:[/bold]")
            for part in report.template_parts:
                console.print(f"  • {part['name']}: {part['reason']}")
            console.print()
    else:
        if report.block_suggestions:
            console.print("[bold]Block Suggestions:[/bold]")
            for block in report.block_suggestions:
                console.print(f"  • {{% block {block['name']} %}}: {block['reason']}")
            console.print()

    # Loop conversions
    if report.loop_conversions:
        console.print("[bold]Loop Conversions:[/bold]")
        for loop in report.loop_conversions:
            if is_wordpress:
                console.print(f"  • {loop['element']} → {loop['loop_type']}")
            else:
                console.print(f"  • {loop['element']} → {{% for {loop['item_var']} in {loop['items_var']} %}}")
        console.print()

    # Manual suggestions
    if report.manual_suggestions:
        console.print("[bold yellow]Manual Review Suggestions:[/bold yellow]")
        for i, suggestion in enumerate(report.manual_suggestions[:5 if not verbose else None], 1):
            # Truncate long suggestions
            if len(suggestion) > 100 and not verbose:
                suggestion = suggestion[:100] + "..."
            console.print(f"  {i}. {suggestion}")
        if not verbose and len(report.manual_suggestions) > 5:
            console.print(f"  ... and {len(report.manual_suggestions) - 5} more (use --verbose to see all)")
        console.print()

    # Warnings
    if report.warnings:
        console.print("[bold red]Warnings:[/bold red]")
        for warning in report.warnings:
            console.print(f"  ⚠ {warning}")
        console.print()


@main.command()
@click.option(
    "--symfony", "-s",
    is_flag=True,
    help="Initialize Symfony Twig template structure"
)
@click.option(
    "--wordpress", "-w",
    is_flag=True,
    help="Initialize WordPress theme structure"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=".",
    help="Output directory"
)
@click.option(
    "--theme-name", "-t",
    type=str,
    default="mytheme",
    help="Theme name (for WordPress)"
)
def init(symfony: bool, wordpress: bool, output: str, theme_name: str):
    """
    Initialize a template structure.

    Creates the necessary directory structure and base templates
    for either Symfony Twig or WordPress development.
    """
    print_banner()

    if not symfony and not wordpress:
        console.print("[yellow]Please specify --symfony or --wordpress[/yellow]")
        console.print("\nExamples:")
        console.print("  html2twig init --symfony")
        console.print("  html2twig init --wordpress --theme-name mytheme")
        sys.exit(1)

    output_dir = Path(output)

    if symfony:
        _init_symfony(output_dir)
    elif wordpress:
        _init_wordpress(output_dir, theme_name)


def _init_symfony(output_dir: Path):
    """Initialize Symfony Twig template structure."""
    templates_dir = output_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Create base.html.twig
    base_template = templates_dir / "base.html.twig"
    base_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Welcome{% endblock %}</title>

    {% block stylesheets %}
        <link rel="stylesheet" href="{{ asset('css/app.css') }}">
    {% endblock %}
</head>
<body>
    {% block header %}
    <header>
        <nav>
            {% block navigation %}
            <ul>
                {% for item in menu_items %}
                <li class="{{ item.active ? 'active' : '' }}">
                    <a href="{{ item.url }}">{{ item.label }}</a>
                </li>
                {% endfor %}
            </ul>
            {% endblock %}
        </nav>
    </header>
    {% endblock %}

    <main>
        {% block body %}{% endblock %}
    </main>

    {% block footer %}
    <footer>
        <p>&copy; {{ "now"|date("Y") }} Your Company. All rights reserved.</p>
    </footer>
    {% endblock %}

    {% block javascripts %}
        <script src="{{ asset('js/app.js') }}"></script>
    {% endblock %}
</body>
</html>
"""
    base_template.write_text(base_content)

    # Create example page template
    example_template = templates_dir / "page" / "index.html.twig"
    example_template.parent.mkdir(parents=True, exist_ok=True)
    example_content = """{% extends 'base.html.twig' %}

{% block title %}Home - {{ parent() }}{% endblock %}

{% block body %}
<div class="container">
    <h1>Welcome to Your Site</h1>
    <p>This is an example page template.</p>

    {% block content %}
    <section class="content">
        <!-- Your content here -->
    </section>
    {% endblock %}
</div>
{% endblock %}
"""
    example_template.write_text(example_content)

    console.print("[green]✓[/green] Symfony Twig structure created:")
    console.print(f"  • {templates_dir}/base.html.twig")
    console.print(f"  • {templates_dir}/page/index.html.twig")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Customize base.html.twig with your layout")
    console.print("  2. Use: html2twig convert input.html templates/page/output.html.twig --layout base")


def _init_wordpress(output_dir: Path, theme_name: str):
    """Initialize WordPress theme structure."""
    theme_dir = output_dir / theme_name
    theme_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    for subdir in ["css", "js", "images", "fonts", "template-parts"]:
        (theme_dir / subdir).mkdir(exist_ok=True)

    # Create style.css (required for WordPress themes)
    style_css = theme_dir / "style.css"
    style_css.write_text(f"""/*
Theme Name: {theme_name.replace('_', ' ').title()}
Theme URI: https://example.com/{theme_name}
Author: Your Name
Author URI: https://example.com
Description: A custom WordPress theme converted from HTML
Version: 1.0.0
License: GNU General Public License v2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {theme_name}
*/

/* Add your custom styles below */
""")

    # Create functions.php
    converter = HTMLToWordPressConverter(theme_name=theme_name)
    # Initialize a basic report for generating functions.php
    from .wordpress_converter import WordPressConversionReport
    converter.report = WordPressConversionReport(
        input_file="", output_file="", theme_name=theme_name
    )
    functions_php = theme_dir / "functions.php"
    functions_php.write_text(converter.generate_functions_php())

    # Create header.php
    header_php = theme_dir / "header.php"
    header_php.write_text(converter.generate_header_php())

    # Create footer.php
    footer_php = theme_dir / "footer.php"
    footer_php.write_text(converter.generate_footer_php())

    # Create index.php
    index_php = theme_dir / "index.php"
    index_php.write_text(f"""<?php
/**
 * Main template file
 *
 * @package {theme_name}
 */

get_header();
?>

<div id="primary" class="content-area">
    <?php
    if (have_posts()) :
        while (have_posts()) :
            the_post();
            get_template_part('template-parts/content', get_post_type());
        endwhile;

        the_posts_navigation();
    else :
        get_template_part('template-parts/content', 'none');
    endif;
    ?>
</div>

<?php
get_sidebar();
get_footer();
""")

    # Create sidebar.php
    sidebar_php = theme_dir / "sidebar.php"
    sidebar_php.write_text(f"""<?php
/**
 * Sidebar template
 *
 * @package {theme_name}
 */

if (!is_active_sidebar('sidebar-1')) {{
    return;
}}
?>

<aside id="secondary" class="widget-area">
    <?php dynamic_sidebar('sidebar-1'); ?>
</aside>
""")

    # Create template-parts/content.php
    content_php = theme_dir / "template-parts" / "content.php"
    content_php.write_text(f"""<?php
/**
 * Template part for displaying posts
 *
 * @package {theme_name}
 */
?>

<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
    <header class="entry-header">
        <?php
        if (is_singular()) :
            the_title('<h1 class="entry-title">', '</h1>');
        else :
            the_title('<h2 class="entry-title"><a href="' . esc_url(get_permalink()) . '">', '</a></h2>');
        endif;
        ?>
    </header>

    <?php if (has_post_thumbnail()) : ?>
    <div class="post-thumbnail">
        <?php the_post_thumbnail(); ?>
    </div>
    <?php endif; ?>

    <div class="entry-content">
        <?php
        if (is_singular()) :
            the_content();
        else :
            the_excerpt();
        endif;
        ?>
    </div>

    <footer class="entry-footer">
        <?php
        if ('post' === get_post_type()) :
            ?>
            <span class="posted-on"><?php echo get_the_date(); ?></span>
            <span class="byline"><?php the_author_posts_link(); ?></span>
            <?php
        endif;
        ?>
    </footer>
</article>
""")

    console.print(f"[green]✓[/green] WordPress theme '{theme_name}' created:")
    console.print(f"  • {theme_dir}/style.css")
    console.print(f"  • {theme_dir}/functions.php")
    console.print(f"  • {theme_dir}/header.php")
    console.print(f"  • {theme_dir}/footer.php")
    console.print(f"  • {theme_dir}/index.php")
    console.print(f"  • {theme_dir}/sidebar.php")
    console.print(f"  • {theme_dir}/template-parts/content.php")
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Copy the '{theme_name}' folder to wp-content/themes/")
    console.print("  2. Activate the theme in WordPress admin")
    console.print(f"  3. Use: html2twig convert input.html {theme_dir}/page-custom.php --wordpress")


@main.command()
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o",
    type=click.Path(),
    default="./templates",
    help="Output directory for converted files"
)
@click.option(
    "--layout", "-l",
    type=str,
    default=None,
    help="Base layout to extend"
)
@click.option(
    "--wordpress", "-w",
    is_flag=True,
    help="Convert to WordPress PHP templates"
)
@click.option(
    "--theme-name", "-t",
    type=str,
    default="mytheme",
    help="WordPress theme name"
)
def batch(
    input_files: tuple,
    output_dir: str,
    layout: Optional[str],
    wordpress: bool,
    theme_name: str,
):
    """
    Convert multiple HTML files at once.

    \b
    Examples:
        html2twig batch *.html -o templates/
        html2twig batch page1.html page2.html --layout base
    """
    print_banner()

    if not input_files:
        console.print("[yellow]No input files specified[/yellow]")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Converting {len(input_files)} file(s)...[/bold]\n")

    success_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for input_file in input_files:
            input_path = Path(input_file)
            task = progress.add_task(f"Converting {input_path.name}...", total=None)

            try:
                # Determine output filename
                if wordpress:
                    output_file = output_path / input_path.with_suffix(".php").name
                    converter = HTMLToWordPressConverter(theme_name=theme_name)
                else:
                    output_file = output_path / (input_path.stem + ".html.twig")
                    converter = HTMLToTwigConverter(layout=layout)

                converter.convert_file(str(input_path), str(output_file))

                progress.update(task, description=f"[green]✓[/green] {input_path.name}")
                success_count += 1

            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] {input_path.name}: {str(e)}")
                error_count += 1

    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  [green]✓[/green] Converted: {success_count}")
    if error_count:
        console.print(f"  [red]✗[/red] Failed: {error_count}")

    console.print(f"\n[bold]Output directory:[/bold] {output_path}")


if __name__ == "__main__":
    main()
