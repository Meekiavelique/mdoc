document.addEventListener('DOMContentLoaded', function() {
    const mermaidElements = document.querySelectorAll('.mdoc-mermaid');
    
    if (mermaidElements.length === 0) {
        return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
    script.onload = initializeMermaidDiagrams;
    document.head.appendChild(script);
});

function initializeMermaidDiagrams() {
    mermaid.initialize({
        startOnLoad: false,
        theme: 'neutral',
        securityLevel: 'strict'
    });
    
    const placeholders = document.querySelectorAll('.mdoc-mermaid');
    
    placeholders.forEach((placeholder, index) => {
        try {
            const encodedDiagram = placeholder.getAttribute('data-diagram');
            const simpleDisplay = placeholder.getAttribute('data-simple-display') === 'true';
            
            if (!encodedDiagram) {
                console.error('No diagram definition found for Mermaid diagram');
                return;
            }
            
            const diagramDefinition = atob(encodedDiagram);
            
            if (!simpleDisplay) {
                const header = document.createElement('div');
                header.className = 'component-header';
                header.textContent = 'Interactive Diagram';
                placeholder.appendChild(header);
                
                const themeSelect = document.createElement('select');
                ['default', 'forest', 'dark', 'neutral'].forEach(theme => {
                    const option = document.createElement('option');
                    option.value = theme;
                    option.textContent = theme.charAt(0).toUpperCase() + theme.slice(1);
                    
                    if (theme === 'neutral') {
                        option.selected = true;
                    }
                    
                    themeSelect.appendChild(option);
                });
                header.appendChild(themeSelect);
                
                const body = document.createElement('div');
                body.className = 'component-body';
                placeholder.appendChild(body);
                
                const diagramContainer = document.createElement('div');
                diagramContainer.className = 'mermaid-diagram-container';
                body.appendChild(diagramContainer);
                
                renderDiagram(diagramContainer, diagramDefinition, 'neutral');
                
                const exportButtonsDiv = document.createElement('div');
                exportButtonsDiv.className = 'mermaid-export-buttons';
                
                const svgBtn = document.createElement('button');
                svgBtn.textContent = 'Export SVG';
                svgBtn.className = 'mermaid-export-btn';
                svgBtn.addEventListener('click', function() {
                    const svgElement = diagramContainer.querySelector('svg');
                    if (svgElement) {
                        exportSvg(svgElement);
                    }
                });
                
                const pngBtn = document.createElement('button');
                pngBtn.textContent = 'Export PNG';
                pngBtn.className = 'mermaid-export-btn';
                pngBtn.addEventListener('click', function() {
                    const svgElement = diagramContainer.querySelector('svg');
                    if (svgElement) {
                        exportPng(svgElement);
                    }
                });
                
                exportButtonsDiv.appendChild(svgBtn);
                exportButtonsDiv.appendChild(pngBtn);
                body.appendChild(exportButtonsDiv);
                
                themeSelect.addEventListener('change', function() {
                    const selectedTheme = themeSelect.value;
                    renderDiagram(diagramContainer, diagramDefinition, selectedTheme);
                });
            } else {
                renderDiagram(placeholder, diagramDefinition, 'neutral');
            }
            
        } catch (error) {
            console.error('Error initializing Mermaid diagram:', error);
            
            const errorMsg = document.createElement('div');
            errorMsg.className = 'mermaid-error';
            errorMsg.textContent = 'Error rendering diagram: ' + (error.message || 'Unknown error');
            placeholder.appendChild(errorMsg);
        }
    });
}

function renderDiagram(container, definition, theme) {
    container.innerHTML = '';
    
    const pre = document.createElement('pre');
    pre.className = 'mermaid';
    pre.textContent = definition;
    container.appendChild(pre);
    
    mermaid.initialize({
        startOnLoad: false,
        theme: theme,
        securityLevel: 'strict'
    });
    
    mermaid.run({ 
        nodes: [pre],
        suppressErrors: true
    });
}

function exportSvg(svgElement) {
    const svgClone = svgElement.cloneNode(true);
    
    const svgData = new XMLSerializer().serializeToString(svgClone);
    
    const svgBlob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(svgBlob);
    downloadLink.download = 'diagram.svg';
    
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportPng(svgElement) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const svgBlob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
    const url = URL.createObjectURL(svgBlob);
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob(function(blob) {
            const downloadLink = document.createElement('a');
            downloadLink.href = URL.createObjectURL(blob);
            downloadLink.download = 'diagram.png';
            
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        });
    };
    
    img.src = url;
}