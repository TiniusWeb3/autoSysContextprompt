#!/usr/bin/env python3
import os
import sys
import argparse
import json
import subprocess
from pathlib import Path
import re
import shutil
import pwd

def check_dependency(command):
    """Check if a command is available"""
    return shutil.which(command) is not None

def copy_to_clipboard(text):
    """Copy text to clipboard using xclip"""
    if not check_dependency("xclip"):
        print("Warning: xclip not found, cannot copy to clipboard. Install with 'pacman -S xclip'")
        return False
    
    try:
        process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        process.communicate(input=text.encode())
        return process.returncode == 0
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

def get_system_info():
    """Collect detailed system information"""
    system_info = {}
    
    # Get Linux distribution info
    try:
        with open('/etc/os-release', 'r') as f:
            os_release = {}
            for line in f:
                if '=' in line:
                    k, v = line.rstrip().split('=', 1)
                    os_release[k] = v.strip('"')
        system_info['os'] = os_release.get('PRETTY_NAME', 'Arch Linux')
    except:
        system_info['os'] = 'Arch Linux'
    
    # Get kernel version
    try:
        system_info['kernel'] = subprocess.check_output(['uname', '-r']).decode().strip()
    except:
        system_info['kernel'] = 'Unknown'
    
    # Get shell
    system_info['shell'] = os.environ.get('SHELL', 'Unknown')
    
    # Get username
    system_info['user'] = pwd.getpwuid(os.getuid()).pw_name
    
    # Get hostname
    try:
        system_info['hostname'] = subprocess.check_output(['hostname']).decode().strip()
    except:
        system_info['hostname'] = 'Unknown'
    
    # Get DE/WM info
    system_info['desktop'] = os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')
    system_info['window_manager'] = os.environ.get('DESKTOP_SESSION', 'i3')
    
    # Get keyboard layout information
    try:
        if check_dependency('setxkbmap'):
            keyboard_info = subprocess.check_output(['setxkbmap', '-query']).decode().strip()
            system_info['keyboard_layout'] = keyboard_info
    except:
        pass
    
    # Get additional system info if neofetch is available
    if check_dependency('neofetch'):
        try:
            neofetch_output = subprocess.check_output(['neofetch', '--stdout']).decode().strip()
            system_info['neofetch'] = neofetch_output
        except:
            pass
    
    # Get installed package count
    if check_dependency('pacman'):
        try:
            package_count = subprocess.check_output(['pacman', '-Q', '|', 'wc', '-l'], shell=True).decode().strip()
            system_info['package_count'] = package_count
        except:
            pass
    
    # Get memory info
    try:
        with open('/proc/meminfo', 'r') as f:
            mem_info = {}
            for line in f:
                if ':' in line:
                    k, v = line.rstrip().split(':', 1)
                    mem_info[k] = v.strip()
            
            total_mem = mem_info.get('MemTotal', '').replace(' kB', '')
            if total_mem:
                system_info['memory'] = f"{int(total_mem) // 1024} MB"
    except:
        pass
    
    # Get CPU info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_model = None
            for line in f:
                if 'model name' in line and not cpu_model:
                    cpu_model = line.rstrip().split(':', 1)[1].strip()
                    break
            if cpu_model:
                system_info['cpu'] = cpu_model
    except:
        pass
    
    return system_info

def get_file_content(filepath, max_size_kb=100, show_errors=True):
    """Read file content if file exists and is not too large"""
    path = Path(filepath)
    
    if not path.exists():
        return None if not show_errors else f"File does not exist: {filepath}"
    
    # Check if file is executable binary
    if path.is_file() and os.access(path, os.X_OK):
        try:
            file_type = subprocess.check_output(['file', str(path)]).decode().strip()
            if 'executable' in file_type and 'text' not in file_type:
                return f"Binary executable file: {filepath}\nType: {file_type}"
        except:
            pass
    
    # Check file size
    file_size_kb = path.stat().st_size / 1024
    if file_size_kb > max_size_kb:
        return None if not show_errors else f"File too large ({file_size_kb:.1f} KB): {filepath}"
    
    # Try to read as text
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return None if not show_errors else f"Binary file (not displayable as text): {filepath}"
    except Exception as e:
        return None if not show_errors else f"Error reading file {filepath}: {str(e)}"

