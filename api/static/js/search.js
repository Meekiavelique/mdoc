document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = searchInput.value.toLowerCase();
            const items = document.querySelectorAll('#doc-list li');
            
            if (searchTerm.length === 0) {
                items.forEach(item => item.classList.remove('hidden'));
                return;
            }
            
            items.forEach(function(item) {
                const text = item.textContent.toLowerCase();
                if (fuzzySearch(text, searchTerm)) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });
        });
    }

    const contentSearchInput = document.getElementById('content-search');
    if (contentSearchInput) {
        contentSearchInput.addEventListener('keyup', function() {
            const searchTerm = contentSearchInput.value.toLowerCase();
            if (searchTerm.length < 2) {
                clearHighlights();
                return;
            }
            
            const content = document.getElementById('doc-content');
            if (!content) return;
            
            clearHighlights();
            
            if (searchTerm.length > 0) {
                const regex = new RegExp(escapeRegExp(searchTerm), 'gi');
                const matches = findAndHighlightText(content, regex);
                
                if (matches > 0) {
                    scrollToFirstHighlight();
                }
            }
        });
    }

    addUIEnhancements();
});

function fuzzySearch(text, search) {
    if (text.includes(search)) return true;
    
    let searchIdx = 0;
    let textIdx = 0;
    
    while (searchIdx < search.length && textIdx < text.length) {
        if (search[searchIdx] === text[textIdx]) {
            searchIdx++;
        }
        textIdx++;
    }
    
    return searchIdx === search.length;
}

function clearHighlights() {
    const highlights = document.querySelectorAll('.highlight');
    highlights.forEach(function(el) {
        el.outerHTML = el.innerHTML;
    });
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function findAndHighlightText(element, regex) {
    let matches = 0;
    
    if (element.nodeType === 3) {
        const match = element.nodeValue.match(regex);
        if (match) {
            matches += match.length;
            const span = document.createElement('span');
            span.className = 'highlight';
            
            const text = element.nodeValue;
            const parts = text.split(regex);
            
            if (parts.length > 1) {
                let replacementHtml = parts[0];
                
                for (let i = 1; i < parts.length; i++) {
                    replacementHtml += `<span class="highlight">${match[i-1]}</span>${parts[i]}`;
                }
                
                const newNode = document.createElement('span');
                newNode.innerHTML = replacementHtml;
                element.parentNode.replaceChild(newNode, element);
            }
        }
    } else if (element.nodeType === 1) {
        if (element.tagName === 'SCRIPT') return 0;
        
        for (let i = 0; i < element.childNodes.length; i++) {
            matches += findAndHighlightText(element.childNodes[i], regex);
        }
    }
    
    return matches;
}

function scrollToFirstHighlight() {
    const firstHighlight = document.querySelector('.highlight');
    if (firstHighlight) {
        firstHighlight.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

function addUIEnhancements() {

    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(function(codeBlock) {
        const container = codeBlock.parentNode;
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        
        container.style.position = 'relative';
        copyButton.style.position = 'absolute';
        copyButton.style.top = '5px';
        copyButton.style.right = '5px';
        
        copyButton.addEventListener('click', function() {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(function() {
                copyButton.textContent = 'Copied!';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
        
        container.appendChild(copyButton);
    });

    const contentContainer = document.getElementById('doc-content');
    if (contentContainer && !document.querySelector('.print-button')) {
        const printButton = document.createElement('a');
        printButton.textContent = 'Print View';
        printButton.className = 'print-button';
        printButton.href = window.location.pathname + '?print=1';
        
        const actionButtons = document.querySelector('.action-buttons');
        if (!actionButtons) {
            const h1 = document.querySelector('h1');
            if (h1 && h1.parentNode) {
                const buttonContainer = document.createElement('div');
                buttonContainer.className = 'action-buttons';
                buttonContainer.appendChild(printButton);
                h1.parentNode.insertBefore(buttonContainer, h1.nextSibling);
            }
        }
    }
    

    const links = document.querySelectorAll('#doc-content a[href^="http"]');
    links.forEach(function(link) {
        if (!link.hasAttribute('target')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
}