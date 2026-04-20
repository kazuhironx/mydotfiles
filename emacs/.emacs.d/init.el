;;; init.el --- Emacs config -*- lexical-binding: t; -*-

;;;; ========================================
;;;; Package Management
;;;; ========================================

(setq package-archives
      '(("gnu"   . "https://elpa.gnu.org/packages/")
        ("melpa" . "https://melpa.org/packages/")))
(package-initialize)

(setq custom-file (locate-user-emacs-file "custom.el"))
(when (file-exists-p custom-file)
  (load custom-file))

;;;; ========================================
;;;; Built-in Settings
;;;; ========================================

(use-package emacs
  :custom
  (truncate-lines t)
  (create-lockfiles nil)
  (debug-on-error nil)
  (init-file-debug t)
  (frame-resize-pixelwise t)
  (enable-recursive-minibuffers t)
  (history-length 1000)
  (history-delete-duplicates t)
  (scroll-preserve-screen-position t)
  (scroll-conservatively 100)
  (mouse-wheel-scroll-amount '(1 ((control) . 5)))
  (ring-bell-function #'ignore)
  (text-quoting-style 'straight)
  (use-dialog-box nil)
  (use-file-dialog nil)
  (indent-tabs-mode nil)
  (which-function-mode t)
  (which-func-unknown "")
  (echo-keystrokes 0.1)
  (indicate-empty-lines t)
  (indicate-buffer-boundaries 'right)
  (make-pointer-invisible t)
  (kill-ring-max 100)
  (kill-read-only-ok t)
  (kill-whole-line t)
  (eval-expression-print-length nil)
  (eval-expression-print-level nil)
  :config
  (prefer-coding-system 'utf-8-unix)
  (menu-bar-mode -1)
  (tool-bar-mode -1)
  (scroll-bar-mode -1)
  (global-display-line-numbers-mode 1)
  (defalias 'yes-or-no-p 'y-or-n-p)
  (keyboard-translate ?\C-h ?\C-?))

(use-package files
  :custom
  (auto-save-timeout 15)
  (auto-save-interval 60)
  (auto-save-file-name-transforms `((".*" ,(locate-user-emacs-file "backup/") t)))
  (backup-directory-alist `((".*" . ,(locate-user-emacs-file "backup"))
                            (,tramp-file-name-regexp . nil)))
  (version-control t)
  (delete-old-versions t)
  (auto-save-list-file-prefix (locate-user-emacs-file "backup/.saves-")))

(use-package autorevert
  :custom
  (auto-revert-interval 0.3)
  (auto-revert-check-vc-info t)
  :config
  (global-auto-revert-mode 1))

(use-package delsel
  :config
  (delete-selection-mode 1))

(use-package paren
  :custom
  (show-paren-delay 0.1)
  :config
  (show-paren-mode 1))

(use-package compile
  :custom
  (byte-compile-warnings '(cl-functions)))

;;;; ========================================
;;;; Completion (vertico + consult)
;;;; ========================================

(use-package vertico
  :ensure t
  :custom
  (vertico-count 30)
  (vertico-cycle t)
  :init
  (vertico-mode))

(use-package marginalia
  :ensure t
  :init
  (marginalia-mode))

(use-package consult
  :ensure t)

(use-package orderless
  :ensure t
  :custom
  (completion-styles '(orderless basic)))

(use-package affe
  :ensure t
  :after orderless consult
  :custom
  (affe-find-command "fd --color=never --full-path --hidden --exclude .git"))

(use-package consult-ghq
  :ensure t
  :if (executable-find "ghq"))

;;;; ========================================
;;;; LSP (eglot)
;;;; ========================================

(use-package eglot
  :hook ((c-mode . eglot-ensure)
         (c++-mode . eglot-ensure)
         (go-mode . eglot-ensure)
         (rust-mode . eglot-ensure))
  :custom
  (eldoc-echo-area-use-multiline-p nil)
  (eglot-connect-timeout 600)
  (eglot-server-programs '((c-mode . ("clangd"))
                           (c++-mode . ("clangd"))
                           (go-mode . ("gopls"))
                           (rust-mode . ("rust-analyzer")))))

(use-package eglot-booster
  :if (executable-find "emacs-lsp-booster")
  :after eglot
  :config
  (unless (package-installed-p 'eglot-booster)
    (package-vc-install "https://github.com/jdtsmith/eglot-booster"))
  (eglot-booster-mode))

;;;; ========================================
;;;; Appearance
;;;; ========================================

(use-package doom-themes
  :ensure t
  :custom
  (doom-themes-enable-bold t)
  (doom-themes-enable-italic t)
  :config
  (load-theme 'doom-Iosvkem t)
  (unless (display-graphic-p)
    (set-face-attribute 'default nil :background "unspecified-bg")))

(use-package doom-modeline
  :ensure t
  :hook (after-init . doom-modeline-mode)
  :custom
  (doom-modeline-buffer-file-name-style 'truncate-with-project))

(add-to-list 'default-frame-alist '(alpha 85 85))

;;;; ========================================
;;;; Git
;;;; ========================================

(use-package git-gutter
  :ensure t
  :config
  (global-git-gutter-mode 1))

;;;; ========================================
;;;; Languages
;;;; ========================================

(use-package go-mode
  :ensure t
  :mode "\\.go\\'"
  :hook (before-save . gofmt-before-save)
  :custom
  (tab-width 2))

;;;; ========================================

(provide 'init)
(put 'dired-find-alternate-file 'disabled nil)
