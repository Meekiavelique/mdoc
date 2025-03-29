document.addEventListener('DOMContentLoaded', function() {
    renderMathExpressions();
});

function renderMathExpressions() {
    const content = document.getElementById('doc-content');
    if (!content) {
        console.error("Element with ID 'doc-content' not found for KaTeX rendering.");
        return;
    }

    try {
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
    } catch (error) {
        console.error("Error during KaTeX auto-rendering:", error);
    }
}