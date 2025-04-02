from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers import PythonLexer
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout.controls import FormattedTextControl
from rich.console import Console
from rich.markdown import Markdown
import tempfile
import os
import sys
import click

# Create a rich console for rendering markdown
console = Console()

def get_editor_style():
    """Get the dark mode color scheme for the editor."""
    # VS Code dark theme colors
    bg_color = '#1e1e1e'
    
    return Style.from_dict({
        # Set background color for everything
        'text-area': f'bg:{bg_color}',
        'text-area.cursor-line': f'bg:{bg_color}',
        'prompt': f'bg:{bg_color}',
        'pygments.keyword': f'#569cd6 bg:{bg_color}',  # soft blue for keywords
        'pygments.string': f'#ce9178 bg:{bg_color}',  # soft orange for strings
        'pygments.comment': f'#6a9955 bg:{bg_color}',  # soft green for comments
        'pygments.number': f'#b5cea8 bg:{bg_color}',  # sage green for numbers
        'pygments.function': f'#dcdcaa bg:{bg_color}',  # soft yellow for functions
        'pygments.class': f'#4ec9b0 bg:{bg_color}',  # turquoise for classes
        'pygments.name.builtin': f'#4ec9b0 bg:{bg_color}',  # turquoise for built-ins
        'pygments.name.function': f'#dcdcaa bg:{bg_color}',  # soft yellow for function names
        'pygments.name.class': f'#4ec9b0 bg:{bg_color}',  # turquoise for class names
        'pygments.name': f'#d4d4d4 bg:{bg_color}',  # light gray for other names
        'pygments.operator': f'#d4d4d4 bg:{bg_color}',  # light gray for operators
        'pygments.punctuation': f'#d4d4d4 bg:{bg_color}',  # light gray for punctuation
    })

def check_terminal_capabilities():
    """Check if the terminal supports the required features for the editor."""
    if not sys.stdout.isatty():
        return False, "Not running in a terminal"
    
    # Check if terminal supports ANSI escape sequences
    if os.environ.get('TERM') == 'dumb':
        return False, "Terminal does not support required features"
    
    return True, None

def edit_code(initial_code: str) -> str:
    """
    Opens a text editor for the given code using prompt_toolkit.
    Returns the edited code or None if cancelled.
    """
    # Check terminal capabilities
    supports_editor, error_msg = check_terminal_capabilities()
    if not supports_editor:
        click.echo(f"Warning: {error_msg}")
        click.echo("Falling back to basic text editor...")
        return edit_code_basic(initial_code)

    # Show editor instructions
    instructions = """
# Editor Instructions

## 1. Viewing/Editing:
- Use arrow keys to move cursor
- Type directly to edit text
- Ctrl+A: Move to start of line
- Ctrl+E: Move to end of line
- Ctrl+K: Cut from cursor to end of line
- Ctrl+Y: Paste previously cut text
- Ctrl+W: Cut word before cursor
- Ctrl+U: Cut from start of line to cursor
- Ctrl+B: Move cursor back one word
- Ctrl+F: Move cursor forward one word

## 2. Saving/Exiting:
- Ctrl+S: Save changes and continue
- Ctrl+C: Cancel and use original code

## 3. Requirements:
- Terminal must support ANSI escape sequences
- Must be running in an interactive terminal
- Not supported in basic terminals or when piped

Press Enter to continue to the editor...
"""
    console.print(Markdown(instructions))
    input()
    click.echo("\nStarting code editor...")

    # Create key bindings
    kb = KeyBindings()
    kb.add("c-c")(lambda e: e.app.exit(result=None))  # Ctrl+C to cancel
    kb.add("c-s")(lambda e: e.app.exit(result=e.current_buffer.text))  # Ctrl+S to save

    # Create text area with syntax highlighting
    text_area = TextArea(
        text=initial_code,
        lexer=PygmentsLexer(PythonLexer),
        multiline=True,
        scrollbar=True,
        focus_on_click=True,
    )

    # Create the layout
    layout = Layout(HSplit([
        Window(
            height=1,
            content=FormattedTextControl([('class:prompt', 'Press Ctrl+S to save, Ctrl+C to cancel')])
        ),
        text_area,
    ]))

    # Create and run the application
    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=get_editor_style(),
        mouse_support=True,
    )

    try:
        # Run the full-screen editor
        result = app.run()
        return result if result is not None else initial_code
    except KeyboardInterrupt:
        # User cancelled
        return initial_code

def edit_code_basic(initial_code: str) -> str:
    """
    Fallback basic editor using system's default text editor.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(initial_code)
        temp_file = f.name

    try:
        # Get the default editor from environment or use a common one
        editor = os.environ.get('EDITOR', 'nano')
        
        click.echo(f"\nOpening {editor} editor...")
        click.echo("Make your changes and save the file.")
        click.echo("If using nano: Ctrl+O to save, Ctrl+X to exit")
        click.echo("If using vim: :w to save, :q to exit")
        
        # Open the editor
        os.system(f"{editor} {temp_file}")
        
        # Read the edited file
        with open(temp_file, 'r') as f:
            return f.read()
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            # File was already deleted or doesn't exist
            pass
        except PermissionError:
            click.echo(f"Warning: Could not delete temporary file due to permission issues: {temp_file}")
        except Exception as e:
            click.echo(f"Warning: Error deleting temporary file: {e}")
            click.echo(f"Temporary file location: {temp_file}") 