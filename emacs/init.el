;;; init.el --- Emacs 30 config -*- lexical-binding: t; -*-

;;;; ========================================
;;;; Package Management
;;;; ========================================

(setq package-archives
      '(("gnu"   . "https://elpa.gnu.org/packages/")
        ("melpa" . "https://melpa.org/packages/")))

(package-initialize)
(setq use-package-always-ensure t)

(setq custom-file (locate-user-emacs-file "custom.el"))
(when (file-exists-p custom-file)
  (load custom-file))

;;;; ========================================
;;;; Built-in Settings
;;;; ========================================

(use-package emacs
  :ensure nil
  :custom
  (truncate-lines t)
  (create-lockfiles nil)
  (debug-on-error nil)
  (init-file-debug t)
  (frame-resize-pixelwise t)
  (enable-recursive-minibuffers t)
  (native-comp-async-report-warnings-errors 'silent)
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
  (keyboard-translate ?\C-h ?\C-?)
  ;; emacsclient -c で作った新フレームにも C-h=BS を適用する
  (add-hook 'after-make-frame-functions
            (lambda (_frame) (keyboard-translate ?\C-h ?\C-?)))
  ;; Disable suspend-frame (useless in tmux, dangerous in terminal)
  (global-unset-key (kbd "C-z"))
  (global-unset-key (kbd "C-x C-z"))
  (global-set-key (kbd "C-o") #'dabbrev-expand))

(use-package server
  :ensure nil
  :config
  (unless (server-running-p)
    (server-start)))

;; .editorconfig があるプロジェクトを開くとインデント幅や改行コードを自動適用
(use-package editorconfig
  :ensure nil
  :config
  (editorconfig-mode 1))

;; C-c u でundo履歴をツリー表示。左右で分岐を移動、上下で時間を遡る
(use-package vundo
  :bind ("C-c u" . vundo)
  :custom
  (vundo-glyph-alist vundo-unicode-symbols))

;; M-% でPCRE正規表現による置換。マッチ箇所をリアルタイムハイライトしながら置換
;; ミニバッファ内で M-n/M-p でプレビューをスクロール可能
(use-package visual-regexp
  :bind (("M-%" . vr/query-replace))
  :config
  (define-key vr/minibuffer-keymap (kbd "M-n") #'scroll-other-window)
  (define-key vr/minibuffer-keymap (kbd "M-p") #'scroll-other-window-down))

(use-package visual-regexp-steroids
  :after visual-regexp
  :requires pcre2el
  :custom
  (vr/engine 'pcre2el))

(use-package pcre2el)

;; C-c m n: 同じ単語の次の出現にカーソル追加 (n連打で続けて追加)
;; C-c m p: 最後に追加したカーソルを取り消し (p連打で続けて取消)
;; C-c m l: 選択範囲の各行にカーソルを置いて一括編集
(use-package multiple-cursors
  :bind (("C-c m n" . my/mc-mark-next)
         ("C-c m p" . my/mc-unmark)
         ("C-c m l" . mc/edit-lines))
  :config
  (add-to-list 'mc/cmds-to-run-once 'my/mc-mark-next)
  (add-to-list 'mc/cmds-to-run-once 'my/mc-unmark)
  (defvar-keymap my/mc-repeat-map
    "n" #'my/mc-mark-next
    "p" #'my/mc-unmark)
  (defun my/mc-mark-next ()
    (interactive)
    (mc/mark-next-like-this 1)
    (set-transient-map my/mc-repeat-map t))
  (defun my/mc-unmark ()
    (interactive)
    (mc/unmark-next-like-this)
    (set-transient-map my/mc-repeat-map t)))

(use-package files
  :ensure nil
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
  :ensure nil
  :custom
  (auto-revert-interval 0.3)
  (auto-revert-check-vc-info t)
  :config
  (global-auto-revert-mode 1))

(use-package tramp
  :ensure nil
  :defer t
  :config
  (setq tramp-default-method "ssh")
  (setq tramp-auto-save-directory "/tmp")
  (setq tramp-verbose 1)
  (setq remote-file-name-inhibit-cache nil))

(use-package delsel
  :ensure nil
  :config
  (delete-selection-mode 1))

(use-package paren
  :ensure nil
  :custom
  (show-paren-delay 0.1)
  :config
  (show-paren-mode 1))

(use-package which-key
  :ensure nil
  :config
  (which-key-mode))

;;;; ========================================
;;;; Tree-sitter grammar sources
;;;; ========================================

;; tree-sitterによる高速・正確なシンタックスハイライト (Emacs 30組み込み)
;; 文法追加: M-x treesit-install-language-grammar で言語を選択してインストール
;; major-mode-remap-alist で従来モードを自動的にts版にリマップ
(use-package treesit
  :ensure nil
  :custom
  (treesit-font-lock-level 4)
  :config
  (setq treesit-language-source-alist
        '((c      "https://github.com/tree-sitter/tree-sitter-c")
          (cpp    "https://github.com/tree-sitter/tree-sitter-cpp")
          (go     "https://github.com/tree-sitter/tree-sitter-go")
          (gomod  "https://github.com/AZMCode/tree-sitter-go-mod")
          (rust   "https://github.com/tree-sitter/tree-sitter-rust")
          (yaml   "https://github.com/ikatyang/tree-sitter-yaml")
          (json   "https://github.com/tree-sitter/tree-sitter-json")))
  ;; Remap to tree-sitter modes
  (setq major-mode-remap-alist
        '((c-mode      . c-ts-mode)
          (c++-mode    . c++-ts-mode)
          (go-mode     . go-ts-mode)
          (rust-mode   . rust-ts-mode)
          (yaml-mode   . yaml-ts-mode)
          (json-mode   . json-ts-mode)))
  ;; Treat .h as C++
  (add-to-list 'auto-mode-alist '("\\.h\\'" . c++-ts-mode)))

;;;; ========================================
;;;; Completion (vertico + consult + embark)
;;;; ========================================

(use-package vertico
  :custom
  (vertico-count 30)
  (vertico-cycle t)
  :init
  (vertico-mode))

(use-package marginalia
  :init
  (marginalia-mode))

;; C-c f: fdでファイル名検索 (1文字入力で結果表示、絞り込み可)
;; C-c s: ripgrepでファイル内容検索 (同上)
;; 検索結果で C-c a → E で wgrep バッファに書き出して一括編集可
(use-package consult
  :bind (("C-c f" . consult-fd)
         ("C-c s" . consult-ripgrep))
  :custom
  (consult-fd-args '("fd" "--full-path" "--color=never"))
  (consult-async-min-input 0))

(use-package orderless
  :custom
  (completion-styles '(orderless basic)))

(use-package corfu
  :custom
  (corfu-auto t)
  (corfu-auto-delay 0.2)
  (corfu-auto-prefix 2)
  (corfu-cycle t)
  :bind (:map corfu-map
         ("M-n" . corfu-next)
         ("M-p" . corfu-previous))
  :init
  (global-corfu-mode))

;; C-c a: カーソル下の対象 (ファイル名,シンボル,URL等) にアクションメニューを表示
;; C-c d: 対象に対して最も自然な操作を即実行 (dwim = do what I mean)
;; 検索結果で C-c a → E: 結果をバッファに書き出し (wgrep連携で一括編集)
(use-package embark
  :bind (("C-c a" . embark-act)
         ("C-c d" . embark-dwim))
  :config
  (setq prefix-help-command #'embark-prefix-help-command))

(use-package embark-consult
  :after embark consult
  :hook (embark-collect-mode . consult-preview-at-point-mode))

(use-package wgrep)

(use-package affe
  :after orderless consult
  :custom
  (affe-find-command "fd --color=never --full-path --hidden --exclude .git"))

(use-package consult-ghq
  :if (executable-find "ghq"))

;;;; ========================================
;;;; LSP (eglot)
;;;; ========================================

(use-package eglot
  :ensure nil
  :hook ((c-mode    . eglot-ensure)
         (c++-mode  . eglot-ensure)
         (c-ts-mode . eglot-ensure)
         (c++-ts-mode . eglot-ensure)
         (go-mode   . eglot-ensure)
         (go-ts-mode . eglot-ensure)
         (rust-mode . eglot-ensure)
         (rust-ts-mode . eglot-ensure)
         (python-mode . eglot-ensure)
         (python-ts-mode . eglot-ensure))
  :custom
  (eldoc-echo-area-use-multiline-p nil)
  (eglot-connect-timeout 600)
  :config
  (add-to-list 'eglot-server-programs '((c-mode c-ts-mode c++-mode c++-ts-mode) "clangd"))
  (add-to-list 'eglot-server-programs '((go-mode go-ts-mode) "gopls"))
  (add-to-list 'eglot-server-programs '((rust-mode rust-ts-mode) "rust-analyzer")))

(use-package eglot-booster
  :if (executable-find "emacs-lsp-booster")
  :vc (:url "https://github.com/jdtsmith/eglot-booster")
  :after eglot
  :config
  (eglot-booster-mode))

;;;; ========================================
;;;; Appearance
;;;; ========================================

(use-package doom-themes
  :custom
  (doom-themes-enable-bold t)
  (doom-themes-enable-italic t)
  :config
  (load-theme 'doom-Iosvkem t)
  (unless (display-graphic-p)
    (set-face-attribute 'default nil :background "unspecified-bg")))

(use-package doom-modeline
  :hook (after-init . doom-modeline-mode)
  :custom
  (doom-modeline-buffer-file-name-style 'truncate-with-project))

(add-to-list 'default-frame-alist '(alpha 85 85))

(use-package rainbow-delimiters
  :hook (prog-mode . rainbow-delimiters-mode))

;;;; ========================================
;;;; Git
;;;; ========================================

(use-package magit
  :bind ("C-c g" . magit-status))

(use-package diff-hl
  :demand t
  :config
  (global-diff-hl-mode 1)
  (require 'diff-hl-flydiff)
  (diff-hl-flydiff-mode 1)
  (unless (display-graphic-p)
    (diff-hl-margin-mode 1))
  :hook (magit-post-refresh . diff-hl-magit-post-refresh))

;;;; ========================================
;;;; Languages
;;;; ========================================

(use-package markdown-mode
  :mode ("\\.md\\'" . gfm-mode)
  :custom
  (markdown-fontify-code-blocks-natively t)
  (markdown-command "pandoc"))

(use-package yaml-ts-mode
  :ensure nil
  :mode ("\\.ya?ml\\'" . yaml-ts-mode))

(use-package json-ts-mode
  :ensure nil
  :mode ("\\.json\\'" . json-ts-mode))

(use-package go-mode
  :mode "\\.go\\'"
  :hook (before-save . gofmt-before-save)
  :custom
  (tab-width 2))

(use-package go-ts-mode
  :ensure nil
  :hook (before-save . gofmt-before-save)
  :custom
  (tab-width 2))

(use-package rust-ts-mode
  :ensure nil
  :mode "\\.rs\\'")

;;;; ========================================

(provide 'init)
