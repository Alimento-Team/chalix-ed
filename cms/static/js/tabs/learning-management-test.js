(function () {
    'use strict';
    
    console.log('🚀 Learning Management TEST loaded');
    
    window.CMS_TABS = window.CMS_TABS || {};

    function render(container, config) {
        if (!container) return;
        console.log('[LM] Starting render for learning-management tab');
        
        container.innerHTML = `
            <div class="lm-wrap">
                <div class="lm-card">
                    <h2>Test Learning Management</h2>
                    <p>This is a minimal test version</p>
                    <div>
                        <h3>Demo Programs:</h3>
                        <div class="lm-card-item">
                            <h4>Test Program 1</h4>
                            <p>This is a test program</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Register the module
    window.CMS_TABS['learning_management'] = {
        render: render
    };

})();