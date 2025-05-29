document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const docName = pathParts[pathParts.length - 1] || 'index';
    
    if (docName === 'index' || docName.includes('.') || docName.startsWith('api') || docName.includes('version')) {
        return;
    }
    
    let retryCount = 0;
    const maxRetries = 3;
    
    function updateViewCount() {
        const timestamp = Date.now();
        const url = `/api/docs/${encodeURIComponent(docName)}?_t=${timestamp}`;
        
        fetch(url, {
            method: 'GET',
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const viewElements = document.querySelectorAll('.view-count');
            if (viewElements.length > 0 && data.view_count) {
                viewElements.forEach(element => {
                    element.textContent = `Views: ${data.view_count}`;
                });
            }
            retryCount = 0;
        })
        .catch(error => {
            console.warn(`View count update failed (attempt ${retryCount + 1}):`, error);
            retryCount++;
            if (retryCount < maxRetries) {
                setTimeout(updateViewCount, 1000 * retryCount);
            }
        });
    }
    
    setTimeout(updateViewCount, 100);
    
    setInterval(updateViewCount, 30000);
});