path=($HOME/dev/bin $HOME/.local/bin $HOME/.cargo/bin /usr/local/sbin /usr/local/bin /usr/local/go/bin /usr/sbin /usr/bin /sbin /bin $path)
typeset -U path

(( $+commands[git] )) && eval "$(git gtr completion zsh 2>/dev/null)"

_gtr_init="${XDG_CACHE_HOME:-$HOME/.cache}/gtr/init-gtr.zsh"
[[ -f "$_gtr_init" ]] || eval "$(git gtr init zsh)" || true
source "$_gtr_init" 2>/dev/null || true; unset _gtr_init

#asdf setup
if [[ -f "$HOME/.asdf/asdf.sh" ]]; then
    . "$HOME/.asdf/asdf.sh"
    fpath=(${ASDF_DIR}/completions $fpath)
fi

autoload -Uz compinit
if [[ -n ~/.zcompdump(#qN.mh+24) ]]; then
    compinit
else
    compinit -C
fi

export LANG=en_US.utf8
export LC_TIME=C
export EDITOR='emacsclient -nw -c -a ""'

# emacs keybind
bindkey -e

# delete 'C-j'
bindkey -r '^J'

# default umask
umask 022

# History
HISTFILE=~/.zsh_history
HISTSIZE=1000000
SAVEHIST=1000000
setopt hist_ignore_all_dups
setopt hist_ignore_space
setopt share_history

# history search with fzf
function fzf-history-widget() {
    local selected
    selected=$(fc -rl 1 | awk '{$1=""; print substr($0,2)}' | fzf --no-sort --exact --reverse --height=40% --query="$LBUFFER")
    if [[ -n "$selected" ]]; then
        BUFFER="$selected"
        CURSOR=$#BUFFER
    fi
    zle reset-prompt
}
zle -N fzf-history-widget
bindkey '^R' fzf-history-widget

# key binding of command history
autoload history-search-end
zle -N history-beginning-search-backward-end history-search-end
zle -N history-beginning-search-forward-end history-search-end
bindkey "^P" history-beginning-search-backward-end
bindkey "^N" history-beginning-search-forward-end

# Shell options
setopt auto_cd              # cd by directory name
setopt auto_pushd           # use cd -
setopt ignoreeof            # not exit Ctrl-D
setopt NOHUP nocheckjobs    # for sighup
setopt magic_equal_subst    # completion after '=' (like --prefix=/usr)
setopt noautoremoveslash    # keep trailing slash
setopt null_glob no_nomatch # glob expand
setopt NO_beep nolistbeep   # no bell
setopt interactive_comments # '#' starts comment
unsetopt promptcr           # print if line is one line

# disable flow control (C-s: XOFF, C-q: XON)
stty stop undef
stty start undef

# completion
zstyle ':completion:*:default' menu select=1
zstyle ':completion:*' use-cache true

# load bash_profile
if [ -f ~/.bash_profile ]; then 
    . ~/.bash_profile;
fi

# setup ls coloring
LIST_COLOR=('di=34;1' 'ln=35' 'so=32' 'ex=32;1' 'bd=46;34' 'cd=43;34')
zstyle ':completion:*' list-colors $LIST_COLOR
if [ ! -e ~/.dir_colors ]; then
    dircolors -p > ~/.dir_colors
fi
eval "$(dircolors ~/.dir_colors -b)"

# alias
alias ls='ls --color -F'
alias ll='ls -la'
alias df='df -h'
alias grep='grep --color=auto'
alias copilot='copilot \
     --allow-all-tools \
     --deny-tool="shell(git push)" \
     --deny-tool="shell(git push:*)" \
     --deny-tool="shell(rm)"'

# starship
eval "$(starship init zsh)"

# zsh plugins (after compinit and starship)
source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=244'
source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
