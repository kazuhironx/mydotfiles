;;; init.el --- "GNU Emacs" main config file -*- mode: Emacs-Lisp; coding: utf-8-unix; lexical-binding: t; -*-

(eval-and-compile
  (customize-set-variable
   'package-archives '(("org" . "https://orgmode.org/elpa/")
		       ("melpa" . "https://melpa.org/packages/")
		       ("gnu" . "https://elpa.gnu.org/packages/")))
  (package-initialize)
  (unless (package-installed-p 'leaf)
    (package-refresh-contents)
    (package-install 'leaf))

  (leaf leaf-keywords
    :ensure t
    :init
    ;; optional packages if you want to use :hydra, :el-get, :blackout,,,
    (leaf hydra :ensure t)
    (leaf el-get :ensure t)
    (leaf blackout :ensure t)

    :config
    ;; initialize leaf-keywords.el
    (leaf-keywords-init)))

(leaf leaf-tree :ensure t)
(leaf leaf-convert :ensure t)
(leaf transient-dwim :ensure t)
(leaf cus-edit
  :doc "tools for customizing Emacs and Lisp packages"
  :tag "builtin" "faces" "help"
  :custom `((custom-file . ,(locate-user-emacs-file "custom.el"))))

(leaf cus-start
  :doc "define customization properties of builtins"
  :tag "builtin" "internal"
  :custom '((prefer-coding-system . 'utf-8-unix)
            (truncate-lines . t)
            (create-lockfiles . nil)
            (debug-on-error . nil)
            (init-file-debug . t)
            (frame-resize-pixelwise . t)
            (enable-recursive-minibuffers . t)
            (history-length . 1000)
            (history-delete-duplicates . t)
            (scroll-preserve-screen-position . t)
            (scroll-conservatively . 100)
            (mouse-wheel-scroll-amount . '(1 ((control) . 5)))
            (ring-bell-function . 'ignore)
            (text-quoting-style . 'straight)
            (truncate-lines . t)
            (use-dialog-box . nil)
            (use-file-dialog . nil)
            (menu-bar-mode . nil)
            (tool-bar-mode . nil)
            (scroll-bar-mode . nil)
            (horizontal-scroll-bar . nil)
            (indent-tabs-mode . nil)
            (line-number-mode . nil)
            (column-number-mode . nil)
            (indent-tabs-mode . nil)
            (which-function-mode . t)
            (which-func-unknown . "")
            (global-display-line-numbers-mode . t)
            (global-font-lock-mode . t)
            (echo-keystrokes . 0.1)
            (indicate-empty-lines . t)
            (indicate-buffer-boundaries . 'right)
            (make-pointer-invisible . t)
            `(gc-cons-threshold . ,(* gc-cons-threshold 10)))
  :config
  (defalias 'yes-or-no-p 'y-or-n-p)
  (keyboard-translate ?\C-h ?\C-?))

(eval-and-compile
  (leaf bytecomp
    :doc "compilation of Lisp code into byte code"
    :tag "builtin" "lisp"
    :custom (byte-compile-warnings . '(cl-functions))))

(leaf autorevert
  :doc "revert buffers when files on disk change"
  :tag "builtin"
  :custom ((auto-revert-interval . 0.3)
           (auto-revert-check-vc-info . t))
  :global-minor-mode global-auto-revert-mode)

(leaf delsel
  :doc "delete selection if you insert"
  :tag "builtin"
  :global-minor-mode delete-selection-mode)

(leaf paren
  :doc "highlight matching paren"
  :tag "builtin"
  :custom ((show-paren-delay . 0.1))
  :global-minor-mode show-paren-mode)

(leaf simple
  :doc "basic editing commands for Emacs"
  :tag "builtin" "internal"
  :custom ((kill-ring-max . 100)
           (kill-read-only-ok . t)
           (kill-whole-line . t)
           (eval-expression-print-length . nil)
           (eval-expression-print-level . nil)))

(leaf files
  :doc "file input and output commands for Emacs"
  :tag "builtin"
  :custom `((auto-save-timeout . 15)
            (auto-save-interval . 60)
            (auto-save-file-name-transforms . '((".*" ,(locate-user-emacs-file "backup/") t)))
            (backup-directory-alist . '((".*" . ,(locate-user-emacs-file "backup"))
                                        (,tramp-file-name-regexp . nil)))
            (version-control . t)
            (delete-old-versions . t)))

(leaf startup
  :doc "process Emacs shell arguments"
  :tag "builtin" "internal"
  :custom `((auto-save-list-file-prefix . ,(locate-user-emacs-file "backup/.saves-"))))

(leaf ivy
  :doc "Incremental Vertical completYon"
  :req "emacs-24.5"
  :tag "matching" "emacs>=24.5"
  :url "https://github.com/abo-abo/swiper"
  :emacs>= 24.5
  :ensure t
  :blackout t
  :leaf-defer nil
  :custom ((ivy-initial-inputs-alist . nil)
           (ivy-re-builders-alist . '((t . ivy--regex-fuzzy)
                                      (swiper . ivy--regex-plus)))
           (ivy-use-selectable-prompt . t))
  :global-minor-mode t
  :config
  (leaf swiper
    :doc "Isearch with an overview. Oh, man!"
    :req "emacs-24.5" "ivy-0.13.0"
    :tag "matching" "emacs>=24.5"
    :url "https://github.com/abo-abo/swiper"
    :emacs>= 24.5
    :ensure t
    :bind (("C-s" . swiper)))

  (leaf counsel
    :doc "Various completion functions using Ivy"
    :req "emacs-24.5" "swiper-0.13.0"
    :tag "tools" "matching" "convenience" "emacs>=24.5"
    :url "https://github.com/abo-abo/swiper"
    :emacs>= 24.5
    :ensure t
    :blackout t
    :bind (("C-x C-i" . counsel-imenu)
           ("C-x C-r" . counsel-recentf)
           ("C-c r" . ivy-resume)
           (ivy-minibuffer-map
            ("M-y" . ivy-next-line)))
    :custom `((counsel-yank-pop-separator . "\n----------\n")
              (counsel-find-file-ignore-regexp . ,(rx-to-string '(or "./" "../") 'no-group))
              (counsel-yank-pop-after-point . t))
    :global-minor-mode t))

(leaf ivy-rich
  :doc "More friendly display transformer for ivy."
  :req "emacs-24.5" "ivy-0.8.0"
  :tag "ivy" "emacs>=24.5"
  :emacs>= 24.5
  :ensure t
  :after ivy
  :global-minor-mode t)

(leaf prescient
  :doc "Better sorting and filtering"
  :req "emacs-25.1"
  :tag "extensions" "emacs>=25.1"
  :url "https://github.com/raxod502/prescient.el"
  :emacs>= 25.1
  :ensure t
  :commands (prescient-persist-mode)
  :custom `((prescient-aggressive-file-save . t)
            (prescient-save-file . ,(locate-user-emacs-file "prescient")))
  :global-minor-mode prescient-persist-mode)

(leaf ivy-prescient
  :doc "prescient.el + Ivy"
  :req "emacs-25.1" "prescient-4.0" "ivy-0.11.0"
  :tag "extensions" "emacs>=25.1"
  :url "https://github.com/raxod502/prescient.el"
  :emacs>= 25.1
  :ensure t
  :after prescient ivy
  :custom ((ivy-prescient-retain-classic-highlighting . t))
  :global-minor-mode t)

(leaf doom-themes
  :doc "an opinionated pack of modern color-themes"
  :req "emacs-25.1" "cl-lib-0.5"
  :tag "nova" "faces" "icons" "neotree" "theme" "one" "atom" "blue" "light" "dark" "emacs>=25.1"
  :added "2020-08-29"
  :url "https://github.com/hlissner/emacs-doom-theme"
  :emacs>= 25.1
  :ensure t
  :custom
  ((doom-themes-enable-bold . t)
   (doom-themes-enable-italic . t))
  :config
  (load-theme 'doom-dark+ t))

(leaf doom-modeline
  :doc "A minimal and modern mode-line"
  :req "emacs-25.1" "all-the-icons-2.2.0" "shrink-path-0.2.0" "dash-2.11.0"
  :tag "mode-line" "faces" "emacs>=25.1"
  :added "2020-08-29"
  :url "https://github.com/seagle0128/doom-modeline"
  :emacs>= 25.1
  :ensure t
  :hook ((after-init-hook . doom-modeline-mode))
  :custom
  ((doom-modeline-buffer-file-name-style . 'truncate-with-project)))
   
(leaf anzu
  :doc "Show number of matches in mode-line while searching"
  :req "emacs-24.3"
  :tag "emacs>=24.3"
  :added "2020-08-29"
  :url "https://github.com/emacsorphanage/anzu"
  :emacs>= 24.3
  :ensure t
  :global-minor-mode global-anzu-mode)

(leaf nyan-mode
  :doc "Nyan Cat shows position in current buffer in mode-line."
  :tag "build something amazing" "pop tart cat" "scrolling" "lulz" "cat" "nyan"
  :added "2020-08-29"
  :url "https://github.com/TeMPOraL/nyan-mode/"
  :ensure t
  :hook ((after-init-hook . nyan-mode)))

(leaf visual-regexp-steroids
  :doc "Extends visual-regexp to support other regexp engines"
  :req "visual-regexp-1.1"
  :tag "feedback" "visual" "python" "replace" "regexp" "foreign" "external"
  :added "2020-08-29"
  :url "https://github.com/benma/visual-regexp-steroids.el/"
  :ensure t
  :bind
  (("M-%" . vr/query-replace)
   ("C-M-r" . vr/isearch-backward)
   ("C-M-s" . vr/isearch-forward))
  :custom
  (vr/engin . 'python))

(leaf multiple-cursors
  :doc "Multiple cursors for Emacs."
  :req "cl-lib-0.5"
  :added "2020-08-29"
  :ensure t
  :bind (("C-c q" . kmz/hydra-multiple-cursors/body))
  :config
  :hydra (kmz/hydra-multiple-cursors
          (:color pink :hint nil)
          "
                                               ╔════════╗
    Point^^           Misc^^                       ║ Cursor ║
  ─────────────────────────────────────────────╨────────╜
     _p_    _P_
     ^↑^^    ^↑^     [_i_] numbers
    mark^^^ skip^^   [_a_] letters
     ^↓^^    ^↓^     [_s_] sort
     _n_    _N_ 
  ╭──────────────────────────────────────────────────────╯
               [_q_]: quit, [Click]: point
"
          ("n" mc/mark-next-like-this)
          ("N" mc/skip-to-next-like-this)
          ("p" mc/mark-previous-like-this)
          ("P" mc/skip-to-previous-like-this)
          ("s" mc/mark-all-in-region-regexp :exit t)
          ("i" mc/insert-numbers :exit t)
          ("a" mc/insert-letters :exit t)
          ("<mouse-1>" mc/add-cursor-on-click)
          ("q" nil)))


(leaf undo-tree
  :doc "Treat undo history as a tree"
  :tag "tree" "history" "redo" "undo" "files" "convenience"
  :added "2020-08-29"
  :url "http://www.dr-qubit.org/emacs.php"
  :ensure t
  :global-minor-mode t)

(leaf rainbow-mode
  :doc "Colorize color names in buffers"
  :tag "faces"
  :added "2020-09-03"
  :url "http://elpa.gnu.org/packages/rainbow-mode.html"
  :ensure t
  :hook (emacs-lisp-mode-hook . rainbow-mode))

(leaf which-key
  :doc "Display available keybindings in popup"
  :req "emacs-24.4"
  :tag "emacs>=24.4"
  :added "2020-08-29"
  :url "https://github.com/justbur/emacs-which-key"
  :emacs>= 24.4
  :ensure t)

(leaf expand-region
  :doc "Increase selected region by semantic units."
  :added "2020-08-29"
  :ensure t
  :bind
  (("C-c k" . er/expand-region))
  :custom
  ((expand-region-contract-fast-key . "j")))

(leaf open-junk-file
  :doc "Open a junk (memo) file to try-and-error"
  :tag "tools" "convenience"
  :added "2020-08-29"
  :url "http://www.emacswiki.org/cgi-bin/wiki/download/open-junk-file.el"
  :ensure t
  :bind (("C-x z" . open-junk-file))
  :custom
  (open-junk-file-format . "~/junk/%Y/%m/%Y-%m-%d-%H%M."))

(leaf git-gutter
  :doc "Port of Sublime Text plugin GitGutter"
  :req "emacs-24.3"
  :tag "emacs>=24.3"
  :added "2020-08-29"
  :url "https://github.com/emacsorphanage/git-gutter"
  :emacs>= 24.3
  :ensure t
  :global-minor-mode t)

(leaf dumb-jump
  :doc "Jump to definition for 40+ languages without configuration"
  :req "emacs-24.3" "s-1.11.0" "dash-2.9.0" "popup-0.5.3"
  :tag "programming" "emacs>=24.3"
  :added "2020-09-03"
  :url "https://github.com/jacktasia/dumb-jump"
  :emacs>= 24.3
  :ensure t
  :init (add-hook 'xref-backend-functions #'dumb-jump-xref-activate)
  :custom ((dumb-jump-selector . 'ivy)
           (dumb-jump-prefer-searcher . 'rg))
  :config
  (dumb-jump-mode))

(leaf smart-jump
  :doc "Smart go to definition."
  :req "emacs-25.1" "dumb-jump-0.5.1"
  :tag "tools" "emacs>=25.1"
  :added "2020-09-03"
  :url "https://github.com/jojojames/smart-jump"
  :emacs>= 25.1
  :ensure t
  :after dumb-jump
  :config (smart-jump-setup-default-registers))

(leaf flycheck
  :doc "On-the-fly syntax checking"
  :req "dash-2.12.1" "pkg-info-0.4" "let-alist-1.0.4" "seq-1.11" "emacs-24.3"
  :tag "minor-mode" "tools" "languages" "convenience" "emacs>=24.3"
  :url "http://www.flycheck.org"
  :emacs>= 24.3
  :ensure t
  :bind (("M-n" . flycheck-next-error)
         ("M-p" . flycheck-previous-error))
  :global-minor-mode global-flycheck-mode)

(leaf company
  :doc "Modular text completion framework"
  :req "emacs-24.3"
  :tag "matching" "convenience" "abbrev" "emacs>=24.3"
  :url "http://company-mode.github.io/"
  :emacs>= 24.3
  :ensure t
  :blackout t
  :leaf-defer nil
  :bind ((company-active-map
          ("M-n" . nil)
          ("M-p" . nil)
          ("C-s" . company-filter-candidates)
          ("C-n" . company-select-next)
          ("C-p" . company-select-previous)
          ("C-M-i" . company-complete-selection))
         (company-search-map
          ("C-n" . company-select-next)
          ("C-p" . company-select-previous)))
  :custom ((company-idle-delay . 0)
           (company-minimum-prefix-length . 1)
           (company-transformers . '(company-sort-by-occurrence)))
  :global-minor-mode global-company-mode)

(leaf company-c-headers
  :doc "Company mode backend for C/C++ header files"
  :req "emacs-24.1" "company-0.8"
  :tag "company" "development" "emacs>=24.1"
  :added "2020-03-25"
  :emacs>= 24.1
  :ensure t
  :after company
  :defvar company-backends
  :config
  (add-to-list 'company-backends 'company-c-headers))

(provide 'init)
(put 'dired-find-alternate-file 'disabled nil)
