document.addEventListener('DOMContentLoaded', function() {
    loadKaTeX();
});

function loadKaTeX() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css';
    document.head.appendChild(link);
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js';
    script.onload = function() {
        const autoRenderScript = document.createElement('script');
        autoRenderScript.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js';
        autoRenderScript.onload = renderMathExpressions;
        document.head.appendChild(autoRenderScript);
    };
    document.head.appendChild(script);
}

function renderMathExpressions() {
    const content = document.getElementById('doc-content');
    if (!content) return;
    
    renderMathInElement(content, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
        ],
        throwOnError: false,
        trust: true,
        macros: {
            "\\f": "#1f(#2)"
        }
    });
}