def scan_directory(dir_path, max_depth=3, current_depth=0, ignore_patterns=None, file_extensions=None, max_file_size_kb=100):
    """Recursively scan directory and collect file information"""
    if current_depth > max_depth:
        return {"message": f"Max depth {max_depth} reached"}
    
    if ignore_patterns is None:
        ignore_patterns = [r'\.git', r'__pycache__', r'node_modules', r'\.venv', r'env', r'venv', 
                          r'\.cache', r'\.npm', r'\.mozilla', r'\.config/google-chrome']
    
    dir_info = {"files": {}, "dirs": {}}
    path = Path(dir_path)
    
    if not path.exists() or not path.is_dir():
        return {"error": f"Directory does not exist or is not accessible: {dir_path}"}
    
    try:
        for item in path.iterdir():
            # Check if item matches any ignore pattern
            if any(re.search(pattern, str(item)) for pattern in ignore_patterns):
                continue
            
            if item.is_file():
                # Check if file extension matches filter (if provided)
                if file_extensions and item.suffix.lower() not in file_extensions:
                    continue
                
                # Get file size
                file_size_kb = item.stat().st_size / 1024
                
                file_info = {
                    "size_kb": round(file_size_kb, 1),
                    "path": str(item)
                }
                
                # Add file to the directory info
                dir_info["files"][item.name] = file_info
            
            elif item.is_dir() and current_depth < max_depth:
                # Recursively scan subdirectory
                subdir_info = scan_directory(
                    item, 
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    ignore_patterns=ignore_patterns,
                    file_extensions=file_extensions,
                    max_file_size_kb=max_file_size_kb
                )
                dir_info["dirs"][item.name] = subdir_info
    except Exception as e:
        return {"error": f"Error scanning directory {dir_path}: {str(e)}"}
    
    return dir_info

def get_default_base_files():
    """Get default 'base files' that provide system context"""
    home = str(Path.home())
    
    base_files = {
        # Window manager configs
        "i3_config": f"{home}/.config/i3/config",
        "sway_config": f"{home}/.config/sway/config",
        
        # Shell configs
        "bashrc": f"{home}/.bashrc",
        "zshrc": f"{home}/.zshrc",
        "bash_profile": f"{home}/.bash_profile",
        "profile": f"{home}/.profile",
        
        # X configs
        "xinitrc": f"{home}/.xinitrc",
        "xresources": f"{home}/.Xresources",
        
        # Editor configs
        "vimrc": f"{home}/.vimrc",
        "nvim_init": f"{home}/.config/nvim/init.vim",
        
        # System configs
        "pacman_conf": "/etc/pacman.conf",
    }
    
    # Filter to only existing files
    return {k: v for k, v in base_files.items() if Path(v).exists()}

def get_project_base_files(project_path):
    """Get common project config files that exist in the project directory"""
    project_base_files = {
        # Python
        "requirements": "requirements.txt",
        "setup": "setup.py",
        "pyproject": "pyproject.toml",
        
        # JavaScript/Node
        "package_json": "package.json",
        "tsconfig": "tsconfig.json",
        
        # General
        "readme": "README.md",
        "makefile": "Makefile",
        "dockerfile": "Dockerfile",
        "gitignore": ".gitignore",
        "env": ".env",
        
        # Configuration
        "config_json": "config.json",
        "config_yaml": "config.yaml",
        "config_toml": "config.toml",
    }
    
    return {k: os.path.join(project_path, v) for k, v in project_base_files.items() 
            if os.path.exists(os.path.join(project_path, v))}

def generate_context_description(project_path, system_info, dir_scan, important_files):
    """Generate a text description of the system and project for Claude"""
    description = [
        "# System and Project Context",
        f"\n## System Information",
    ]
    
    # Add system info
    for key, value in system_info.items():
        if key == 'neofetch':
            description.append(f"\n### Neofetch Output\n```\n{value}\n```")
        else:
            description.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    
    # Add project path if specified
    if project_path:
        description.append(f"\n## Project Overview")
        description.append(f"- **Project Path**: {project_path}")
    
    # Add important file contents
    if important_files:
        description.append(f"\n## Configuration Files")
        for label, file_path in important_files.items():
            file_content = get_file_content(file_path)
            if file_content:
                filename = os.path.basename(file_path)
                description.append(f"\n### {filename} ({label})")
                description.append("```")
                description.append(file_content)
                description.append("```")
    
    # Summarize project structure if path specified
    if project_path and dir_scan:
        description.append(f"\n## Project Structure")
        
        def format_dir_structure(dir_info, prefix=""):
            lines = []
            
            # Add files
            for filename, file_info in dir_info.get("files", {}).items():
                size_info = f" ({file_info.get('size_kb', 0):.1f} KB)"
                lines.append(f"{prefix}- {filename}{size_info}")
            
            # Add directories
            for dirname, subdir_info in dir_info.get("dirs", {}).items():
                lines.append(f"{prefix}- {dirname}/ (directory)")
                lines.extend(format_dir_structure(subdir_info, prefix + "  "))
            
            return lines
        
        description.extend(format_dir_structure(dir_scan))
    
    return "\n".join(description)

