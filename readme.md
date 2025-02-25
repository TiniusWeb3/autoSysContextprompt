# Project Context for Claude

A utility script that automatically collects and provides system context, keyboard information, and project structure to Claude, enhancing the AI's ability to give you relevant, accurate assistance.

## Value Proposition

This tool solves a common frustration when working with AI assistants: manually copying and pasting system information, configuration files, and project structures. It streamlines your workflow by:

1. **Saving Time**: Automatically generates comprehensive context in one command
2. **Improving Accuracy**: Provides Claude with precise information about your system and projects
3. **Reducing Repetition**: Eliminates the need to explain your setup multiple times
4. **Enhancing Responses**: Claude gives more tailored solutions with better context

## Features

- **System Information**: OS, kernel, shell, hardware specs
- **Configuration Files**: Auto-detects and includes relevant system config files
- **Project Structure**: Scans directories and provides file/folder overview
- **Keyboard Reference**: Displays special character key combinations
- **Character Lookup**: Quickly find how to type specific characters
- **Clipboard Integration**: Automatically copies results to clipboard

## Installation

1. Save the script to your preferred location:
   ```bash
   mkdir -p ~/projects/syscontext
   cd ~/projects/syscontext
   # Save the script as project_context.py
   chmod +x project_context.py
   ```

2. Add these aliases to your `~/.bashrc`:
   ```bash
   alias claude-context="python3 ~/projects/syscontext/project_context.py"
   alias claude-project="python3 ~/projects/syscontext/project_context.py \$(pwd)"
   alias kbd-ref="python3 ~/projects/syscontext/project_context.py --only-keyboard"
   function kbd-char() {
     python3 ~/projects/syscontext/project_context.py --key-lookup "$1"
   }
   alias claude-full="python3 ~/projects/syscontext/project_context.py --keyboard-info"
   alias claude-min="python3 ~/projects/syscontext/project_context.py"
   ```

3. Apply changes:
   ```bash
   source ~/.bashrc
   ```

4. Dependencies: Make sure `xclip` is installed for clipboard functionality:
   ```bash
   sudo pacman -S xclip xorg-xmodmap
   ```

## Usage Examples

### 1. Basic System Context

```bash
claude-context
```

Generates and copies to clipboard a comprehensive overview including:
- System information (OS, kernel, shell)
- Hardware specs (CPU, memory)
- Important configuration files (bashrc, i3 config, etc.)

**Use case**: When asking Claude about system customization, troubleshooting, or configuration questions.

### 2. Project Context

```bash
cd ~/myproject
claude-project
```

Generates context for your current project directory, including:
- System information
- Project structure
- Project configuration files
- Dependencies (requirements.txt, package.json, etc.)

**Use case**: When asking Claude for help with coding, debugging, or understanding a project.

### 3. Keyboard Reference

```bash
kbd-ref
```

Generates a table of special characters and their key combinations.

**Use case**: When working on i3 config, bash scripts, or programming where special characters are needed.

### 4. Character Lookup

```bash
kbd-char '\\'
```

Shows how to type a specific character (e.g., "To type '\': Press backslash").

**Use case**: When you need to find a specific keyboard shortcut quickly.

## Real-World Use Cases

### 1. System Configuration Help

**Scenario**: You want to customize your i3 window manager but aren't sure how to configure workspaces.

**Without this tool**: You'd need to manually copy your i3 config, explain your system, and hope Claude understands what you want.

**With this tool**:
```bash
claude-context
```
Then ask Claude: "How can I configure 10 workspaces in i3 with custom names and shortcuts?"

Claude now has your exact i3 configuration and can provide tailored advice for your specific setup.

### 2. Project Debugging

**Scenario**: You're working on a Python project and getting a cryptic error.

**Without this tool**: You'd need to copy the error message, relevant code files, and explain your project structure.

**With this tool**:
```bash
cd ~/myproject
claude-project
```
Then ask Claude: "I'm getting this error: [paste error]. What's causing it and how do I fix it?"

Claude now understands your project structure, dependencies, and configuration, leading to more accurate debugging help.

### 3. Keyboard Configuration

**Scenario**: You're working with a special character but can't remember how to type it.

**Without this tool**: You'd google "how to type [character] on linux" and sift through results.

**With this tool**:
```bash
kbd-char '@'
```
Instantly shows you the key combination for typing the character.

## Command Reference

### Basic Commands

| Command | Description |
|---------|-------------|
| `claude-context` | System information and config files |
| `claude-project` | System + current project context |
| `claude-full` | Complete context with keyboard reference |
| `claude-min` | Minimal system context |
| `kbd-ref` | Keyboard special character reference |
| `kbd-char 'X'` | How to type character X |

### Advanced Options

```bash
# Include specific files
claude-context --important-files ~/.config/polybar/config ~/.Xmodmap

# Filter by file extensions
claude-project --extensions py js json

# Limit directory scan depth
claude-project --max-depth 2

# Save output to file instead of clipboard
claude-context --output system-context.md

# Get JSON output for programmatic use
claude-context --json
```

## Tips for Best Results

1. **Start conversations with context**: Paste the generated context at the beginning of your Claude conversation

2. **Use project context for code questions**: When asking about code, use `claude-project` in the relevant directory

3. **Be specific with follow-up questions**: After providing context, ask clear questions that reference the information

4. **Update context when changing projects**: Generate fresh context when switching to a different project

5. **Include keyboard info when needed**: Use `claude-full` when asking about keyboard shortcuts or configuration

## Security Considerations

The script collects system and project information that will be shared with Claude. Be mindful of:

- **Sensitive information**: The script includes content from config files which may contain API keys or passwords
- **Private projects**: Consider using `--no-base-files` when working with confidential projects
- **Customize what's shared**: Use `--important-files` to explicitly choose what files to include

## Troubleshooting

If commands aren't working:

1. Ensure the script has execute permissions: `chmod +x ~/projects/syscontext/project_context.py`
2. Check that your `.bashrc` aliases are correct and you've run `source ~/.bashrc`
3. Verify dependencies are installed: `pacman -Q xclip xorg-xmodmap`
4. For clipboard issues: `pacman -S xclip`
