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
;;; Basic Setting
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'cl-lib)

;; encoding
(set-language-environment "Japanese")
(prefer-coding-system 'utf-8-unix)

;; Coloring
(global-font-lock-mode +1)

;; basic customize variables
(custom-set-variables
 '(package-enable-at-startup nil)
 '(large-file-warning-threshold (* 25 1024 1024))
 '(dabbrev-case-fold-search nil)
 '(inhibit-startup-screen t)
 '(read-file-name-completion-ignore-case t)
 '(line-move-visual nil)
 '(set-mark-command-repeat-pop t)
 '(find-file-visit-truename t)
 '(comment-style 'multi-line)
 '(imenu-auto-rescan t)
 '(delete-auto-save-files t)
 '(create-lockfiles nil)
 '(backup-directory-alist `((".*" . ,temporary-file-directory)))
 '(auto-save-file-name-transforms `((".*" ,temporary-file-directory t))))

(setq-default horizontal-scroll-bar nil)

;; cursor
(set-cursor-color "chartreuse2")
(blink-cursor-mode t)

;; for GC
(setq-default gc-cons-threshold (* gc-cons-threshold 10))

;; echo stroke
(setq-default echo-keystrokes 0.1)
;; I never use C-x C-c
(defalias 'exit 'save-buffers-kill-emacs)

;; enable disabled commands
(put 'narrow-to-region 'disabled nil)
(put 'upcase-region 'disabled nil)
(put 'downcase-region 'disabled nil)
(put 'set-goal-column 'disabled nil)

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

(defun close-all-buffers ()
  (interactive)
  (mapc 'kill-buffer (buffer-list)))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Key Binding
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(keyboard-translate ?\C-h ?\C-?)  ; translate `C-h' to DEL

(setq mac-command-modifier 'super)
(setq mac-option-modifier 'meta)

(define-key global-map (kbd "C-o") 'dabbrev-expand)

;; custom of the ctl-x-map
(define-key ctl-x-map (kbd "C-c") 'close-all-buffers)
(define-key ctl-x-map (kbd "l") 'goto-line)
