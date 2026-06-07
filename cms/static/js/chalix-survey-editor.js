/**
 * Chalix Survey Editor — shared module
 *
 * Provides the survey authoring UI (table of program choices, add/edit popup with WYSIWYG,
 * detail preview modal, link generation) used by both:
 *   - learning-management.js  (primary Learning Management tab)
 *   - chalix-cms-interface.js (legacy evaluation modal)
 *
 * Exposed as window.ChalixSurvey = {
 *   loadSurveyManagement,
 *   createSurveyCampaign,
 *   loadSurveyEditor,
 * }.
 * Depends on: window.CMS_ROLE_DATA (role code), getCookie() available in calling scope
 * OR the module reads document.cookie directly.
 */
(function () {
    'use strict';

    let _popupDirty = false;
    let _popupOpen = false;
    const _fallbackEditors = {};
    const _autoSaveState = new WeakMap();

    function _beforeUnloadGuard(e) {
        if (!_popupOpen || !_popupDirty) return;
        e.preventDefault();
        e.returnValue = '';
    }

    // ─── Utilities ─────────────────────────────────────────────────────────────

    function _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = String(text == null ? '' : text);
        return div.innerHTML;
    }

    function _statusLabel(status) {
        const map = { published: 'Đã phát hành', draft: 'Bản nháp', closed: 'Đã đóng' };
        return map[status] || status || 'Bản nháp';
    }

    function _monthFromIso(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) return '';
        return String(date.getMonth() + 1);
    }

    function _yearFromIso(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) return '';
        return String(date.getFullYear());
    }

    function _renderMonthOptions(selectedMonth) {
        const selected = selectedMonth ? String(selectedMonth) : '';
        const options = ['<option value="">-- Tháng --</option>'];
        for (let month = 1; month <= 12; month += 1) {
            const value = String(month);
            options.push(`<option value="${value}" ${selected === value ? 'selected' : ''}>Tháng ${value}</option>`);
        }
        return options.join('');
    }

    function _renderYearOptions(selectedYear) {
        const currentYear = new Date().getFullYear();
        const selected = selectedYear ? String(selectedYear) : '';
        const options = ['<option value="">-- Năm --</option>'];
        for (let year = currentYear - 5; year <= currentYear + 10; year += 1) {
            const value = String(year);
            options.push(`<option value="${value}" ${selected === value ? 'selected' : ''}>${value}</option>`);
        }
        return options.join('');
    }

    function _buildMonthBoundaryIso(yearValue, monthValue, isEndBoundary) {
        if (!yearValue || !monthValue) return null;
        const year = parseInt(yearValue, 10);
        const month = parseInt(monthValue, 10);
        if (Number.isNaN(year) || Number.isNaN(month) || month < 1 || month > 12) return null;

        const mm = String(month).padStart(2, '0');
        if (!isEndBoundary) {
            return `${year}-${mm}-01T00:00:00`;
        }

        const lastDay = new Date(year, month, 0).getDate();
        const dd = String(lastDay).padStart(2, '0');
        return `${year}-${mm}-${dd}T23:59:59`;
    }

    function _getCsrf() {
        const name = 'csrftoken';
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
        return cookie ? decodeURIComponent(cookie.trim().slice(name.length + 1)) : '';
    }

    function _copyText(text) {
        if (!text) return Promise.reject(new Error('empty text'));

        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text);
        }

        return new Promise(function (resolve, reject) {
            try {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.setAttribute('readonly', '');
                textArea.style.position = 'fixed';
                textArea.style.top = '-1000px';
                textArea.style.left = '-1000px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const ok = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (ok) resolve();
                else reject(new Error('copy command failed'));
            } catch (err) {
                reject(err);
            }
        });
    }

    // ─── Styles ────────────────────────────────────────────────────────────────

    function _ensureStyles() {
        if (document.getElementById('chalix-survey-editor-styles')) return;
        const css = `
            /* Survey Editor panel */
            .chalix-survey-editor {
                margin-top: 20px; border-top: 2px solid #e5e7eb; padding-top: 16px;
            }
            .chalix-survey-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 12px;
            }
            .chalix-survey-header h4 {
                margin: 0; font-size: 15px; font-weight: 600; color: #374151;
            }

            /* Choices table */
            .chalix-survey-table {
                width: 100%; border-collapse: collapse; margin-bottom: 8px;
            }
            .chalix-survey-table th,
            .chalix-survey-table td {
                padding: 8px 10px; border: 1px solid #e5e7eb;
                text-align: left; font-size: 13px;
            }
            .chalix-survey-table th { background: #f9fafb; font-weight: 600; }
            .chalix-choice-name {
                max-width: 280px; overflow: hidden;
                text-overflow: ellipsis; white-space: nowrap;
            }
            .chalix-survey-empty td {
                text-align: center; color: #9ca3af; padding: 20px;
            }

            /* Link area */
            .chalix-survey-link-area { display: flex; flex-direction: column; gap: 6px; }
            .chalix-survey-link-display { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
            .chalix-survey-link-label { font-size: 13px; white-space: nowrap; font-weight: 500; }
            .chalix-survey-link-input {
                max-width: 420px; flex: 1; display: inline-block; vertical-align: middle;
            }
            .chalix-survey-link-msg { font-size: 13px; min-height: 18px; }

            /* Results panel */
            .chalix-survey-results {
                margin-top: 18px;
                border-top: 1px solid #e5e7eb;
                padding-top: 14px;
            }
            .chalix-survey-results-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            .chalix-survey-results-total {
                font-size: 13px;
                color: #4b5563;
                margin-bottom: 8px;
            }
            .chalix-survey-results-table {
                width: 100%;
                border-collapse: collapse;
            }
            .chalix-survey-results-table th,
            .chalix-survey-results-table td {
                border: 1px solid #e5e7eb;
                padding: 8px 10px;
                font-size: 13px;
            }
            .chalix-survey-results-table th:last-child,
            .chalix-survey-results-table td:last-child {
                text-align: center;
                white-space: nowrap;
            }
            .chalix-survey-results-bar {
                width: 100%;
                background: #eef2ff;
                border-radius: 6px;
                overflow: hidden;
                height: 8px;
            }
            .chalix-survey-results-bar-fill {
                height: 8px;
                background: #3b82f6;
            }
            .chalix-respondents-empty {
                color: #9ca3af;
                padding: 12px 0;
                text-align: center;
            }
            .chalix-respondents-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 8px;
            }
            .chalix-respondents-table th,
            .chalix-respondents-table td {
                border: 1px solid #e5e7eb;
                padding: 8px 10px;
                font-size: 13px;
                vertical-align: top;
            }
            .chalix-respondents-table th {
                background: #f9fafb;
                font-weight: 600;
            }

            /* Field errors */
            .chalix-field-err {
                color: #dc2626; font-size: 12px; margin-top: 4px; min-height: 16px;
            }

            /* Popup overlay */
            .chalix-choice-popup-overlay {
                position: fixed; inset: 0; background: rgba(0,0,0,.45);
                display: flex; justify-content: center; align-items: center;
                z-index: 10100;
            }
            .chalix-choice-popup-box {
                background: #fff; border-radius: 8px; padding: 24px;
                width: min(92vw, 680px); max-height: 90vh; overflow-y: auto;
                box-shadow: 0 8px 32px rgba(0,0,0,.2);
            }
            .chalix-choice-popup-header { margin-bottom: 16px; }
            .chalix-choice-popup-header h4 { margin: 0; font-size: 16px; font-weight: 600; }
            .chalix-choice-popup-body {
                display: flex; flex-direction: column; gap: 4px;
                padding-right: 8px;
            }
            .chalix-choice-popup-body input,
            .chalix-choice-popup-body textarea {
                width: 100%; box-sizing: border-box;
            }
            .chalix-choice-popup-body .tox-tinymce {
                max-width: 100%;
            }
            .chalix-choice-popup-actions {
                display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px;
            }
            /* Detail preview body */
            .chalix-detail-body { line-height: 1.6; }
            .chalix-detail-body p { margin: 0 0 8px; }

            /* Fallback rich-text editor (when TinyMCE is unavailable) */
            .chalix-rich-editor-fallback {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: #fff;
                overflow: hidden;
            }
            .chalix-rich-toolbar {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                padding: 8px;
                border-bottom: 1px solid #e5e7eb;
                background: #f9fafb;
            }
            .chalix-rich-toolbar button {
                border: 1px solid #d1d5db;
                background: #fff;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                cursor: pointer;
            }
            .chalix-rich-editable {
                min-height: 160px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
                outline: none;
                overflow-wrap: break-word;
                word-break: break-word;
            }
            .chalix-rich-editable i,
            .chalix-rich-editable em,
            .chalix-detail-body i,
            .chalix-detail-body em {
                font-style: italic !important;
            }
        `;
        const style = document.createElement('style');
        style.id = 'chalix-survey-editor-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    // ─── WYSIWYG helpers ───────────────────────────────────────────────────────

    function _initFallbackRichEditor(textareaId, initialHtml) {
        const textarea = document.getElementById(textareaId);
        const fallbackWrap = document.getElementById(textareaId + '-fallback');
        const editable = document.getElementById(textareaId + '-rich');
        if (!textarea || !fallbackWrap || !editable) return;

        textarea.style.display = 'none';
        fallbackWrap.style.display = 'block';
        editable.innerHTML = initialHtml || textarea.value || '';

        const syncToTextarea = function () {
            textarea.value = editable.innerHTML;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        };

        const toolbarHandler = function (event) {
            const btn = event.target.closest('button[data-cmd]');
            if (!btn) return;
            event.preventDefault();
            const cmd = btn.getAttribute('data-cmd');
            if (cmd === 'createLink') {
                const url = window.prompt('Nhập URL liên kết:', 'https://');
                if (url) document.execCommand('createLink', false, url);
            } else {
                document.execCommand(cmd, false, null);
            }
            editable.focus();
            syncToTextarea();
        };

        const toolbar = fallbackWrap.querySelector('.chalix-rich-toolbar');
        const toolbarMouseDownHandler = function (event) {
            // Keep current selection in the editable area when clicking toolbar buttons.
            if (event.target.closest('button[data-cmd]')) {
                event.preventDefault();
            }
        };
        if (toolbar) toolbar.addEventListener('mousedown', toolbarMouseDownHandler);
        if (toolbar) toolbar.addEventListener('click', toolbarHandler);
        editable.addEventListener('input', syncToTextarea);
        editable.addEventListener('blur', syncToTextarea);
        syncToTextarea();

        _fallbackEditors[textareaId] = {
            destroy: function () {
                if (toolbar) {
                    toolbar.removeEventListener('mousedown', toolbarMouseDownHandler);
                    toolbar.removeEventListener('click', toolbarHandler);
                }
                editable.removeEventListener('input', syncToTextarea);
                editable.removeEventListener('blur', syncToTextarea);
                fallbackWrap.style.display = 'none';
                textarea.style.display = '';
            },
            getContent: function () {
                return editable.innerHTML || '';
            }
        };
    }

    function _initWysiwyg(textareaId, initialHtml) {
        const textarea = document.getElementById(textareaId);
        if (textarea) {
            textarea.value = initialHtml || textarea.value || '';
        }

        if (typeof tinymce === 'undefined') {
            _initFallbackRichEditor(textareaId, initialHtml);
            return;
        }
        try {
            tinymce.init({
                selector: '#' + textareaId,
                menubar: false,
                plugins: 'lists link',
                toolbar: 'bold italic underline | bullist numlist | link | removeformat',
                branding: false,
                height: 200,
                setup: function (editor) {
                    editor.on('init', function () {
                        if (initialHtml) editor.setContent(initialHtml);
                    });
                    editor.on('change keyup', function () {
                        const el = document.getElementById(textareaId);
                        if (el) el.dispatchEvent(new Event('input', { bubbles: true }));
                    });
                }
            });
        } catch (e) {
            // fallback: plain textarea stays functional
            console.warn('[ChalixSurvey] TinyMCE init failed, using plain textarea:', e);
            _initFallbackRichEditor(textareaId, initialHtml);
            return;
        }

        // If TinyMCE did not attach for any reason, fallback to local rich editor.
        setTimeout(function () {
            const ed = (typeof tinymce !== 'undefined') ? tinymce.get(textareaId) : null;
            if (!ed) _initFallbackRichEditor(textareaId, initialHtml);
        }, 150);
    }

    function _destroyWysiwyg(textareaId) {
        if (typeof tinymce !== 'undefined') {
            try {
                const ed = tinymce.get(textareaId);
                if (ed) ed.remove();
            } catch (e) { /* ignore */ }
        }

        if (_fallbackEditors[textareaId]) {
            _fallbackEditors[textareaId].destroy();
            delete _fallbackEditors[textareaId];
        }
    }

    function _getWysiwygContent(textareaId) {
        if (typeof tinymce !== 'undefined') {
            try {
                const ed = tinymce.get(textareaId);
                if (ed) return ed.getContent();
            } catch (e) { /* fallthrough */ }
        }

        if (_fallbackEditors[textareaId]) {
            return _fallbackEditors[textareaId].getContent();
        }

        const el = document.getElementById(textareaId);
        return el ? el.value : '';
    }

    // ─── Table rendering ───────────────────────────────────────────────────────

    function _buildChoiceRow(choice, index) {
        const safeId = (typeof choice.id === 'number') ? choice.id : 'new_' + index;
        return `
            <tr class="chalix-choice-row"
                data-idx="${index}"
                data-choice-id="${safeId}">
                <td class="chalix-choice-name" title="${_escapeHtml(choice.name)}">${_escapeHtml(choice.name)}</td>
                <td style="white-space:nowrap;">
                    <button class="lm-btn secondary chalix-detail-btn"
                            style="padding:4px 10px;font-size:12px;"
                            title="${_escapeHtml(choice.name)}">Chi tiết</button>
                </td>
                <td style="white-space:nowrap;">
                    <button class="lm-btn secondary chalix-edit-row-btn"
                            style="padding:4px 10px;font-size:12px;">Sửa</button>
                    <button class="lm-btn danger chalix-delete-row-btn"
                            style="padding:4px 10px;font-size:12px;margin-left:4px;">Xóa</button>
                </td>
            </tr>
        `;
    }

    function _rerenderTable(sectionEl, choicesState) {
        const tbody = sectionEl.querySelector('.chalix-survey-tbody');
        if (!tbody) return;
        if (choicesState.length === 0) {
            tbody.innerHTML = '<tr class="chalix-survey-empty"><td colspan="3">Chưa có chương trình nào. Nhấn "+ Thêm chương trình" để bắt đầu.</td></tr>';
        } else {
            tbody.innerHTML = choicesState.map((c, i) => _buildChoiceRow(c, i)).join('');
        }
        _wireRowEvents(sectionEl, choicesState);
        if (typeof sectionEl._queueAutoSave === 'function') {
            sectionEl._queueAutoSave();
        }
    }

    // ─── Row-level event wiring ────────────────────────────────────────────────

    function _wireRowEvents(sectionEl, choicesState) {
        sectionEl.querySelectorAll('.chalix-detail-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const row = btn.closest('.chalix-choice-row');
                const idx = parseInt(row.dataset.idx, 10);
                _openDetailModal(choicesState[idx]);
            });
        });

        sectionEl.querySelectorAll('.chalix-edit-row-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const row = btn.closest('.chalix-choice-row');
                const idx = parseInt(row.dataset.idx, 10);
                _openChoiceEditor(choicesState[idx], choicesState, sectionEl);
            });
        });

        sectionEl.querySelectorAll('.chalix-delete-row-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const row = btn.closest('.chalix-choice-row');
                const idx = parseInt(row.dataset.idx, 10);
                choicesState.splice(idx, 1);
                _rerenderTable(sectionEl, choicesState);
            });
        });
    }

    // ─── Choice editor popup ───────────────────────────────────────────────────

    function _openChoiceEditor(existingChoice, choicesState, sectionEl) {
        const stale = document.getElementById('chalix-choice-popup');
        if (stale) {
            _popupOpen = false;
            _popupDirty = false;
            window.removeEventListener('beforeunload', _beforeUnloadGuard);
            stale.remove();
        }

        const isNew = !existingChoice;
        const popup = document.createElement('div');
        popup.id = 'chalix-choice-popup';
        popup.className = 'chalix-choice-popup-overlay';
        popup.setAttribute('role', 'dialog');
        popup.setAttribute('aria-modal', 'true');
        popup.innerHTML = `
            <div class="chalix-choice-popup-box"
                 aria-label="${isNew ? 'Thêm chương trình' : 'Sửa chương trình'}">
                <div class="chalix-choice-popup-header">
                    <h4>${isNew ? 'Thêm chương trình' : 'Sửa chương trình'}</h4>
                </div>
                <div class="chalix-choice-popup-body">
                    <label class="lm-form-label" for="chalix-choice-name"
                           style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">
                        Tên chương trình <span style="color:#dc2626">*</span>
                    </label>
                    <input type="text" id="chalix-choice-name"
                              aria-describedby="chalix-choice-name-err"
                           style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;"
                           maxlength="500" autocomplete="off"
                           placeholder="Nhập tên chương trình đào tạo..."
                           value="${_escapeHtml(existingChoice ? existingChoice.name : '')}">
                    <div id="chalix-choice-name-err" class="chalix-field-err"
                         aria-live="polite"></div>

                    <label class="lm-form-label" for="chalix-choice-detail"
                           style="font-size:13px;font-weight:600;display:block;margin:14px 0 4px;">
                        Chi tiết mô tả chương trình <span style="color:#dc2626">*</span>
                    </label>
                    <div id="chalix-choice-detail-fallback" class="chalix-rich-editor-fallback" style="display:none;">
                        <div class="chalix-rich-toolbar">
                            <button type="button" data-cmd="bold"><strong>B</strong></button>
                            <button type="button" data-cmd="italic"><em>I</em></button>
                            <button type="button" data-cmd="underline"><u>U</u></button>
                            <button type="button" data-cmd="insertUnorderedList">• List</button>
                            <button type="button" data-cmd="insertOrderedList">1. List</button>
                            <button type="button" data-cmd="createLink">Link</button>
                            <button type="button" data-cmd="removeFormat">Clear</button>
                        </div>
                        <div id="chalix-choice-detail-rich" class="chalix-rich-editable" contenteditable="true"></div>
                    </div>
                    <textarea id="chalix-choice-detail"
                              aria-describedby="chalix-choice-detail-err"
                              style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;min-height:140px;resize:vertical;"
                              rows="6"
                              placeholder="Nhập mô tả chi tiết về chương trình..."
                    ></textarea>
                    <div id="chalix-choice-detail-err" class="chalix-field-err"
                         aria-live="polite"></div>
                </div>
                <div class="chalix-choice-popup-actions">
                    <button class="lm-btn secondary chalix-popup-discard"
                            style="padding:8px 20px;">Discard</button>
                    <button class="lm-btn primary chalix-popup-save"
                            style="padding:8px 20px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer;">Save</button>
                </div>
            </div>
        `;
        document.body.appendChild(popup);

        const nameInput = popup.querySelector('#chalix-choice-name');
        const detailInput = popup.querySelector('#chalix-choice-detail');
        detailInput.value = existingChoice ? (existingChoice.detail_html || '') : '';

        _popupOpen = true;
        _popupDirty = false;
        window.addEventListener('beforeunload', _beforeUnloadGuard);

        nameInput.addEventListener('input', function () { _popupDirty = true; });
        detailInput.addEventListener('input', function () { _popupDirty = true; });
        nameInput.focus();

        _initWysiwyg('chalix-choice-detail', detailInput.value);

        const close = function () {
            _destroyWysiwyg('chalix-choice-detail');
            _popupOpen = false;
            _popupDirty = false;
            window.removeEventListener('beforeunload', _beforeUnloadGuard);
            popup.remove();
        };

        popup.querySelector('.chalix-popup-discard').addEventListener('click', close);
        popup.addEventListener('click', function (e) { if (e.target === popup) close(); });
        popup.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

        popup.querySelector('.chalix-popup-save').addEventListener('click', function () {
            const name = nameInput.value.trim();
            const detailHtml = _getWysiwygContent('chalix-choice-detail');

            let valid = true;
            popup.querySelector('#chalix-choice-name-err').textContent = '';
            popup.querySelector('#chalix-choice-detail-err').textContent = '';

            if (!name) {
                popup.querySelector('#chalix-choice-name-err').textContent =
                    'Tên chương trình không được để trống';
                nameInput.focus();
                valid = false;
            }
            // Strip all tags and check there's actual text
            if (!detailHtml || !detailHtml.replace(/<[^>]+>/g, '').trim()) {
                popup.querySelector('#chalix-choice-detail-err').textContent =
                    'Chi tiết mô tả không được để trống';
                valid = false;
            }
            if (!valid) return;

            if (existingChoice) {
                existingChoice.name = name;
                existingChoice.detail_html = detailHtml;
            } else {
                choicesState.push({ name: name, detail_html: detailHtml });
            }

            _popupDirty = false;
            _rerenderTable(sectionEl, choicesState);
            close();
        });
    }

    // ─── Detail preview modal ──────────────────────────────────────────────────

    function _openDetailModal(choice) {
        const stale = document.getElementById('chalix-detail-modal');
        if (stale) stale.remove();

        const detailHtml = _decodeHtmlEntities(choice && choice.detail_html ? choice.detail_html : '');

        const modal = document.createElement('div');
        modal.id = 'chalix-detail-modal';
        modal.className = 'chalix-choice-popup-overlay';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        // detail_html is sanitised server-side by bleach; safe to assign as innerHTML
        modal.innerHTML = `
            <div class="chalix-choice-popup-box" style="max-width:600px;">
                <div class="chalix-choice-popup-header">
                    <h4>${_escapeHtml(choice.name)}</h4>
                </div>
                <div class="chalix-choice-popup-body chalix-detail-body">
                    ${detailHtml || '<p>Chưa có mô tả chi tiết.</p>'}
                </div>
                <div class="chalix-choice-popup-actions">
                    <button class="lm-btn secondary chalix-detail-close"
                            style="padding:8px 20px;">Đóng</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.querySelector('.chalix-detail-close').addEventListener('click', function () { modal.remove(); });
        modal.addEventListener('click', function (e) { if (e.target === modal) modal.remove(); });
        modal.addEventListener('keydown', function (e) { if (e.key === 'Escape') modal.remove(); });
        modal.querySelector('.chalix-detail-close').focus();
    }

    function _decodeHtmlEntities(html) {
        if (!html) return '';
        const textarea = document.createElement('textarea');
        textarea.innerHTML = html;
        return textarea.value;
    }

    // ─── Link display ──────────────────────────────────────────────────────────

    function _showGeneratedLink(sectionEl, link) {
        let display = sectionEl.querySelector('.chalix-survey-link-display');
        if (!display) {
            display = document.createElement('div');
            display.className = 'chalix-survey-link-display';
            const linkArea = sectionEl.querySelector('.chalix-survey-link-area');
            const msgEl = sectionEl.querySelector('.chalix-survey-link-msg');
            linkArea.insertBefore(display, msgEl);
        }
        display.innerHTML = `
            <span class="chalix-survey-link-label">Link khảo sát:</span>
            <input type="text" class="chalix-survey-link-input"
                   style="flex:1;max-width:420px;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;"
                   readonly value="${_escapeHtml(link)}" />
            <button class="lm-btn secondary chalix-copy-link-btn"
                    style="padding:6px 14px;white-space:nowrap;">Sao chép</button>
        `;
        display.querySelector('.chalix-copy-link-btn').addEventListener('click', function () {
            _copyText(link).then(function () {
                const btn = display.querySelector('.chalix-copy-link-btn');
                btn.textContent = '✅ Đã sao chép';
                setTimeout(function () { btn.textContent = 'Sao chép'; }, 2000);
            }).catch(function () {
                const input = display.querySelector('.chalix-survey-link-input');
                if (input) input.select();
            });
        });
    }

    function _openRespondentsModal(choiceId, choiceName) {
        const stale = document.getElementById('chalix-respondents-modal');
        if (stale) stale.remove();

        const modal = document.createElement('div');
        modal.id = 'chalix-respondents-modal';
        modal.className = 'chalix-choice-popup-overlay';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.innerHTML = `
            <div class="chalix-choice-popup-box" style="max-width:900px;">
                <div class="chalix-choice-popup-header">
                    <h4>Chi tiết thành viên - ${_escapeHtml(choiceName || '')}</h4>
                </div>
                <div class="chalix-choice-popup-body">
                    <div class="chalix-respondents-content" style="padding:10px;color:#6b7280;">Đang tải danh sách thành viên...</div>
                </div>
                <div class="chalix-choice-popup-actions">
                    <button class="lm-btn secondary chalix-respondents-close" style="padding:8px 20px;">Đóng</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        const close = function () { modal.remove(); };
        modal.querySelector('.chalix-respondents-close').addEventListener('click', close);
        modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
        modal.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
        modal.querySelector('.chalix-respondents-close').focus();

        fetch('/api/chalix/surveys/choice/' + choiceId + '/respondents/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) {
                throw new Error(data.error || 'Không thể tải danh sách thành viên');
            }

            const container = modal.querySelector('.chalix-respondents-content');
            const respondents = data.respondents || [];
            if (!respondents.length) {
                container.innerHTML = '<div class="chalix-respondents-empty">Chưa có thành viên nào chọn chương trình này.</div>';
                return;
            }

            const rows = respondents.map(function (item) {
                let submittedAt = item.submitted_at || '';
                try {
                    if (submittedAt) {
                        submittedAt = new Date(submittedAt).toLocaleString('vi-VN');
                    }
                } catch (e) {
                    // Keep original value if date parse fails
                }

                return `
                    <tr>
                        <td>${_escapeHtml(item.full_name || '')}</td>
                        <td>${_escapeHtml(item.email || '')}</td>
                        <td>${_escapeHtml(item.phone_number || '')}</td>
                        <td>${_escapeHtml(submittedAt)}</td>
                    </tr>
                `;
            }).join('');

            container.innerHTML = `
                <table class="chalix-respondents-table">
                    <thead>
                        <tr>
                            <th>Họ và tên</th>
                            <th>Email</th>
                            <th>Điện thoại</th>
                            <th>Thời gian nộp</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        })
        .catch(function (err) {
            const container = modal.querySelector('.chalix-respondents-content');
            container.innerHTML = '<div style="color:#dc2626;padding:10px;">' + _escapeHtml(err.message || 'Không thể tải danh sách thành viên') + '</div>';
        });
    }

    // ─── Save + publish link ───────────────────────────────────────────────────

    function _renderSurveyResults(sectionEl, surveyId) {
        const resultsArea = sectionEl.querySelector('.chalix-survey-results-content');
        const totalEl = sectionEl.querySelector('.chalix-survey-results-total');
        if (!resultsArea || !totalEl) return;

        resultsArea.innerHTML = '<div style="padding:10px;color:#6b7280;">Đang tải kết quả khảo sát...</div>';
        fetch('/api/chalix/dashboard/surveys/' + surveyId + '/results/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success || !data.results) {
                throw new Error(data.error || 'Không thể tải kết quả khảo sát');
            }
            const results = data.results;
            totalEl.textContent = 'Tổng số phiếu: ' + (results.total_votes || 0);

            const choices = results.choices || [];
            if (!choices.length) {
                resultsArea.innerHTML = '<div style="padding:10px;color:#9ca3af;">Chưa có lựa chọn nào để thống kê.</div>';
                return;
            }

            const rows = choices.map(function (choice) {
                const pct = Number(choice.percentage || 0);
                return `
                    <tr>
                        <td>${_escapeHtml(choice.name || '')}</td>
                        <td style="width:90px;text-align:right;">${choice.vote_count || 0}</td>
                        <td style="width:120px;text-align:right;">${pct.toFixed(2)}%</td>
                        <td style="width:260px;">
                            <div class="chalix-survey-results-bar">
                                <div class="chalix-survey-results-bar-fill" style="width:${Math.max(0, Math.min(100, pct))}%;"></div>
                            </div>
                        </td>
                        <td style="width:170px;">
                            <button class="lm-btn secondary chalix-view-respondents-btn"
                                    data-choice-id="${choice.id}"
                                    data-choice-name="${_escapeHtml(choice.name || '')}"
                                    style="padding:4px 10px;font-size:12px;">Chi tiết thành viên</button>
                        </td>
                    </tr>
                `;
            }).join('');

            resultsArea.innerHTML = `
                <table class="chalix-survey-results-table">
                    <thead>
                        <tr>
                            <th>Tên chương trình</th>
                            <th>Số phiếu</th>
                            <th>Tỷ lệ</th>
                            <th>Biểu đồ</th>
                            <th>Thành viên</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;

            resultsArea.querySelectorAll('.chalix-view-respondents-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    const choiceId = parseInt(btn.getAttribute('data-choice-id'), 10);
                    const choiceName = btn.getAttribute('data-choice-name') || '';
                    if (!Number.isNaN(choiceId)) {
                        _openRespondentsModal(choiceId, choiceName);
                    }
                });
            });
        })
        .catch(function (err) {
            resultsArea.innerHTML = '<div style="padding:10px;color:#dc2626;">' + _escapeHtml(err.message || 'Không thể tải kết quả khảo sát') + '</div>';
        });
    }

    function _buildSurveyPayload(sectionEl, choicesState) {
        const titleInput = sectionEl.querySelector('.chalix-survey-title-input');
        const startMonthInput = sectionEl.querySelector('.chalix-survey-start-month-input');
        const startYearInput = sectionEl.querySelector('.chalix-survey-start-year-input');
        const endMonthInput = sectionEl.querySelector('.chalix-survey-end-month-input');
        const endYearInput = sectionEl.querySelector('.chalix-survey-end-year-input');
        const allowMultipleVotesCheckbox = sectionEl.querySelector('.chalix-allow-multiple-votes-checkbox');
        const allowAddChoiceCheckbox = sectionEl.querySelector('.chalix-allow-add-choice-checkbox');

        return {
            title: titleInput ? titleInput.value.trim() : '',
            starts_at: _buildMonthBoundaryIso(
                startYearInput ? startYearInput.value : '',
                startMonthInput ? startMonthInput.value : '',
                false,
            ),
            ends_at: _buildMonthBoundaryIso(
                endYearInput ? endYearInput.value : '',
                endMonthInput ? endMonthInput.value : '',
                true,
            ),
            allow_multiple_votes: allowMultipleVotesCheckbox ? allowMultipleVotesCheckbox.checked : false,
            allow_add_choice: allowAddChoiceCheckbox ? allowAddChoiceCheckbox.checked : false,
            choices: choicesState.map(function (c, i) {
                const item = { name: c.name, detail_html: c.detail_html, order_index: i };
                if (typeof c.id === 'number') item.id = c.id;
                return item;
            })
        };
    }

    function _saveSurveyDraft(sectionEl, surveyId, choicesState, options) {
        const opts = options || {};
        const isAuto = !!opts.isAuto;
        const msgEl = sectionEl.querySelector('.chalix-survey-link-msg');
        if (msgEl) {
            msgEl.textContent = isAuto ? 'Đang tự động lưu...' : '';
            msgEl.style.color = isAuto ? '#6b7280' : '';
        }

        const payload = _buildSurveyPayload(sectionEl, choicesState);

        return fetch('/api/chalix/dashboard/surveys/' + surveyId + '/save/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': _getCsrf()
            },
            body: JSON.stringify(payload)
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) throw new Error(data.error || 'Không lưu được khảo sát');
            if (msgEl) {
                msgEl.textContent = isAuto ? '✅ Đã tự động lưu' : '✅ Đã lưu bản nháp khảo sát';
                msgEl.style.color = '#16a34a';
            }
            _renderSurveyResults(sectionEl, surveyId);
            return data;
        })
        .catch(function (err) {
            if (msgEl) {
                msgEl.textContent = '❌ ' + err.message;
                msgEl.style.color = '#dc2626';
            }
            throw err;
        });
    }

    function _getAutoSaveState(sectionEl) {
        if (!_autoSaveState.has(sectionEl)) {
            _autoSaveState.set(sectionEl, {
                timer: null,
                inFlight: false,
                pending: false,
            });
        }
        return _autoSaveState.get(sectionEl);
    }

    function _runAutoSave(sectionEl, surveyId, choicesState) {
        const state = _getAutoSaveState(sectionEl);
        if (state.inFlight) {
            state.pending = true;
            return;
        }

        state.inFlight = true;
        _saveSurveyDraft(sectionEl, surveyId, choicesState, { isAuto: true })
        .catch(function () {
            // error already surfaced via message area
        })
        .finally(function () {
            state.inFlight = false;
            if (state.pending) {
                state.pending = false;
                _runAutoSave(sectionEl, surveyId, choicesState);
            }
        });
    }

    function _queueAutoSave(sectionEl, surveyId, choicesState) {
        const state = _getAutoSaveState(sectionEl);
        if (state.timer) window.clearTimeout(state.timer);
        state.timer = window.setTimeout(function () {
            state.timer = null;
            _runAutoSave(sectionEl, surveyId, choicesState);
        }, 900);
    }

    function _cancelAutoSave(sectionEl) {
        const state = _getAutoSaveState(sectionEl);
        if (state.timer) {
            window.clearTimeout(state.timer);
            state.timer = null;
        }
        state.pending = false;
    }

    // ─── Section event wiring ──────────────────────────────────────────────────

    function _wireSectionEvents(sectionEl, surveyId, choicesState) {
        sectionEl._queueAutoSave = function () {
            _queueAutoSave(sectionEl, surveyId, choicesState);
        };

        const titleInput = sectionEl.querySelector('.chalix-survey-title-input');
        if (titleInput) {
            titleInput.addEventListener('input', function () {
                sectionEl._queueAutoSave();
            });
        }

        const startMonthInput = sectionEl.querySelector('.chalix-survey-start-month-input');
        if (startMonthInput) {
            startMonthInput.addEventListener('change', function () {
                sectionEl._queueAutoSave();
            });
        }

        const startYearInput = sectionEl.querySelector('.chalix-survey-start-year-input');
        if (startYearInput) {
            startYearInput.addEventListener('change', function () {
                sectionEl._queueAutoSave();
            });
        }

        const endMonthInput = sectionEl.querySelector('.chalix-survey-end-month-input');
        if (endMonthInput) {
            endMonthInput.addEventListener('change', function () {
                sectionEl._queueAutoSave();
            });
        }

        const endYearInput = sectionEl.querySelector('.chalix-survey-end-year-input');
        if (endYearInput) {
            endYearInput.addEventListener('change', function () {
                sectionEl._queueAutoSave();
            });
        }

        const allowMultipleVotesCheckbox = sectionEl.querySelector('.chalix-allow-multiple-votes-checkbox');
        if (allowMultipleVotesCheckbox) {
            allowMultipleVotesCheckbox.addEventListener('change', function () {
                sectionEl._queueAutoSave();
            });
        }

        const allowAddChoiceCheckbox = sectionEl.querySelector('.chalix-allow-add-choice-checkbox');
        if (allowAddChoiceCheckbox) {
            allowAddChoiceCheckbox.addEventListener('change', function () {
                sectionEl._queueAutoSave();
            });
        }

        sectionEl.querySelector('.chalix-add-choice-btn').addEventListener('click', function () {
            _openChoiceEditor(null, choicesState, sectionEl);
        });

        const copyBtn = sectionEl.querySelector('.chalix-copy-link-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', function () {
                const input = sectionEl.querySelector('.chalix-survey-link-input');
                if (!input) return;
                _copyText(input.value).then(function () {
                    copyBtn.textContent = '✅ Đã sao chép';
                    setTimeout(function () { copyBtn.textContent = 'Sao chép'; }, 2000);
                }).catch(function () {
                    input.select();
                });
            });
        }

        const refreshResultsBtn = sectionEl.querySelector('.chalix-refresh-results-btn');
        if (refreshResultsBtn) {
            refreshResultsBtn.addEventListener('click', function () {
                _renderSurveyResults(sectionEl, surveyId);
            });
        }

        _wireRowEvents(sectionEl, choicesState);
        _renderSurveyResults(sectionEl, surveyId);
    }

    // ─── Render survey editor ──────────────────────────────────────────────────

    function _renderSurveyEditor(container, surveyId, survey) {
        const choices = (survey && survey.choices) ? survey.choices.slice() : [];
        const surveyTitle = (survey && survey.title) ? survey.title : '';
        const startMonth = _monthFromIso(survey && survey.starts_at);
        const startYear = _yearFromIso(survey && survey.starts_at);
        const endMonth = _monthFromIso(survey && survey.ends_at);
        const endYear = _yearFromIso(survey && survey.ends_at);
        const allowMultipleVotes = (survey && survey.allow_multiple_votes) ? true : false;
        const allowAddChoice = (survey && survey.allow_add_choice) ? true : false;

        const section = document.createElement('div');
        section.className = 'chalix-survey-editor';
        section.innerHTML = `
            <div class="chalix-survey-header">
                <h4>Khảo sát nhu cầu đào tạo</h4>
                <button class="lm-btn secondary chalix-add-choice-btn"
                        style="padding:6px 14px;font-size:13px;">+ Thêm chương trình</button>
            </div>

            <div style="margin-bottom:12px;">
                <label style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Tên biểu mẫu khảo sát</label>
                <input type="text" class="chalix-survey-title-input"
                       style="width:100%;max-width:560px;padding:8px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;"
                       maxlength="500"
                       value="${_escapeHtml(surveyTitle)}"
                       placeholder="Nhập tên biểu mẫu khảo sát" />
            </div>

            <div style="margin-bottom:14px;padding:12px;background:#f9fafb;border-radius:6px;border:1px solid #e5e7eb;">
                <h5 style="margin:0 0 10px;font-size:13px;font-weight:600;color:#374151;">Thời gian khảo sát</h5>
                <div style="display:flex;gap:12px;margin-bottom:10px;">
                    <div style="flex:1;">
                        <label style="display:block;font-size:12px;font-weight:500;margin-bottom:4px;">Bắt đầu (Từ tháng):</label>
                        <div style="display:flex;gap:8px;">
                            <select class="chalix-survey-start-month-input"
                                    style="flex:1;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;">${_renderMonthOptions(startMonth)}</select>
                            <select class="chalix-survey-start-year-input"
                                    style="flex:1;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;">${_renderYearOptions(startYear)}</select>
                        </div>
                        <small style="color:#6b7280;font-size:11px;">Để trống = không giới hạn</small>
                    </div>
                    <div style="flex:1;">
                        <label style="display:block;font-size:12px;font-weight:500;margin-bottom:4px;">Kết thúc (Đến tháng):</label>
                        <div style="display:flex;gap:8px;">
                            <select class="chalix-survey-end-month-input"
                                    style="flex:1;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;">${_renderMonthOptions(endMonth)}</select>
                            <select class="chalix-survey-end-year-input"
                                    style="flex:1;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;">${_renderYearOptions(endYear)}</select>
                        </div>
                        <small style="color:#6b7280;font-size:11px;">Để trống = không giới hạn</small>
                    </div>
                </div>

                <div style="display:flex;gap:16px;margin-bottom:8px;">
                    <label style="display:flex;align-items:center;gap:6px;font-size:12px;cursor:pointer;">
                        <input type="checkbox" class="chalix-allow-multiple-votes-checkbox"
                               ${allowMultipleVotes ? 'checked' : ''} />
                        <span>Cho phép chọn nhiều phương án</span>
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;font-size:12px;cursor:pointer;">
                        <input type="checkbox" class="chalix-allow-add-choice-checkbox"
                               ${allowAddChoice ? 'checked' : ''} />
                        <span>Cho phép thêm lựa chọn khác</span>
                    </label>
                </div>
            </div>

            <table class="chalix-survey-table">
                <thead>
                    <tr>
                        <th style="width:55%;">Tên chương trình</th>
                        <th style="width:15%;">Chi tiết</th>
                        <th style="width:30%;"></th>
                    </tr>
                </thead>
                <tbody class="chalix-survey-tbody">
                    ${choices.length === 0
                        ? '<tr class="chalix-survey-empty"><td colspan="3">Chưa có chương trình nào. Nhấn "+ Thêm chương trình" để bắt đầu.</td></tr>'
                        : choices.map(function (c, i) { return _buildChoiceRow(c, i); }).join('')
                    }
                </tbody>
            </table>

            <div class="chalix-survey-results">
                <div class="chalix-survey-results-header">
                    <h5 style="margin:0;font-size:15px;font-weight:600;color:#374151;">Kết quả khảo sát</h5>
                    <button class="lm-btn secondary chalix-refresh-results-btn" style="padding:6px 12px;font-size:12px;">Làm mới kết quả</button>
                </div>
                <div class="chalix-survey-results-total">Tổng số phiếu: 0</div>
                <div class="chalix-survey-results-content"></div>
            </div>
        `;

        container.appendChild(section);
        _wireSectionEvents(section, surveyId, choices);
    }

    // ─── Public entry point ────────────────────────────────────────────────────

    function _renderSurveyList(container, surveys, canAuthor) {
        if (!surveys || surveys.length === 0) {
            container.innerHTML = '<div class="lm-empty">Chưa có khảo sát nào. Nhấn "Tạo khảo sát mới" để bắt đầu.</div>';
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'lm-grid';
        surveys.forEach(function (survey) {
            const card = document.createElement('div');
            card.className = 'lm-card-item';
            card.innerHTML = `
                <div class="lm-card-header">
                    <div class="lm-card-icon">📝</div>
                    <h4 class="lm-card-title">${_escapeHtml(survey.title || 'Khảo sát nhu cầu')}</h4>
                </div>
                <div class="lm-card-meta">${_escapeHtml(_statusLabel(survey.status))} • ${survey.choice_count || 0} chương trình</div>
                <div class="lm-card-actions">
                    <button class="lm-card-btn view" data-action="open-survey" data-id="${survey.id}">Quản lý</button>
                    ${canAuthor ? `<button class="lm-card-btn delete" data-action="archive-survey" data-id="${survey.id}">Lưu trữ</button>` : ''}
                </div>
            `;

            card.querySelector('[data-action="open-survey"]').addEventListener('click', function (e) {
                e.stopPropagation();
                loadSurveyEditor(container, survey.id, canAuthor, { showBackButton: true });
            });

            const archiveBtn = card.querySelector('[data-action="archive-survey"]');
            if (archiveBtn) {
                archiveBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    fetch('/api/chalix/dashboard/surveys/' + survey.id + '/archive/', {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: { 'X-CSRFToken': _getCsrf() }
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (!data.success) throw new Error(data.error || 'Không thể lưu trữ khảo sát');
                        loadSurveyManagement(container, canAuthor);
                    })
                    .catch(function (err) {
                        alert(err.message || 'Không thể lưu trữ khảo sát');
                    });
                });
            }

            card.addEventListener('click', function () {
                loadSurveyEditor(container, survey.id, canAuthor, { showBackButton: true });
            });

            grid.appendChild(card);
        });

        container.innerHTML = '';
        container.appendChild(grid);
    }

    function loadSurveyManagement(container, canAuthor) {
        if (!container) return;
        if (!canAuthor) {
            container.innerHTML = '<div class="lm-empty">Bạn không có quyền quản lý khảo sát nhu cầu.</div>';
            return;
        }

        _ensureStyles();
        container.innerHTML = '<div class="lm-loading">Đang tải danh sách khảo sát...</div>';
        fetch('/api/chalix/dashboard/surveys/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) throw new Error(data.error || 'Không thể tải danh sách khảo sát');
            _renderSurveyList(container, data.surveys || [], canAuthor);
        })
        .catch(function (err) {
            console.error('[ChalixSurvey] list load error:', err);
            container.innerHTML = '<div class="lm-error">Không thể tải danh sách khảo sát nhu cầu</div>';
        });
    }

    function createSurveyCampaign(container, canAuthor) {
        if (!container) return;
        if (!canAuthor) {
            container.innerHTML = '<div class="lm-empty">Bạn không có quyền tạo khảo sát nhu cầu.</div>';
            return;
        }

        container.innerHTML = '<div class="lm-loading">Đang khởi tạo khảo sát mới...</div>';
        fetch('/api/chalix/dashboard/surveys/create/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': _getCsrf()
            },
            body: JSON.stringify({})
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success || !data.survey || !data.survey.id) {
                throw new Error(data.error || 'Không tạo được khảo sát');
            }
            loadSurveyEditor(container, data.survey.id, canAuthor, { showBackButton: true });
        })
        .catch(function (err) {
            container.innerHTML = '<div class="lm-error">' + _escapeHtml(err.message || 'Không tạo được khảo sát') + '</div>';
        });
    }

    /**
     * loadSurveyEditor(container, surveyId, canAuthor, options)
     */
    function loadSurveyEditor(container, surveyId, canAuthor, options) {
        if (!canAuthor) return;
        _ensureStyles();

        if (!surveyId || Number.isNaN(Number(surveyId))) {
            container.innerHTML = '<div class="lm-error">Thiếu mã khảo sát để tải trình chỉnh sửa.</div>';
            return;
        }

        container.innerHTML = '';
        const cfg = options || {};
        if (cfg.showBackButton) {
            const top = document.createElement('div');
            top.style.cssText = 'display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;';
            top.innerHTML = '<button class="lm-btn secondary chalix-survey-back" style="padding:8px 14px;">← Danh sách khảo sát</button>';
            container.appendChild(top);
            const backBtn = top.querySelector('.chalix-survey-back');
            backBtn.addEventListener('click', function () {
                loadSurveyManagement(container, canAuthor);
            });
        }

        const loading = document.createElement('div');
        loading.className = 'lm-loading';
        loading.textContent = 'Đang tải khảo sát...';
        container.appendChild(loading);

        fetch('/api/chalix/dashboard/surveys/' + surveyId + '/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) throw new Error(data.error || 'Không thể tải khảo sát');
            loading.remove();
            const survey = (data.success && data.survey) ? data.survey : null;
            _renderSurveyEditor(container, Number(surveyId), survey);
        })
        .catch(function (err) {
            console.error('[ChalixSurvey] load error:', err);
            loading.remove();
            container.insertAdjacentHTML('beforeend',
                '<div style="color:#6b7280;font-size:13px;margin-top:12px;">Không thể tải khảo sát nhu cầu</div>');
        });
    }

    // ─── Export ────────────────────────────────────────────────────────────────

    window.ChalixSurvey = {
        loadSurveyManagement: loadSurveyManagement,
        createSurveyCampaign: createSurveyCampaign,
        loadSurveyEditor: loadSurveyEditor,
    };

})();
