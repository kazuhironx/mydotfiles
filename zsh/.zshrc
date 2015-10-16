path=(/usr/local/sbin /usr/local/bin /usr/sbin /usr/bin /sbin /bin)

# emacs keybind
bindkey -e

# enable completion
autoload -U compinit; compinit

# defaut umask
umask 022

# History
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt hist_ignore_all_dups
setopt hist_ignore_dups
setopt hist_ignore_space
setopt share_history

# delete 'C-j'
bindkey -r '^J'

# for incremental search
bindkey '^R' history-incremental-pattern-search-backward
bindkey '^S' history-incremental-pattern-search-forward

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

RPROMPT="%{${fg[blue]}%}[%~]%{${reset_color}%}"

autoload -Uz vcs_info
setopt prompt_subst
zstyle ':vcs_info:git:*' check-for-changes true
zstyle ':vcs_info:git:*' stagedstr "%F{yellow}!"
zstyle ':vcs_info:git:*' unstagedstr "%F{red}+"
zstyle ':vcs_info:*' formats "%F{green}%c%u[%b]%f"
zstyle ':vcs_info:*' actionformats '[%b|%a]'
precmd () { vcs_info }
RPROMPT=$RPROMPT'${vcs_info_msg_0_}'


path=($HOME/bin $path)
