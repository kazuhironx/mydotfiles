(when load-file-name
  (setq user-emacs-directory (file-name-directory load-file-name)))

(add-to-list 'load-path (locate-user-emacs-file "el-get/el-get"))
(unless (require 'el-get nil 'noerror)
  (with-current-buffer
      (url-retrieve-synchronously
       "https://raw.githubusercontent.com/dimitri/el-get/master/el-get-install.el")
    (goto-char (point-max))
    (eval-print-last-sexp)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Packages
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; hc-zenburn
(el-get-bundle elpa:hc-zenburn-theme
  (add-to-list 'custom-theme-load-path default-directory))

;; open-junk-file
(el-get-bundle elpa:open-junk-file)

;; mozc
(when (executable-find "mozc_emacs_helper")
  (el-get-bundle elpa:mozc))

;; helm
(el-get-bundle emacs-helm/helm)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; My Funcs
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(defun my/close-all-buffers ()
  (interactive)
  (mapc 'kill-buffer (buffer-list)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Basic Setting
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'cl-lib)

;; encoding
(set-language-environment "Japanese")
(prefer-coding-system 'utf-8-unix)

;; basic customize variables
(custom-set-variables
 '(auto-save-file-name-transforms (\` ((".*" (\, temporary-file-directory) t))))
 '(backup-directory-alist (\` ((".*" \, temporary-file-directory))))
 '(comment-style (quote multi-line))
 '(create-lockfiles nil)
 '(dabbrev-case-fold-search nil)
 '(delete-auto-save-files t)
 '(delete-selection-mode t)
 '(find-file-visit-truename t)
 '(imenu-auto-rescan t)
 '(inhibit-startup-screen t)
 '(large-file-warning-threshold (* 25 1024 1024))
 '(line-move-visual nil)
 '(package-enable-at-startup nil)
 '(read-file-name-completion-ignore-case t)
 '(set-mark-command-repeat-pop t))

(setq-default horizontal-scroll-bar nil)

;; Coloring
(global-font-lock-mode +1)

;; cursor
(set-cursor-color "chartreuse2")
(blink-cursor-mode t)

;; GC Setting
(setq-default gc-cons-threshold (* gc-cons-threshold 10))

;; echo stroke
(setq-default echo-keystrokes 0.1)

;; emacsを終了するときはM-x exitで
(defalias 'exit 'save-buffers-kill-emacs)

;; リージョンの大文字小文字変換
;; C-x C-u で大文字に
;; C-x C-l で小文字に
(put 'upcase-region 'disabled nil)
(put 'downcase-region 'disabled nil)

;; info for japanese
(auto-compression-mode t)

;; highlight mark region
(transient-mark-mode +1)

;; indicate last line
(setq-default indicate-empty-lines t
              indicate-buffer-boundaries 'right)

;; Disable default scroll bar and tool bar
(when window-system
  (set-scroll-bar-mode 'nil)
  (tool-bar-mode 0))

;; not create backup file and not create auto save file
(setq-default backup-inhibited t)

;; Disable menu bar
(menu-bar-mode -1)

;; not beep
(setq-default ring-bell-function 'ignore)

;; display line infomation
(line-number-mode 1)
(column-number-mode 1)

;; yes-or-no-p
(defalias 'yes-or-no-p 'y-or-n-p)
(setq-default use-dialog-box nil)

;; history
(setq-default history-length 500
              history-delete-duplicates t)

;; run server
(require 'server)
(unless (server-running-p)
  (server-start))

;; which-func
(which-function-mode +1)
(setq-default which-func-unknown "")

;; invisible mouse cursor when editing text
(setq-default make-pointer-invisible t)

;; undo setting
;(setq-default undo-no-redo t
;              undo-limit 600000
;              undo-strong-limit 900000)

;;;; undo-tree
;(global-undo-tree-mode)
;(define-key undo-tree-map (kbd "C-/") 'undo-tree-undo)
;(define-key undo-tree-map (kbd "M-_") 'nil)

;; fill-mode
(setq-default fill-column 80)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Color Theme
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(load-theme 'hc-zenburn t)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Fonts
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(set-face-attribute 'default nil
                    :family "Ricty Diminished Discord"
                    :height 110)
(set-fontset-font (frame-parameter nil 'font)
                  'japanese-jisx0208
                  (cons "Ricty Diminished Discord" "iso10646-1"))
(set-fontset-font (frame-parameter nil 'font)
                  'japanese-jisx0212
                  (cons "Ricty Diminished Discord" "iso10646-1"))
(set-fontset-font (frame-parameter nil 'font)
                  'katakana-jisx0201
                  (cons "Ricty Diminished Discord" "iso10646-1"))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; IME
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(add-hook 'input-method-activate-hook
	  (lambda () (set-cursor-color "gold")))
(add-hook 'input-method-inactivate-hook
	  (lambda () (set-cursor-color "chartreuse2")))

(custom-set-variables
 '(mozc-candidate-style 'echo-area)
 '(mozc-leim-title "[も]"))

(when (and (require 'mozc nil t) (executable-find "mozc_emacs_helper"))
  (setq default-input-method "japanese-mozc")
  (global-set-key (kbd "C-z") 'toggle-input-method))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Global Key Binding
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(setq mac-command-modifier 'super)
(setq mac-option-modifier 'meta)

(keyboard-translate ?\C-h ?\C-?)  ; translate `C-h' to DEL

;; global map
(define-key global-map (kbd "C-o") 'dabbrev-expand)

;; ctl-x-map
(define-key ctl-x-map (kbd "C-c") 'my/close-all-buffers)
(define-key ctl-x-map (kbd "l") 'goto-line)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Helm
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(custom-set-variables
 '(helm-input-idle-delay 0)
 '(helm-exit-idle-delay 0)
 '(helm-candidate-number-limit 500)
 '(helm-ag-insert-at-point 'symbol)
 '(helm-find-files-doc-header "")
 '(helm-command-prefix-key nil))

(with-eval-after-load 'helm
  (helm-descbinds-mode)

  (define-key helm-map (kbd "C-p")   'helm-previous-line)
  (define-key helm-map (kbd "C-n")   'helm-next-line)
  (define-key helm-map (kbd "C-M-n") 'helm-next-source)
  (define-key helm-map (kbd "C-M-p") 'helm-previous-source)
  (define-key helm-map (kbd "C-e") 'helm-editutil-select-2nd-action)
  (define-key helm-map (kbd "C-j") 'helm-editutil-select-3rd-action))

;; helm faces
(with-eval-after-load 'helm-files
  (define-key helm-find-files-map (kbd "C-M-u") 'helm-find-files-down-one-level)
  (define-key helm-find-files-map (kbd "C-c C-o") 'helm-ff-run-switch-other-window))
