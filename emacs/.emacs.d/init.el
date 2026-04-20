;;; init.el --- Emacs config -*- lexical-binding: t; -*-

;;;; ========================================
;;;; Package Management (leaf)
;;;; ========================================

(eval-and-compile
  (customize-set-variable
   'package-archives '(("org"   . "https://orgmode.org/elpa/")
                       ("melpa" . "https://melpa.org/packages/")
                       ("gnu"   . "https://elpa.gnu.org/packages/")))
  (package-initialize)
  (unless (package-installed-p 'leaf)
    (package-refresh-contents)
    (package-install 'leaf))

  (leaf leaf-keywords
    :ensure t
    :init
    (leaf hydra :ensure t)
    (leaf el-get :ensure t)
    (leaf blackout :ensure t)
    :config
    (leaf-keywords-init)))

(leaf transient-dwim :ensure t)

;;;; ========================================
;;;; Built-in Settings
;;;; ========================================

(leaf cus-edit
  :doc "tools for customizing Emacs and Lisp packages"
  :custom `((custom-file . ,(locate-user-emacs-file "custom.el"))))

(leaf cus-start
  :doc "define customization properties of builtins"
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
            (use-dialog-box . nil)
            (use-file-dialog . nil)
            (menu-bar-mode . nil)
            (tool-bar-mode . nil)
            (scroll-bar-mode . nil)
            (horizontal-scroll-bar . nil)
            (indent-tabs-mode . nil)
            (line-number-mode . nil)
            (column-number-mode . nil)
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
    :custom (byte-compile-warnings . '(cl-functions))))

(leaf autorevert
  :doc "revert buffers when files on disk change"
  :custom ((auto-revert-interval . 0.3)
           (auto-revert-check-vc-info . t))
  :global-minor-mode global-auto-revert-mode)

(leaf delsel
  :doc "delete selection if you insert"
  :global-minor-mode delete-selection-mode)

(leaf paren
  :doc "highlight matching paren"
  :custom ((show-paren-delay . 0.1))
  :global-minor-mode show-paren-mode)

(leaf simple
  :doc "basic editing commands for Emacs"
  :custom ((kill-ring-max . 100)
           (kill-read-only-ok . t)
           (kill-whole-line . t)
           (eval-expression-print-length . nil)
           (eval-expression-print-level . nil)))

(leaf files
  :doc "file input and output commands for Emacs"
  :custom `((auto-save-timeout . 15)
            (auto-save-interval . 60)
            (auto-save-file-name-transforms . '((".*" ,(locate-user-emacs-file "backup/") t)))
            (backup-directory-alist . '((".*" . ,(locate-user-emacs-file "backup"))
                                        (,tramp-file-name-regexp . nil)))
            (version-control . t)
            (delete-old-versions . t)))

(leaf startup
  :doc "process Emacs shell arguments"
  :custom `((auto-save-list-file-prefix . ,(locate-user-emacs-file "backup/.saves-"))))

;;;; ========================================
;;;; Completion (vertico + consult)
;;;; ========================================

(leaf mini-buffer-completion
  :config
  (leaf vertico
    :ensure t
    :global-minor-mode t
    :custom ((vertico-count . 30)
             (vertico-cycle . t)))
  (leaf marginalia
    :ensure t
    :global-minor-mode t)
  (leaf consult :ensure t)
  (leaf orderless
    :ensure t
    :custom ((completion-styles . '(orderless)))))

(leaf affe
  :ensure t
  :after orderless consult
  :custom
  (affe-find-command . "fd --color=never --full-path --hidden --exclude .git"))

(leaf consult-ghq
  :ensure t
  :if (executable-find "ghq"))

;;;; ========================================
;;;; LSP (eglot)
;;;; ========================================

(leaf eglot
  :doc "The Emacs Client for LSP servers"
  :hook ((c-mode . eglot-ensure)
         (c++-mode . eglot-ensure)
         (go-mode . eglot-ensure)
         (rust-mode . eglot-ensure))
  :custom ((eldoc-echo-area-use-multiline-p . nil)
           (eglot-connect-timeout . 600)
           (eglot-server-programs . '((c-mode . ("clangd"))
                                      (c++-mode . ("clangd"))
                                      (go-mode . ("gopls"))
                                      (rust-mode . ("rust-analyzer"))))))

(leaf eglot-booster
  :when (executable-find "emacs-lsp-booster")
  :vc ( :url "https://github.com/jdtsmith/eglot-booster")
  :global-minor-mode t)

;;;; ========================================
;;;; Appearance
;;;; ========================================

(leaf doom-themes
  :ensure t
  :custom
  ((doom-themes-enable-bold . t)
   (doom-themes-enable-italic . t))
  :config
  (load-theme 'doom-Iosvkem t)
  (when (not (display-graphic-p))
    (set-face-attribute 'default nil :background "unspecified-bg")))

(leaf doom-modeline
  :ensure t
  :hook ((after-init-hook . doom-modeline-mode))
  :custom
  ((doom-modeline-buffer-file-name-style . 'truncate-with-project)))

(add-to-list 'default-frame-alist '(alpha 85 85))

;;;; ========================================
;;;; Git
;;;; ========================================

(leaf git-gutter
  :ensure t
  :global-minor-mode t)

;;;; ========================================
;;;; Languages
;;;; ========================================

(leaf go-mode
  :ensure t
  :mode ("\\.go\\'" . go-mode)
  :hook (before-save . gofmt-before-save)
  :custom
  (tab-width . 2))

;;;; ========================================

(provide 'init)
(put 'dired-find-alternate-file 'disabled nil)
