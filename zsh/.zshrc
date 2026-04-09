path=($HOME/dev/bin $HOME/.local/bin $HOME/.cargo/bin /usr/local/sbin /usr/local/bin /usr/local/go/bin /usr/sbin /usr/bin /sbin /bin $path)

#asdf setup
. "$HOME/.asdf/asdf.sh"
fpath=(${ASDF_DIR}/completions $fpath)
autoload -Uz compinit && compinit

export LANG=en_US.utf8
export LC_TIME=C
export TERM=xterm-256color
export EDITOR=emacs

# emacs keybind
bindkey -e

# delete 'C-j'
bindkey -r '^J'

# enable completion
autoload -U compinit; compinit

# defaut umask
umask 022

# History
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
setopt hist_ignore_all_dups
setopt hist_ignore_dups
setopt hist_ignore_space
setopt share_history

# for incremental search
bindkey '^R' history-incremental-pattern-search-backward
bindkey '^S' history-incremental-pattern-search-forward

# key binding of command history
autoload history-search-end
zle -N history-beginning-search-backward-end history-search-end
zle -N history-beginning-search-forward-end history-search-end
bindkey "^P" history-beginning-search-backward-end
bindkey "^N" history-beginning-search-forward-end

setopt auto_cd

# use cd -
setopt auto_pushd

# not exit Ctrl-D
setopt ignoreeof

# for sighup
setopt NOHUP
setopt nocheckjobs

# stty
stty stop undef

# completion like emacs
zstyle ':completion:*:default' menu select=1

# completion use cache
zstyle ':completion:*' use-cache true

# completion after '='(like --prefix=/usr)
setopt magic_equal_subst

# with slash
setopt noautoremoveslash

# glob expand
setopt null_glob no_nomatch

# print if line is one line
unsetopt promptcr

# Not bell
setopt NO_beep
setopt nolistbeep

# String behind '#' is comment.
setopt interactive_comments

# load bash_profile
if [ -f ~/.bash_profile ]; then 
    . ~/.bash_profile;
fi


# setup ls coloring
local LIST_COLOR='di=34;1' 'ln=35' 'so=32' 'ex=32;1' 'bd=46;34' 'cd=43;34'
zstyle ':completion:*' list-colors $LIST_COLOR
if [ ! -e ~/.dir_colors ]; then
    dircolors -p > ~/.dir_colors
fi
eval `dircolors ~/.dir_colors -b`

# alias
alias ls='ls --color -F'
alias ll='ls -la'
alias df='df -h'
alias grep='grep --color=auto'
alias e='emacsclient'
alias g='git'
alias s='git status'
alias d='git diff '

alias -g G='`ghq list -p | peco`'
alias -g B='`git branch | peco | sed -e "s/^\*[ ]*//g"`'

# starship
eval "$(starship init zsh)"