def get_keyboard_special_chars():
    """Get a mapping of special characters and how to type them"""
    if not check_dependency('xmodmap'):
        return "xmodmap not found. Install with 'pacman -S xorg-xmodmap'."
    
    try:
        # Get current keyboard mapping
        xmodmap_output = subprocess.check_output(['xmodmap', '-pke']).decode()
        
        # Common special characters to look for
        special_chars = {
            '\\': 'backslash',
            '|': 'pipe',
            '~': 'tilde',
            '!': 'exclamation mark',
            '@': 'at sign',
            '#': 'hash',
            '$': 'dollar sign',
            '%': 'percent',
            '^': 'caret',
            '&': 'ampersand',
            '*': 'asterisk',
            '(': 'left parenthesis',
            ')': 'right parenthesis',
            '-': 'minus',
            '_': 'underscore',
            '+': 'plus',
            '=': 'equals',
            '{': 'left curly brace',
            '}': 'right curly brace',
            '[': 'left bracket',
            ']': 'right bracket',
            ':': 'colon',
            ';': 'semicolon',
            '"': 'double quote',
            "'": 'single quote',
            '<': 'less than',
            '>': 'greater than',
            ',': 'comma',
            '.': 'period',
            '?': 'question mark',
            '/': 'forward slash'
        }
        
        # Parse xmodmap output to find key combinations
        char_mapping = {}
        
        for line in xmodmap_output.splitlines():
            for char, name in special_chars.items():
                if f" {char} " in line:
                    key_code = line.split()[1]
                    key_name = line.split('=')[0].strip()
                    
                    # Determine if shift is needed
                    needs_shift = False
                    if char in '~!@#$%^&*()_+{}|:"<>?':
                        needs_shift = True
                    
                    # Add to mapping
                    if needs_shift:
                        char_mapping[char] = f"Shift + {key_name}"
                    else:
                        char_mapping[char] = key_name
        
        # Format the output
        result = "## Special Character Key Combinations\n\n"
        result += "| Character | Name | Key Combination |\n"
        result += "|-----------|------|----------------|\n"
        
        for char, name in special_chars.items():
            key_combo = char_mapping.get(char, "Not found")
            result += f"| {char} | {name} | {key_combo} |\n"
        
        return result
    except Exception as e:
        return f"Error getting keyboard mapping: {str(e)}"

