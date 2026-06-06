/**
 * Chalix Survey Editor — shared module
 *
 * Provides the survey authoring UI (table of program choices, add/edit popup with WYSIWYG,
 * detail preview modal, link generation) used by both:
 *   - learning-management.js  (primary Learning Management tab)
 *   - chalix-cms-interface.js (legacy evaluation modal)
 *
 * Exposed as window.ChalixSurvey = { loadSurveyEditor }.
 * Depends on: window.CMS_ROLE_DATA (role code), getCookie() available in calling scope
 * OR the module reads document.cookie directly.
 */
(function () {
    'use strict';

    let _popupDirty = false;
    let _popupOpen = false;

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

    function _getCsrf() {
        const name = 'csrftoken';
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
        return cookie ? decodeURIComponent(cookie.trim().slice(name.length + 1)) : '';
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
                width: 90%; max-width: 540px; max-height: 90vh; overflow-y: auto;
                box-shadow: 0 8px 32px rgba(0,0,0,.2);
            }
            .chalix-choice-popup-header { margin-bottom: 16px; }
            .chalix-choice-popup-header h4 { margin: 0; font-size: 16px; font-weight: 600; }
            .chalix-choice-popup-body { display: flex; flex-direction: column; gap: 4px; }
            .chalix-choice-popup-actions {
                display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px;
            }
            /* Detail preview body */
            .chalix-detail-body { line-height: 1.6; }
            .chalix-detail-body p { margin: 0 0 8px; }
        `;
        const style = document.createElement('style');
        style.id = 'chalix-survey-editor-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    // ─── WYSIWYG helpers ───────────────────────────────────────────────────────

    function _initWysiwyg(textareaId) {
        if (typeof tinymce === 'undefined') return;
        try {
            tinymce.init({
                selector: '#' + textareaId,
                menubar: false,
                plugins: 'lists link',
                toolbar: 'bold italic underline | bullist numlist | link | removeformat',
                branding: false,
                height: 200,
            });
        } catch (e) {
            // fallback: plain textarea stays functional
            console.warn('[ChalixSurvey] TinyMCE init failed, using plain textarea:', e);
        }
    }

    function _destroyWysiwyg(textareaId) {
        if (typeof tinymce === 'undefined') return;
        try {
            const ed = tinymce.get(textareaId);
            if (ed) ed.remove();
        } catch (e) { /* ignore */ }
    }

    function _getWysiwygContent(textareaId) {
        if (typeof tinymce !== 'undefined') {
            try {
                const ed = tinymce.get(textareaId);
                if (ed) return ed.getContent();
            } catch (e) { /* fallthrough */ }
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

        _initWysiwyg('chalix-choice-detail');

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
                    ${choice.detail_html || '<p>Chưa có mô tả chi tiết.</p>'}
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
            navigator.clipboard.writeText(link).then(function () {
                const btn = display.querySelector('.chalix-copy-link-btn');
                btn.textContent = '✅ Đã sao chép';
                setTimeout(function () { btn.textContent = 'Sao chép'; }, 2000);
            }).catch(function () {
                // clipboard API not available — select input as fallback
                display.querySelector('.chalix-survey-link-input').select();
            });
        });
    }

    // ─── Save + generate link ──────────────────────────────────────────────────

    function _saveSurveyAndGenerateLink(sectionEl, courseKey, choicesState) {
        const genBtn = sectionEl.querySelector('.chalix-gen-link-btn');
        const msgEl = sectionEl.querySelector('.chalix-survey-link-msg');
        genBtn.disabled = true;
        genBtn.textContent = 'Đang xử lý...';
        msgEl.textContent = '';
        msgEl.style.color = '';

        if (!choicesState.length) {
            msgEl.textContent = '❌ Cần có ít nhất một chương trình trước khi tạo link';
            msgEl.style.color = '#dc2626';
            genBtn.disabled = false;
            genBtn.textContent = 'Tạo link khảo sát nhu cầu học tập';
            return;
        }

        const payload = {
            choices: choicesState.map(function (c, i) {
                const item = { name: c.name, detail_html: c.detail_html, order_index: i };
                if (typeof c.id === 'number') item.id = c.id;
                return item;
            })
        };

        fetch('/api/chalix/dashboard/survey/save/' + courseKey + '/', {
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
            if (!data.success) throw new Error(data.error || 'Lỗi không xác định');
            return fetch('/api/chalix/dashboard/survey/generate-link/' + courseKey + '/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'X-CSRFToken': _getCsrf() }
            });
        })
        .then(function (r) { return r.json(); })
        .then(function (linkData) {
            if (!linkData.success) throw new Error(linkData.error || 'Không tạo được link');
            _showGeneratedLink(sectionEl, linkData.link);
            msgEl.textContent = '✅ Đã tạo link thành công!';
            msgEl.style.color = '#16a34a';
        })
        .catch(function (err) {
            msgEl.textContent = '❌ ' + err.message;
            msgEl.style.color = '#dc2626';
        })
        .finally(function () {
            genBtn.disabled = false;
            genBtn.textContent = 'Tạo link khảo sát nhu cầu học tập';
        });
    }

    // ─── Section event wiring ──────────────────────────────────────────────────

    function _wireSectionEvents(sectionEl, courseKey, choicesState) {
        sectionEl.querySelector('.chalix-add-choice-btn').addEventListener('click', function () {
            _openChoiceEditor(null, choicesState, sectionEl);
        });

        sectionEl.querySelector('.chalix-gen-link-btn').addEventListener('click', function () {
            _saveSurveyAndGenerateLink(sectionEl, courseKey, choicesState);
        });

        const copyBtn = sectionEl.querySelector('.chalix-copy-link-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', function () {
                const input = sectionEl.querySelector('.chalix-survey-link-input');
                if (input) navigator.clipboard.writeText(input.value);
            });
        }

        _wireRowEvents(sectionEl, choicesState);
    }

    // ─── Render survey editor ──────────────────────────────────────────────────

    function _renderSurveyEditor(container, courseKey, survey) {
        const choices = (survey && survey.choices) ? survey.choices.slice() : [];
        const existingLink = (survey && survey.public_token)
            ? window.location.origin + '/survey/' + survey.public_token + '/'
            : null;

        const section = document.createElement('div');
        section.className = 'chalix-survey-editor';
        section.innerHTML = `
            <div class="chalix-survey-header">
                <h4>Khảo sát nhu cầu đào tạo, bồi dưỡng</h4>
                <button class="lm-btn secondary chalix-add-choice-btn"
                        style="padding:6px 14px;font-size:13px;">+ Thêm chương trình</button>
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

            <div class="chalix-survey-link-area" style="margin-top:16px;">
                <div>
                    <button class="lm-btn primary chalix-gen-link-btn"
                            style="padding:8px 20px;">Tạo link khảo sát nhu cầu học tập</button>
                </div>
                ${existingLink ? `
                    <div class="chalix-survey-link-display" style="margin-top:8px;">
                        <span class="chalix-survey-link-label">Link hiện tại:</span>
                        <input type="text" class="chalix-survey-link-input"
                               style="flex:1;max-width:420px;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;"
                               readonly value="${_escapeHtml(existingLink)}" />
                        <button class="lm-btn secondary chalix-copy-link-btn"
                                style="padding:6px 14px;white-space:nowrap;">Sao chép</button>
                    </div>
                ` : ''}
                <div class="chalix-survey-link-msg" style="font-size:13px;min-height:18px;"></div>
            </div>
        `;

        container.appendChild(section);
        _wireSectionEvents(section, courseKey, choices);
    }

    // ─── Public entry point ────────────────────────────────────────────────────

    /**
     * loadSurveyEditor(container, courseKey, canAuthor)
     *
     * Fetches the existing survey for courseKey and renders the editor into container.
     * No-ops silently if canAuthor is false.
     */
    function loadSurveyEditor(container, courseKey, canAuthor) {
        if (!canAuthor) return;
        _ensureStyles();

        fetch('/api/chalix/dashboard/survey/get/' + courseKey + '/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            const survey = (data.success && data.survey) ? data.survey : null;
            _renderSurveyEditor(container, courseKey, survey);
        })
        .catch(function (err) {
            console.error('[ChalixSurvey] load error:', err);
            container.insertAdjacentHTML('beforeend',
                '<div style="color:#6b7280;font-size:13px;margin-top:12px;">Không thể tải khảo sát nhu cầu đào tạo</div>');
        });
    }

    // ─── Export ────────────────────────────────────────────────────────────────

    window.ChalixSurvey = { loadSurveyEditor: loadSurveyEditor };

})();
