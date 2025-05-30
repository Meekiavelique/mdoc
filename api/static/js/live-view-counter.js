document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/').filter(part => part.length > 0);

    if (pathParts.length === 0 || 
        pathParts[0] === 'api' || 
        pathParts[0] === 'version' ||
        pathParts[0] === 'sitemap.xml' ||
        pathParts.some(part => part.includes('.'))) {
        return;
    }
    const docName = pathParts.join('/');

    console.log('Extracted document name:', docName);

    let retryCount = 0;
    const maxRetries = 3;
    const retryDelay = 1000; 

    function updateViewCount() {
        const timestamp = Date.now();
        const url = `/api/docs/${docName}?_t=${timestamp}`;

        console.log('Fetching view count from:', url);

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
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('View count data received:', data);

            const viewElements = document.querySelectorAll('.view-count');
            if (viewElements.length > 0 && typeof data.view_count === 'number') {
                viewElements.forEach(element => {
                    element.textContent = `Views: ${data.view_count}`;
                });
                console.log('Updated view count elements:', data.view_count);
            } else {
                console.log('No view count elements found or invalid data');
            }

            retryCount = 0;
        })
        .catch(error => {
            console.warn(`View count update failed (attempt ${retryCount + 1}/${maxRetries}):`, error);
            retryCount++;

            if (retryCount < maxRetries) {
                const delay = retryDelay * Math.pow(2, retryCount - 1); 
                console.log(`Retrying in ${delay}ms...`);
                setTimeout(updateViewCount, delay);
            } else {
                console.error('Max retries reached. Giving up on view count updates.');

                const viewElements = document.querySelectorAll('.view-count');
                viewElements.forEach(element => {
                    element.textContent = 'Views: --';
                    element.style.opacity = '0.5';
                });
            }
        });
    }

    setTimeout(updateViewCount, 100);

    const updateInterval = setInterval(() => {
        if (retryCount < maxRetries) {
            updateViewCount();
        } else {
            clearInterval(updateInterval);
        }
    }, 30000);

    window.addEventListener('beforeunload', () => {
        clearInterval(updateInterval);
    });
});