def lookup_key_for_char(char):
    """Look up how to type a specific character"""
    if not char:
        return "No character specified."
    
    if not check_dependency('xmodmap'):
        return "xmodmap not found. Install with 'pacman -S xorg-xmodmap'."
    
    try:
        # Get current keyboard mapping
        xmodmap_output = subprocess.check_output(['xmodmap', '-pke']).decode()
        
        # Look for the character in the output
        for line in xmodmap_output.splitlines():
            if f" {char} " in line:
                key_code = line.split()[1]
                key_name = line.split('=')[0].strip()
                
                # Determine if shift is needed
                needs_shift = False
                if char in '~!@#$%^&*()_+{}|:"<>?':
                    needs_shift = True
                
                # Format the result
                if needs_shift:
                    return f"To type '{char}': Press Shift + {key_name}"
                else:
                    return f"To type '{char}': Press {key_name}"
        
        return f"Character '{char}' not found in keyboard mapping."
    except Exception as e:
        return f"Error looking up character: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Generate context about your system and project for Claude")
    
    # Main command groups
    main_group = parser.add_argument_group('Main options')
    main_group.add_argument("project_path", nargs="?", default=None, 
                      help="Path to the project directory (optional)")
    main_group.add_argument("--output", "-o", default=None,
                      help="Output file path (default: print to stdout)")
    main_group.add_argument("--json", "-j", action="store_true",
                      help="Output in JSON format (default: formatted text)")
    main_group.add_argument("--clipboard", "-c", action="store_true", default=True,
                      help="Copy output to clipboard (default: True)")
    main_group.add_argument("--no-clipboard", action="store_false", dest="clipboard",
                      help="Don't copy output to clipboard")
    
    # Project options
    project_group = parser.add_argument_group('Project options')
    project_group.add_argument("--important-files", "-i", nargs="+", default=[],
                      help="List of additional important files to include in full")
    project_group.add_argument("--max-depth", "-d", type=int, default=3,
                      help="Maximum directory depth to scan (default: 3)")
    project_group.add_argument("--extensions", "-e", nargs="+", default=None,
                      help="Filter files by these extensions (e.g., .py .js .json)")
    project_group.add_argument("--max-file-size", "-s", type=int, default=100,
                      help="Maximum file size in KB to include content (default: 100)")
    project_group.add_argument("--no-project-base-files", action="store_true",
                      help="Don't auto-detect project config files")
    
    # System options
    system_group = parser.add_argument_group('System options')
    system_group.add_argument("--no-system", action="store_true",
                      help="Don't include system information")
    system_group.add_argument("--no-base-files", action="store_true",
                      help="Don't include base system config files")
    
    # Keyboard options
    keyboard_group = parser.add_argument_group('Keyboard options')
    keyboard_group.add_argument("--keyboard-info", "-k", action="store_true",
                      help="Include information about keyboard layout and special characters")
    keyboard_group.add_argument("--key-lookup", type=str, default=None,
                      help="Look up how to type a specific character (e.g., '\\')")
    keyboard_group.add_argument("--only-keyboard", action="store_true",
                      help="Only output keyboard information (implies --keyboard-info)")
    
    args = parser.parse_args()
    
    # Convert extensions to proper format if provided
    file_extensions = None
    if args.extensions:
        file_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
    
    # Get system information (unless disabled)
    system_info = {} if args.no_system else get_system_info()
    
    # Collect important files
    important_files = {}
    
    # Add system base files (unless disabled)
    if not args.no_base_files:
        important_files.update(get_default_base_files())
    
    # Add project base files if project path specified (unless disabled)
    if args.project_path and not args.no_project_base_files:
        important_files.update(get_project_base_files(args.project_path))
    
    # Add user-specified important files
    for file_path in args.important_files:
        if os.path.exists(file_path):
            important_files[os.path.basename(file_path)] = file_path
    
    # Scan directory if project path specified
    dir_scan = None
    if args.project_path:
        dir_scan = scan_directory(
            args.project_path,
            max_depth=args.max_depth,
            file_extensions=file_extensions,
            max_file_size_kb=args.max_file_size
        )
    
    # Handle keyboard-specific queries first
    if args.key_lookup:
        result = lookup_key_for_char(args.key_lookup)
        print(result)
        if args.clipboard:
            if copy_to_clipboard(result):
                print("\n[Result copied to clipboard.]")
        return
    
    if args.only_keyboard:
        args.keyboard_info = True
        args.no_system = True
        args.no_base_files = True
        
    # Generate keyboard info if requested
    keyboard_special_chars = None
    if args.keyboard_info:
        keyboard_special_chars = get_keyboard_special_chars()
        if args.only_keyboard:
            print(keyboard_special_chars)
            if args.clipboard:
                if copy_to_clipboard(keyboard_special_chars):
                    print("\n[Keyboard info copied to clipboard.]")
            return
    
    # Generate output
    if args.json:
        file_contents = {}
        for label, file_path in important_files.items():
            content = get_file_content(file_path, args.max_file_size, show_errors=False)
            if content:
                file_contents[label] = content
        
        output = {
            "system_info": system_info,
            "project_path": args.project_path,
            "directory_scan": dir_scan,
            "important_files": file_contents
        }
        
        if args.keyboard_info and keyboard_special_chars:
            output["keyboard_info"] = keyboard_special_chars
            
        result = json.dumps(output, indent=2)
    else:
        result = generate_context_description(
            args.project_path,
            system_info,
            dir_scan,
            important_files
        )
        
        # Append keyboard info if requested
        if args.keyboard_info and keyboard_special_chars:
            result += f"\n\n{keyboard_special_chars}"
    
    # Handle output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Output written to {args.output}")
    else:
        print(result)
    
    # Copy to clipboard if requested
    if args.clipboard:
        if copy_to_clipboard(result):
            print("\n[Context copied to clipboard. Paste it at the beginning of your Claude conversation.]")
        else:
            print("\n[Failed to copy to clipboard. Please install xclip or copy the output manually.]")

if __name__ == "__main__":
    main()
