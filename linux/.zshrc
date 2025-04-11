# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n] confirmations, etc.)
# must go above this block; everything else may go below this block.

if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" &>/dev/null
fi

# ------------------------------------------------------------------------------
# 🌐 Oh My Zsh Config
# ------------------------------------------------------------------------------
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"

# Plugins configuration
plugins=(
  git
  command-not-found
  zsh-completions
  web-search
  fzf
  autopep8  # For auto-formatting Python code
  docker
  zsh-users/zsh-history-substring-search # Search command history with substrings
)

# Silence Oh-My-Zsh output during loading
DISABLE_UPDATE_PROMPT=true
DISABLE_AUTO_UPDATE=true
source $ZSH/oh-my-zsh.sh &>/dev/null

# Load performance-sensitive plugins manually
source ${ZSH_CUSTOM:-$ZSH/custom}/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh &>/dev/null
source ${ZSH_CUSTOM:-$ZSH/custom}/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh &>/dev/null

# Add fzf-tab if installed
if [[ -f "${ZSH_CUSTOM:-$ZSH/custom}/plugins/fzf-tab/fzf-tab.plugin.zsh" ]]; then
  source "${ZSH_CUSTOM:-$ZSH/custom}/plugins/fzf-tab/fzf-tab.plugin.zsh" &>/dev/null
fi

# ------------------------------------------------------------------------------
# 🤖 Completion
# ------------------------------------------------------------------------------
autoload -Uz compinit
compinit -d "${ZSH_CACHE_DIR:-$HOME/.zsh_cache}/zcompdump-$ZSH_VERSION" -C &>/dev/null

# Better completion UI
zstyle ':completion:*' menu select
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}' 'r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' group-name ''
zstyle ':fzf-tab:*' switch-group ',' '.'  # Use , and . to navigate in fzf-tab

# Completion waiting dots
COMPLETION_WAITING_DOTS="true"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh &>/dev/null

# ------------------------------------------------------------------------------
# Custom Aliases
# ------------------------------------------------------------------------------
# Use exa for detailed ls with icons
alias ls='exa -lah --icons --color=always'

# File navigation aliases with icons
alias ..='cd ..'                   # Go up one directory
alias ...='cd ../..'                # Go up two directories
alias ....='cd ../../..'            # Go up three directories
alias ~='cd ~'                      # Go to home directory
alias c='clear'                     # Clear terminal screen

# Navigation shortcuts
alias d='cd ~/Documents'            # Go to Documents folder
alias dls='cd ~/Documents && ls'    # List Documents folder

# Git shortcuts with icons
alias gst='git status'              # Show Git status
alias gco='git checkout'            # Git checkout
alias gcm='git commit -m'           # Git commit with message
alias gpl='git pull'                # Git pull
alias gps='git push'                # Git push
alias gl='git log --oneline --graph --decorate'  # Git log in graph form
alias gaa='git add .'               # Git add all changes
alias gbr='git branch'              # Show branches
alias gcl='git clone'               # Git clone

# Docker shortcuts with icons
alias dps='docker ps'               # List running Docker containers
alias dpsa='docker ps -a'           # List all Docker containers
alias di='docker images'            # List Docker images
alias drm='docker rm'               # Remove Docker container
alias rmi='docker rmi'              # Remove Docker image

# System management utilities
alias h='history'                   # Show command history
alias man='man -P cat'              # Man page viewer without pause
alias df='df -h'                    # Disk usage in human-readable format
alias du='du -sh'                   # Disk usage of current directory
alias top='htop'                    # Use htop for task manager (if installed)

# Python environment management
alias venv='python3 -m venv'        # Create a Python virtual environment
alias activate='source ./venv/bin/activate'  # Activate Python virtual environment

# Node.js and NPM shortcuts
alias ni='npm install'              # Install dependencies using npm
alias nis='npm install --save'      # Install and save dependencies
alias nin='npm install --no-save'   # Install dependencies without saving

# Search shortcuts with icons
alias grep='grep --color=auto'      # Highlight matches in grep
alias fgrep='fgrep --color=auto'    # Highlight matches in fgrep
alias egrep='egrep --color=auto'    # Highlight matches in egrep

# Auto-formatting and linting
alias pep8='autopep8 --in-place'    # Automatically format Python files using autopep8
alias lint='flake8'                 # Run flake8 for Python linting

# ------------------------------------------------------------------------------
# Zsh History Substring Search
# ------------------------------------------------------------------------------
# Allows you to search through your Zsh history using substrings
bindkey '^R' history-substring-search-up
bindkey '^S' history-substring-search-down

# ------------------------------------------------------------------------------
# Icon-Related Configuration
# ------------------------------------------------------------------------------
# Add Nerd Fonts support for icons
# To display icons properly in your terminal, you need to have Nerd Fonts installed.
# Install Nerd Fonts and set your terminal to use a Nerd Font patched font.
# For example, you can install the "FiraCode Nerd Font" or "Hack Nerd Font" and configure
# your terminal emulator to use it.

# Example: for exa, icons will be visible for directories, files, and symlinks.
# To make this work, ensure you have a patched font (Nerd Font) installed in your terminal.

# ------------------------------------------------------------------------------
# Welcome Message with Icon
# ------------------------------------------------------------------------------
echo "\n Welcome Neo, follow the white rabbit...\n"
